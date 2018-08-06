# Fax Production Main

# Submitting to midway processing node

import sys
import os
import getpass

sys.path.append(os.getcwd())

from fax_production_control import Setup, Batch, Submit

if __name__ == '__main__':
    # Change the parameters in arg to change production directory and batching condition
    # for changing config: go to fax_production_control
    # for changing data processing: go to fax_production_process
    head_directory = '/project2/lgrandi/{user}/sim/'.format(
        user=getpass.getuser())
    #{Step 1.}#
    crl = Setup()
    crl.default_config['BASICS'] = dict(name='Fax_Test',
                                        description='Simple Test on if this works',
                                        detector='XENON1T SR1_parameters',
                                        conda_env='pax_v6.8.0',
                                        number_job=20,
                                        number_event_per_job=100,
                                        production_id_format='{name}_{index:06}',
                                        pmt_afterpulse='True',
                                        s2_afterpulse='True',
                                        personalize_config='False',
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

    crl.default_config['MIDWAYNODE'] = dict(user=getpass.getuser(),
                                            partition='xenon1t',
                                            qos='xenon1t',
                                            )
    crl.execute(head_directory=head_directory)

    #{Step 2.}#
    num_group = 2  # Break all jobs into a handful of groups. You can put number_job here,
    # but let each node run ~10 jobs as number_group = number_job/10 would speed up you production
    # so that jobs in the same group will be run on one node one by one without waiting for node after one another
    max_num_submit = 50  # Maximum number of jobs running on submit node
    crl = Batch()
    crl.execute(head_directory=head_directory, num_group=num_group)

    #{Step 3.}#
    crl = Submit()
    crl.execute(head_directory=head_directory, max_num_submit=max_num_submit)
