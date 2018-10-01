#!/usr/bin/env python
#
# This script should go on Midway here:
#  /project/lgrandi/xenon1t/grid_proxy
# as called by renew-cron.sh
import os
import sys
import subprocess
import shutil

PROXY_LOCATION = '/project/lgrandi/xenon1t/grid_proxy/xenon_service_proxy'
PROXY_USER_ID  = '368041573'  #corresponse to bauermeister
PROXY_GROUP_ID = '10401'      #corresponse to pi-lgrandi
#hint: checkout user and group id's with id <username> command

os.chmod(PROXY_LOCATION, 0o640)
#shutil.chown(PROXY_LOCATION, group='pi-lgrandi')
os.chown(PROXY_LOCATION, 368041573, 10401)
