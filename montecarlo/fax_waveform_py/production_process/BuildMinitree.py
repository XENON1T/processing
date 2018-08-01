import sys
import os
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None

from fax_production_process import ProductionProcess
import hax


class BuildMiniTree(ProductionProcess):
    '''Run hax to create minitree'''

    process_oerder = 5
    __version__ = '0.0.1'

    def _check(self):
        return os.path.isfile('{minitree_pickle_path}/{production_id}.h5'.format(minitree_pickle_path=self.config['DIRECTORY']['minitree_pickle'], production_id=self.production_id))

    def hax_init(self, force_reload=False):
        self.main_data_path = self.config['DIRECTORY']['processed']
        self.minitree_path = self.config['DIRECTORY']['minitree']

        # Trick learned from Daniel Coderre's DAQVeto lichen
        if (not len(hax.config)) or force_reload:
            # User didn't init hax yet... let's do it now
            hax.init(experiment='XENON1T',
                     main_data_paths=[self.main_data_path],
                     minitree_paths=[self.minitree_path],
                     version_policy='loose'
                     )

        elif not (self.main_data_path in hax.config['main_data_paths']):
            hax.config['main_data_paths'] = ['.', self.main_data_path]

        elif not (self.minitree_path == hax.config['minitree_paths'][0]):
            hax.config['minitree_paths'] = [self.minitree_path]

    def _process(self):
        self.hax_init(force_reload=False)
        self.minitree_pickle_path = self.config['DIRECTORY']['minitree_pickle']

        with self._divert_stdout():
            self.df = hax.minitrees.load(
                self.production_id, ['Basics', 'Fundamentals'])
            self.df.to_hdf(os.path.join(
                self.minitree_pickle_path, '{name}.h5'.format(name=self.production_id)), 'table')
            print('{production_id} minitrees building success :)'.format(
                production_id=self.production_id))
