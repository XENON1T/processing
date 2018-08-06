#######################################
# Fax Production Control Classes
# by Tianyu tz2263@columbia.edu, Aug 2017
#######################################

import os
import getpass
import numpy as np

from configparser import ConfigParser
from cax.qsub import submit_job
import time


class Controller():
    '''Cross productions works'''

    __version__ = '0.0.0'

    def name(self):
        return self.__class__.__name__

    def execute(self, *args, **kwargs):
        eval('self.{name}(*args, **kwargs)'.format(name=self.name().lower()))


class Setup(Controller):
    '''
    Create {config}.ini in current folder
    * Create example_config.ini in current folder if not already exist
    Store production specifications in {config}.ini
    Down fall of this is that ConfigParser couldn't be deep copyed
    Only config names (str) are stored in config_list.txt in current directory
    '''
    __version__ = '0.0.2'

    def setup(self, head_directory=''):
        if head_directory == '':
            print('head_directory must be specified')
            return 0

        self.head_directory = head_directory

        # Save a copy of default_config.ini
        if not os.path.isfile(os.path.join(os.getcwd(), 'configs', '%s.ini' % 'default_config_copy')):
            with open(os.path.join(os.getcwd(), 'configs', '%s.ini' % 'default_config_copy'), 'w') as config_file:
                self.default_config.write(config_file)
                config_file.close()

        # Use default config for one time
        self._generate_config_by_default()

        # Customize and create multiple configs
        # self._generate_config()

        print('following process will be generated under %s:' %
              self.head_directory)
        print(self.config_list)
        with open(os.path.join(os.getcwd(), '%s.txt' % 'config_list'), 'w+') as config_list_file:
            _ = [config_list_file.write('%s\n' % c) for c in self.config_list]
            config_list_file.close()

        self._setup_directory()

    def __init__(self):
        self.config_list = []

        self.default_config = ConfigParser()
        self.default_config['BASICS'] = dict(name='Fax_Test',
                                             description='Simple Test on if this works',
                                             detector='XENON1T',
                                             conda_env='pax_head',
                                             number_job=100,
                                             number_event_per_job=100,
                                             production_id_format='{name}_{index:06}',
                                             pmt_afterpulse='True',
                                             s2_afterpulse='True',
                                             personalize_config='True',
                                             photon_number_low=50,
                                             photon_number_high=100,
                                             electron_number_low=10,
                                             electron_number_high=100,
                                             # 'False' to generate lone S1(2)
                                             correlated='True',
                                             recoil_type='ER',
                                             use_array_truth='False',
                                             save_afterpulse_truth='False',
                                             config_string='',  # add more paxer --config_string
                                             )

        self.default_config['MIDWAYNODE'] = dict(user=getpass.getuser(),
                                                 partition='xenon1t',
                                                 qos='xenon1t',
                                                 )

    def _generate_config_by_default(self):
        """
        just write default confit out
        """

        config = self.default_config

        with open(os.path.join(os.getcwd(), '%s.ini' % config['BASICS']['name']), 'w') as config_file:
            config.write(config_file)
        config_file.close()
        self.config_list.append(config['BASICS']['name'])

    def _generate_config(self):
        """
        Modify this to change configration
        Create a {config}.ini file in current folder for each configration
        Don't duplicate config name !
        """

        config = self.default_config

        for ix, num_photon in enumerate([100, 200, 300, 400, 500]):
            config_name = 'test_with_%d_photons' % num_photon
            config['BASICS']['name'] = config_name
            config['BASICS']['photon_number_low'] = '%d' % (num_photon - 50)
            config['BASICS']['photon_number_high'] = '%d' % (num_photon + 50)

            with open(os.path.join(os.getcwd(), '%s.ini' % config_name), 'w') as config_file:
                config.write(config_file)
            config_file.close()
            self.config_list.append(config_name)

    def _setup_directory(self):
        if len(self.config_list) == 0:
            print(
                'Zero configuration found, use Config.generate_config to generate configurations')
            return 0
        else:
            for config_name in self.config_list:
                self._setup_single_directory(config_name)

    def _setup_single_directory(self, config_name):
        # Read in configuration from current folder
        self.config_name = config_name
        self.config = ConfigParser()
        self.config.read(os.path.join(
            os.getcwd(), '%s.ini' % self.config_name))

        # Establish the dirctories for production
        self.directory = {}
        self.directory['head'] = os.path.join(
            self.head_directory, self.config_name)
        self.directory['log'] = os.path.join(self.head_directory, 'log')
        #self.directory['err'] = os.path.join(self.head_directory, 'err')
        self.directory['tmp'] = os.path.join(self.head_directory, 'tmp')
        self.directory['cwd'] = os.getcwd()

        for sub_directory in ['csv',  # Lovely Shire
                              'truth_raw', 'truth_sorted',  # Frodo and Sam
                              'raw', 'processed', 'minitree', 'minitree_pickle', 'productionlog',  # Pippin and Merry
                              'merged',
                              ]:
            self.directory[sub_directory] = os.path.join(
                self.directory['head'], sub_directory)

        self._make_directory()

    def _make_directory(self):
        # Create directory if not already exist
        for key in self.directory.keys():
            if not os.path.exists(self.directory[key]):
                os.makedirs(self.directory[key])

        # Merge directory info into process
        self.config['DIRECTORY'] = self.directory

        config_file = open(os.path.join(
            os.getcwd(), self.config['DIRECTORY']['head'], '%s.ini' % self.config_name), 'w')
        self.config.write(config_file)
        config_file.close()

        # Remove the temporary .ini file
        os.remove(os.path.join(os.getcwd(), '%s.ini' % self.config_name))


class Batch(Controller):
    '''
    Take 1) head_directory 2) number of batches
    Hidden input of list of config names within config_list.txt under current directory
    Adds up all productions with differet configurations according to {head}/{config}/{config}.ini
    Split productions into batches.
    '''

    __version__ = '0.0.1'

    def batch(self, head_directory='', num_group=10):
        if head_directory == '':
            print('head_directory must be specified')
            return 0

        self.head_directory = head_directory
        self.num_group = num_group
        config_list_file = open(os.path.join(os.getcwd(), 'config_list.txt'))
        self.config_list = config_list_file.read().splitlines()

        # Give name(id) to individual production
        self.production_list = []

        if len(self.config_list) != 0:
            for config_name in self.config_list:
                self.config = ConfigParser()
                config_path = os.path.join(
                    self.head_directory, config_name, '%s.ini' % config_name)
                self.config.read(config_path)

                for i in range(int(self.config['BASICS']['number_job'])):
                    self.production_list.append(
                        self.config['BASICS']['production_id_format'].format(name=config_name, index=i))

        self.group_production_list = np.array_split(
            self.production_list, self.num_group)
        self.group_list = []

        for index, group in enumerate(self.group_production_list):
            group_name = 'submit{:02}'.format(index)
            self.group_list.append(group_name)

            production_list_file = os.path.join(
                self.config['DIRECTORY']['log'], '{gn}_id_list.txt'.format(gn=group_name))
            np.savetxt(production_list_file, np.asarray(
                group, dtype='U32'),  fmt='%s')

        with open(os.path.join(os.getcwd(), '%s.txt' % 'group_list'), 'w+') as group_list_file:
            _ = [group_list_file.write('%s\n' % g) for g in self.group_list]
            group_list_file.close()


class Submit(Controller):
    '''
        Take 1) head directory 2) maximum number of nodes to use at once
        Submit each group to a node and excute
        python fax_production_process.py {head_directory} {group_list}

    '''

    def submit(self, head_directory='', max_num_submit=10):
        self.max_num_submit = max_num_submit
        self.head_directory = head_directory

        if head_directory == '':
            print('head_directory must be specified')
            return 0

        group_list_file = open(os.path.join(os.getcwd(), 'group_list.txt'))
        self.group_list = group_list_file.read().splitlines()
        self.read_config()

        index = 0
        while (index < len(self.group_list)):
            if (self.working_job() < self.max_num_submit):
                self._submit_single(group_name=self.group_list[index])
                time.sleep(0.1)
                index += 1

    # check my jobs
    def working_job(self):
        cmd = 'squeue --user={user} | wc -l'.format(
            user=self.config['MIDWAYNODE']['user'])
        jobNum = int(os.popen(cmd).read())
        return jobNum - 1

    def _submit_single(self, group_name):
        cmd = """#!/bin/bash
#SBATCH --job-name={group_name}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=3000
#SBATCH --output={log}/{group_name}.log
#SBATCH --error={log}/{group_name}.log
#SBATCH --account=pi-lgrandi
#SBATCH --partition={partition}
#SBATCH --qos={qos}
export PATH=/project/lgrandi/anaconda3/bin:$PATH
export PROCESSING_DIR={tmp}

cd {cwd}

source activate {conda_env}

python fax_production_process.py {head_directory} {log}/{group_name}_id_list.txt

rm -rf ${{PROCESSING_DIR}}
"""
        y = cmd.format(group_name=group_name,
                       log=self.config['DIRECTORY']['log'],
                       # err=self.config['DIRECTORY']['err'],
                       tmp=self.config['DIRECTORY']['tmp'],
                       cwd=self.config['DIRECTORY']['cwd'],
                       partition=self.config['MIDWAYNODE']['partition'],
                       qos=self.config['MIDWAYNODE']['qos'],
                       head_directory=self.head_directory,
                       conda_env=self.config['BASICS']['conda_env'],
                       )
        submit_job(y)

    def read_config(self):
        # Read the parameters used for production
        config_list_file = open(os.path.join(os.getcwd(), 'config_list.txt'))
        self.config_list = config_list_file.read().splitlines()
        config_name = self.config_list[0]
        self.config = ConfigParser()
        self.config.read(os.path.join(self.head_directory,
                                      config_name, '%s.ini' % config_name))
