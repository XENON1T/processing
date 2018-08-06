#######################################
# Fax Production Processes
# by Tianyu tz2263@columbia.edu, Aug 2017
# Changed from Qing and Joey's code
#
# All processes required for fax production
# CreateFake
# CreateFakeFromPickle
# Simulation
# ProcessRaw
# SortTruth
# BuildMiniTree
# MergeTruth
# BuildMiniTreeArray (not implemented)
# MergeTruthArray (not implemented)
#######################################
# Hard Code Warnings
#
# RunAllProcess.process_list
# PaxerProcess timeout
# BuildMiniTree hax.minitrees.load(..,[Correction])
#######################################
# Run as __main__ with
# python fax_production_process {head_directory} {production_list_file}
# python fax_production_process {head_directory} {production_id}
#
# will initiate and run RunAllProcess() and RunAllProcess.process()
########################################

import sys
import os
from configparser import ConfigParser
from contextlib import contextmanager
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None


class ProductionProcess():
    '''Generic production process class'''

    process_order = 0
    __version__ = '0.0.0'

    def process(self, head_directory, production_id):
        self.read_config(head_directory, production_id)
        flag = self._check()
        if not flag:
            self._process()

    def _check(self):
        '''Check if the file has already be computed'''
        raise NotImplementedError()

    def _process(self):
        '''The core production process'''
        raise NotImplementedError()

    def read_config(self, head_directory, production_id):
        '''Read the parameters used for production'''
        if head_directory == '' or production_id == '':
            print('Must specify head_directory and production_id')
            return 0

        self.production_id = production_id
        self.config_name = production_id[:-7]
        self.head_directory = head_directory

        self.config_path = os.path.join(
            self.head_directory, self.config_name, '%s.ini' % self.config_name)
        self.config = ConfigParser()
        self.config.read(self.config_path)

    @contextmanager
    def _divert_stdout(self):
        # Dangerous to use but works very nice if all bugs are fixed.
        # Basically works as 1&>${log}
        self.productionlog_path = self.config['DIRECTORY']['productionlog']
        self.productionlog = open(
            '{path}/{name}.log'.format(path=self.productionlog_path, name=self.production_id), 'a+')

        global saved_stdout, saved_stderr
        saved_stdout, saved_stderr = sys.stdout, sys.stderr
        sys.stdout = self.productionlog
        sys.stderr = self.productionlog
        print(saved_stdout)
        print(saved_stderr)
        yield
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr
        self.productionlog.close()


class RunAllProcess(ProductionProcess):
    '''Go through all processes'''

    __version__ = '0.0.1'

    def __init__(self):
        from production_process.CreateFake import CreateFake, CreateFakeFromPickle
        from production_process.PaxerProcess import Simulation, ProcessRaw
        from production_process.BuildMinitree import BuildMiniTree
        from production_process.SortAndMerge import SortTruth, MergeTruth

        self.process_list = [CreateFake(),
                             Simulation(),
                             ProcessRaw(),
                             SortTruth(),
                             BuildMiniTree(),
                             MergeTruth(),
                             ]

    def process(self, head_directory, production_id):
        for process in self.process_list:
            process.process(head_directory, production_id)


# When called upon, run RunAllProcess.process
if __name__ == '__main__':
    arg = sys.argv
    if not (len(arg) == 3):
        sys.exit(1)

    head_directory = arg[1]
    production_list_file = arg[2]

    # Process a list of productions
    if 'txt' in production_list_file:
        errors = []
        production_list = np.array(np.genfromtxt(
            production_list_file, dtype='<U32'), ndmin=1)
        for prod in production_list:
            try:
                production_process = RunAllProcess()
                production_process.process(
                    head_directory=head_directory, production_id=prod)
            except Exception as e:
                err = dict(production_id=prod,
                           error_type=e.__class__.__name__,
                           error_message=str(e),
                           )
                print(str(e))
                errors.append(err)

        print('Enconter %d exceptions' % len(errors))
        if len(errors) != 0:
            errors = pd.DataFrame(errors)
            errors.to_pickle(production_list_file[:-11]+'err_msg.pkl')

    # Process a single prodution
    else:
        prod = production_list_file
        production_process = RunAllProcess()
        production_process.process(
            head_directory=head_directory, production_id=prod)
