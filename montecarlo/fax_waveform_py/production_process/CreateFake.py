import sys
import os
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None

from fax_production_process import ProductionProcess


class CreateFake(ProductionProcess):
    '''Create fake data and write to {production_id}.csv at {csv} directory'''

    process_order = 1
    __version__ = '0.0.1'

    def __init__(self):
        ####################################
        # Some nuisance parameters (HARDCODE WARNING):
        ####################################
        self.DriftVelocity = 1.440e-1  # cm/us
        self.default_event_time = 1000.  # Where we put S1

    def _check(self):
        return os.path.isfile('{csv_path}/{production_id}.csv'.format(csv_path=self.config['DIRECTORY']['csv'], production_id=self.production_id))

    def _process(self):
        # Where the csv will be save to
        self.csv_path = self.config['DIRECTORY']['csv']
        self.detector = self.config['BASICS']['detector']
        self.number_event_per_job = int(
            self.config['BASICS']['number_event_per_job'])
        self.photon_number_low = int(
            self.config['BASICS']['photon_number_low'])
        self.photon_number_high = int(
            self.config['BASICS']['photon_number_high'])
        self.electron_number_low = int(
            self.config['BASICS']['electron_number_low'])
        self.electron_number_high = int(
            self.config['BASICS']['electron_number_high'])
        self.recoil_type = self.config['BASICS']['recoil_type']

        S1, S2 = 'S1', 'S2'  # Allow eval to work
        self.correlated = eval(self.config['BASICS']['correlated'])

        # Actual creation
        self._randomize_FV()
        self._randomize_photon_number()
        self._randomize_electron_number()

        self.csv = pd.DataFrame(columns=['instruction', 'recoil_type', 'x', 'y', 'z',
                                         's1_photons', 's2_electrons', 't'])

        if self.correlated == False:
            self.csv['instruction'] = np.asarray(
                [(n+((-1)**n-1)/2)/2 for n in range(2*self.number_event_per_job)], dtype=int)
            self.csv['recoil_type'] = self.recoil_type
            self.csv['temp'] = [n %
                                2+1 for n in range(2*self.number_event_per_job)]

            self.csv.loc[self.csv.temp == 1, 't'] = self.default_event_time
            self.csv.loc[self.csv.temp == 1, 's1_photons'] = self.photon_number
            self.csv.loc[self.csv.temp == 1, 's2_electrons'] = 0

            self.csv.loc[self.csv.temp == 2,
                         't'] = self.default_event_time+self.z/self.DriftVelocity
            self.csv.loc[self.csv.temp == 2, 's1_photons'] = 0
            self.csv.loc[self.csv.temp == 2,
                         's2_electrons'] = self.electron_number

            for field in ['x', 'y', 'z']:
                for t in [1, 2]:
                    self.csv.loc[self.csv.temp == t,
                                 field] = getattr(self, field)

            self.csv.drop('temp', inplace=True)

        else:
            self.csv['instruction'] = list(range(self.number_event_per_job))
            self.csv['recoil_type'] = self.recoil_type

            for field in ['x', 'y', 'z']:
                self.csv[field] = getattr(self, field)

            if self.correlated == True:
                self.csv['t'] = self.default_event_time
                self.csv['s1_photons'] = self.photon_number
                self.csv['s2_electrons'] = self.electron_number

            elif self.correlated == 'S1':
                self.csv['t'] = self.default_event_time
                self.csv['s1_photons'] = self.photon_number
                self.csv['s2_electrons'] = 0

            elif self.correlated == 'S2':
                self.csv['t'] = self.default_event_time + \
                    self.z/self.DriftVelocity
                self.csv['s1_photons'] = 0
                self.csv['s2_electrons'] = self.electron_number

        # Write to csv file
        self.csv.rename(columns={'z': 'depth'}, inplace=True)
        self.csv.to_csv('{csv_path}/{production_id}.csv'.format(csv_path=self.csv_path, production_id=self.production_id),
                        sep=',', index=False)

    def _randomize_FV(self):
        self.cm2mm = 1

        ####################################
        # FV definitions (HARDCODE WARNING):
        ####################################

        # randomize the X, Y, Z according to X48kg FV
        if 'XENON100' in self.detector:
            Zlower, Zupper = -14.6-15.0, -14.6+15.0
            Rlower, Rupper = -np.sqrt(200.), np.sqrt(200.)

        elif 'XENON1T' in self.detector:  # NEED TO UPDATE THIS
            # Zlower, Zupper, Rupper = -92.9, -9, 36.94
            Zlower, Zupper, Rupper = -100, -5, 40

        r2 = np.random.uniform(0, Rupper*Rupper, self.number_event_per_job)
        angle = np.random.uniform(-np.pi, np.pi, self.number_event_per_job)

        self.r = np.sqrt(r2)
        self.x = self.r * np.cos(angle) * self.cm2mm
        self.y = self.r * np.sin(angle) * self.cm2mm
        self.z = - 1 * \
            np.random.uniform(
                Zlower, Zupper, self.number_event_per_job) * self.cm2mm
        return (self.x, self.y, self.z)

    def _randomize_photon_number(self):
        self.photon_number = np.random.randint(
            self.photon_number_low, self.photon_number_high, self.number_event_per_job)
        return self.photon_number

    def _randomize_electron_number(self):
        self.electron_number = np.random.randint(
            self.electron_number_low, self.electron_number_high, self.number_event_per_job)
        return self.electron_number


class CreateFakeFromPickle(ProductionProcess):
    ''' Read a pickled real data from {cwd}/{config_name}.pkl
        Create fake data and write to {production_id}.csv at {csv} directory'''

    process_order = 1
    __version__ = '0.0.1'

    def __init__(self):
        self.default_event_time = 1000.  # Where we put S1

    def _check(self):
        return os.path.isfile('{csv_path}/{production_id}.csv'.format(csv_path=self.config['DIRECTORY']['csv'], production_id=self.production_id))

    def _process(self):
        # Where the csv will be save to
        self.csv_path = self.config['DIRECTORY']['csv']
        self.detector = self.config['BASICS']['detector']
        self.number_event_per_job = int(
            self.config['BASICS']['number_event_per_job'])
        self.recoil_type = self.config['BASICS']['recoil_type']

        self.csv = pd.DataFrame(columns=['instruction', 'recoil_type', 'x', 'y', 'depth',
                                         's1_photons', 's2_electrons', 't'])

        self.original = pd.read_pickle(os.path.join(
            self.config['DIRECTORY']['cwd'], '%s.pkl' % self.config_name))
        self.original = self.original.reset_index(drop=True)
        self.order = int(self.production_id[-6:])

        self.original = self.original.ix[self.order*self.number_event_per_job: (
            self.order+1)*self.number_event_per_job-1, :]
        self.original = self.original.loc[:, [
            'event_number', 'x', 'y', 'z', 'cs1', 'cs2']]

        self.original.rename(
            columns={'event_number': 'instruction'}, inplace=True)

        for field in ['instruction', 'x', 'y']:
            self.csv[field] = self.original[field]

        self.csv['depth'] = - self.original['z']
        self.csv['s1_photons'] = np.array(
            np.around(self.original['cs1'].values / 0.12), dtype=np.int)
        self.csv['s2_electrons'] = np.array(
            np.around(self.original['cs2'].values / 23), dtype=np.int)
        self.csv['recoil_type'] = 'NR'
        self.csv['t'] = self.default_event_time

        self.csv.to_csv('{csv_path}/{production_id}.csv'.format(csv_path=self.csv_path, production_id=self.production_id),
                        sep=',', index=False)
