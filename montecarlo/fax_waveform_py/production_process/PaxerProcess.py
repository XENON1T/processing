import sys
import os
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired

from fax_production_process import ProductionProcess


class PaxerProcess(ProductionProcess):
    '''Use commend line submition to run paxer'''

    def _generate_commend(self):
        raise NotImplementedError()

    def _process(self):
        self._generate_commend()
        with Popen(self.cmd, shell=True, stderr=STDOUT, stdout=PIPE) as self.proc:
            # Here redirct 2&>1
            with self._divert_stdout():
                try:
                    self.stdout, self.stderr = self.proc.communicate(
                        timeout=1800)
                    self.stdout = self.stdout.decode('utf-8')
                    self.productionlog.write(self.stdout)
                except TimeoutExpired:
                    print('Subprocess timed out at 1800s')
                    self.proc.kill()
                    self.stdout, self.stderr = self.proc.communicate()
                    self.stdout = self.stdout.decode('utf-8')
                    self.productionlog.write(self.stdout)


class Simulation(PaxerProcess):
    '''Use paxer simulation to generate both fax_truth and pax_raw data'''

    process_order = 2
    __version__ = '0.0.1'

    def _check(self):
        return os.path.isfile('{truth_raw_path}/{production_id}.csv'.format(truth_raw_path=self.config['DIRECTORY']['truth_raw'], production_id=self.production_id))

    def _generate_commend(self):
        self.no_pmt_afterpulse = not eval(
            self.config['BASICS']['pmt_afterpulse'])
        self.no_s2_afterpulse = not eval(
            self.config['BASICS']['s2_afterpulse'])
        self.personalize = eval(self.config['BASICS']['personalize_config'])

        self.map = dict(production_id=self.production_id,
                        csv_path=self.config['DIRECTORY']['csv'],
                        truth_raw_path=self.config['DIRECTORY']['truth_raw'],
                        raw_path=self.config['DIRECTORY']['raw'],
                        detector=self.config['BASICS']['detector'],
                        NoPmtAP_config=os.path.join(
                            self.config['DIRECTORY']['cwd'], 'configs', 'NoPMTAfterpulses.ini'),
                        NoS2AP_config=os.path.join(
                            self.config['DIRECTORY']['cwd'], 'configs', 'NoS2Afterpulses.ini'),
                        Personalize_config=os.path.join(
                            self.config['DIRECTORY']['cwd'], 'configs', 'Personalize.ini'),
                        )

        cmds = ['paxer',
                '--input {csv_path}/{production_id}.csv',
                '--config {detector} reduce_raw_data Simulation',
                '--config_string "[WaveformSimulator]truth_file_name=\'{truth_raw_path}/{production_id}\'"',
                '--output {raw_path}/{production_id}']

        # Make out put directory
        if not os.path.exists('{raw_path}/{production_id}'.format(**self.map)):
            os.makedirs('{raw_path}/{production_id}'.format(**self.map))

        additional_cmd = ''
        keys = ['NoPmtAP_config', 'NoS2AP_config', 'Personalize_config']
        for iy, ac in enumerate([self.no_pmt_afterpulse, self.no_s2_afterpulse, self.personalize]):
            if ac:
                if additional_cmd == '':
                    additional_cmd += '--config_path'

                additional_cmd += ' {%s}' % keys[iy]
        cmds.append(additional_cmd)

        self.cmd = ' '.join(cmds)
        self.cmd = self.cmd.format(**self.map)


class ProcessRaw(PaxerProcess):
    '''User paxer to process raw data into processed data'''

    process_order = 3
    __version__ = '0.0.1'

    def _check(self):
        return os.path.isfile('{process_path}/{production_id}.root'.format(process_path=self.config['DIRECTORY']['processed'], production_id=self.production_id))

    def _generate_commend(self):
        self.map = dict(production_id=self.production_id,
                        raw_path=self.config['DIRECTORY']['raw'],
                        processed_path=self.config['DIRECTORY']['processed'],
                        detector=self.config['BASICS']['detector'],
                        )

        cmds = ['paxer',
                '--ignore_rundb',
                '--input {raw_path}/{production_id}',
                '--config {detector}',
                '--output {processed_path}/{production_id}']

        self.cmd = ' '.join(cmds)
        self.cmd = self.cmd.format(**self.map)
