#!/usr/bin/env python3.5
import pexpect
import os
import sys
import subprocess
import shutil

CERT_LOCATION = '/xenon/grid_certificates/rucio_service_cert.pem'
KEY_LOCATION = '/xenon/grid_certificates/rucio_service_key.pem'
PROXY_LOCATION = '/xenon/grid_proxy/xenon_service_proxy'
CERT_PASS = 'o665I995JPLk'
DESTINATION_HOST = 'midway.rcc.uchicago.edu'
DESTINATION = DESTINATION_HOST+':/project/lgrandi/xenon1t/grid_proxy'

print('voms-proxy-init  -hours 168 -voms xenon.biggrid.nl ' +
                      '-cert {0} -key {1} '.format(CERT_LOCATION, KEY_LOCATION) +
                      '-out {0}'.format(PROXY_LOCATION))
child = pexpect.spawn('voms-proxy-init -hours 168 -voms xenon.biggrid.nl ' +
                      '-cert {0} -key {1} '.format(CERT_LOCATION, KEY_LOCATION) +
                      '-out {0}'.format(PROXY_LOCATION))
#child.expect('Enter GRID.*:', timeout=10)
#child.sendline(CERT_PASS)
child.expect('Your proxy is valid.*')

os.chmod(PROXY_LOCATION, 0o640)
#shutil.chown(PROXY_LOCATION, group='pi-lgrandi')

subprocess.call('scp {0} {1}'.format(PROXY_LOCATION, DESTINATION), shell=True)
