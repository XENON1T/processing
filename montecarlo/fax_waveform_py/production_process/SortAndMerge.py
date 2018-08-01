import sys
import os
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None

from fax_production_process import ProductionProcess


class SortTruth(ProductionProcess):
    '''Sort peak infomation in fax_truth from peak to event level'''

    process_oerder = 4
    __version__ = '0.0.1'

    def _check(self):
        return os.path.isfile('{truth_sorted_path}/{production_id}.csv'.format(truth_sorted_path=self.config['DIRECTORY']['truth_sorted'], production_id=self.production_id))

    def _process(self):
        # Read in the csv file
        self.truth_raw_path = self.config['DIRECTORY']['truth_raw']
        self.truth_sorted_path = self.config['DIRECTORY']['truth_sorted']

        self.truth_file = open(os.path.join(
            self.truth_raw_path, '{name}.csv'.format(name=self.production_id)))
        self.truth_peak = pd.read_csv(self.truth_file)
        self.truth_peak.drop(['fax_truth_peak_id', 'g4_id', 'instruction', 'repetition', 'n_electrons',
                              't_first_electron', 't_last_electron', 't_sigma_electrons', 't_mean_electrons', 't_interaction',
                              't_first_photon', 't_last_photon', 'z',
                              ], axis=1, inplace=True)

        # Separate out s1, s2, and other peaks
        tmp = []
        for i, peak_type in enumerate(['s1', 's2', 'other_s2']):
            if peak_type == 'other_s2':
                _df = self.truth_peak[~self.truth_peak.peak_type.isin([
                                                                      's1', 's2'])]
                tmp.append(_df.loc[_df.groupby('event').n_photons.idxmax()])
            else:
                tmp.append(
                    self.truth_peak[self.truth_peak.peak_type == peak_type])

            replace_dict = {
                'n_photons': '%s' % peak_type,
                't_mean_photons': '%s_hit_time_mean' % peak_type,
                't_sigma_photons': '%s_width' % peak_type,
                'top_fraction': '%s_area_fraction_top' % peak_type,
                'x': '%s_x' % peak_type,
                'y': '%s_y' % peak_type,
            }

            tmp[i].rename(columns=replace_dict, inplace=True)
            tmp[i].drop('peak_type', axis=1, inplace=True)

        # Create a new dataframe on event level,
        # Merge s1, s2 and other peaks accroding to 'event' columns
        self.truth_event = pd.DataFrame()
        self.truth_event['event_number'] = self.truth_peak.event.unique()

        for t in tmp:
            self.truth_event = self.truth_event.merge(t, left_on='event_number',
                                                      right_on='event', how='left').drop('event', axis=1)

        # Doing some refining jobs
        self.truth_event.drop(
            ['s1_x', 's1_y', 'other_s2_x', 'other_s2_y'], axis=1, inplace=True)
        self.truth_event.rename(
            columns={'s2_x': 'x', 's2_y': 'y'}, inplace=True)

        # Save the sorted dataframe to pickle
        self.truth_event.to_hdf(os.path.join(
            self.truth_sorted_path, '{name}.h5'.format(name=self.production_id)), 'table')
        self.truth_event.to_csv(os.path.join(
            self.truth_sorted_path, '{name}.csv'.format(name=self.production_id)), index=False)


class MergeTruth(ProductionProcess):
    '''Merge sorted fax truth with minitree pickle give every column in fax truth prefix: truth_{column_name}'''

    process_oerder = 6
    __version__ = '0.0.1'

    def _check(self):
        return os.path.isfile('{merged_path}/{production_id}.pkl'.format(merged_path=self.config['DIRECTORY']['merged'], production_id=self.production_id))

    def _process(self):
        self.truth_sorted_path = self.config['DIRECTORY']['truth_sorted']
        self.minitree_pickle_path = self.config['DIRECTORY']['minitree_pickle']
        self.merged_path = self.config['DIRECTORY']['merged']

        self.truth = pd.read_hdf(
            '{path}/{name}.h5'.format(path=self.truth_sorted_path, name=self.production_id), 'table')
        self.data = pd.read_hdf(
            '{path}/{name}.h5'.format(path=self.minitree_pickle_path, name=self.production_id), 'table')

        # Change column name for truth
        name_replace_dict = {col: 'truth_' + col for col in self.truth.columns}
        self.truth.rename(columns=name_replace_dict, inplace=True)

        self.merged = self.data.merge(
            self.truth, left_on='event_number', right_on='truth_event_number', how='outer')
        self.merged.drop('truth_event_number', axis=1, inplace=True)
        self.merged.to_hdf(
            '{path}/{name}.h5'.format(path=self.merged_path, name=self.production_id), 'table')
