import datetime
import logging
import os
import time
import hashlib
import json
import random
import requests
import signal
import socket
import subprocess
import sys
import traceback
import datetime
from datetime import timedelta
import tarfile
import copy
import shutil
import tempfile
import io
import locale
import json
import pymongo
import argparse

#-------------------------------------------
#This part (class RucioAPI) is copied from a RucioAPI class which is under development by Boris Bauermeister
#right now (07/07/18). Most likely this development will not be finished and the code goes to 
#future XENONnT developments for Rucio in XENONnT. For any question ever: Boris.Bauermeister@gmail.com
class RucioAPI():
    
    def __init__(self):
        self.vlevel = 1
        
    def SetAccount(self, account):
        self.account=account

    def SetHost(self, host):
        self.host = host

    def LoadProxy(self, path_to_proxy=None):
        if path_to_proxy == None:
            print("Add the path to your proxy ticket")
            return 0
        else:
            self.path_proxy = path_to_proxy        
        
    def GetConfig(self):
        varStash = """
#Source Python2.7 and rucio
module load python/2.7
source /cvmfs/xenon.opensciencegrid.org/software/rucio-py27/setup_rucio_1_8_3.sh

#Configure the rucio environment
export RUCIO_HOME=/cvmfs/xenon.opensciencegrid.org/software/rucio-py27/1.8.3/rucio
export RUCIO_ACCOUNT={rucio_account}

#Set location of the proxy:
export X509_USER_PROXY={x509_user_proxy}
"""
        varXe1t = """
export PATH=/home/xe1ttransfer/.local/bin:$PATH
export RUCIO_HOME=~/.local/rucio
export RUCIO_ACCOUNT={rucio_account}

#Set location of the proxy:
export X509_USER_PROXY={x509_user_proxy}   
"""

        varMidway = """
source /cvmfs/xenon.opensciencegrid.org/software/rucio-py26/setup_rucio_1_8_3.sh
export RUCIO_HOME=/cvmfs/xenon.opensciencegrid.org/software/rucio-py26/1.8.3/rucio/
export RUCIO_ACCOUNT={rucio_account}
export X509_USER_PROXY={x509_user_proxy}

"""             
        
        varMidway2 = """
source /cvmfs/xenon.opensciencegrid.org/software/rucio-py27/setup_rucio_1_8_3.sh
export RUCIO_HOME=/cvmfs/xenon.opensciencegrid.org/software/rucio-py27/1.8.3/rucio/
source /cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/3.3/current/el7-x86_64/setup.sh
export RUCIO_ACCOUNT={rucio_account}
export X509_USER_PROXY={x509_user_proxy}
      
"""
        varDummy = """
echo "Rucio configuration is missing"
export RUCIO_ACCOUNT={rucio_account}
export X509_USER_PROXY={x509_user_proxy}
      
"""
        if self.host=="xe1t-datamanager":
            return varXe1t
        elif self.host=="login":
            return varStash
        elif self.host=="midway":
            return varMidway
        elif self.host=="midway2":
            return varMidway2
        else:
            return varDummy
    
    def ConfigHost(self):
        self.config = self.GetConfig().format(rucio_account=self.account, x509_user_proxy=self.path_proxy)
    
    def create_script(self, script):
        """Create script as temp file to be run on cluster"""
        fileobj = tempfile.NamedTemporaryFile(delete=False,
                                            suffix='.sh',
                                            mode='wt',
                                            buffering=1)
        fileobj.write(script)
        os.chmod(fileobj.name, 0o774)
        return fileobj
    
    def delete_script(self, fileobj):
        """Delete script after submitting to cluster
        :param script_path: path to the script to be removed
        """
        fileobj.close()
    
    def doRucio(self, upload_string ):
        sc = self.create_script( upload_string )    
        execute = subprocess.Popen( ['sh', sc.name] , 
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    shell=False,
                                    universal_newlines=False)
        stdout_value, stderr_value = execute.communicate()
        stdout_value = stdout_value.decode("utf-8")
        stdout_value = stdout_value.split("\n")
        stdout_value = list(filter(None, stdout_value)) # fastest way to remove '' from list
        self.delete_script(sc)
        return stdout_value, stderr_value
    
    def Whoami(self):
        cmd_adj = "rucio whoami"
        cmd = self.config
        cmd += cmd_adj
        msg, err = self.doRucio(cmd)
        
        for i in msg:
            print(i)
    
    def Download(self, scope=None, dname=None, destination=None):
        cmd_adj = "rucio download --dir {destination} --no-subdir {scope}:{dname}".format(destination=destination,
                                                                                         scope=scope,
                                                                                         dname=dname)
        cmd = self.config
        cmd += cmd_adj
        msg, err = self.doRucio(cmd)
        
        for i in msg:
            print(i)

#Additional functions:
def get_size(start_path = '.'):
    #https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def getLEDCalibration(rc_days = 1):
    #This function interacts with the XENON1T runDB:
    uri = 'mongodb://eb:%s@xenon1t-daq.lngs.infn.it:27017,copslx50.fysik.su.se:27017,zenigata.uchicago.edu:27017/run'
    uri = uri % os.environ.get('MONGO_PASSWORD')
    c = pymongo.MongoClient(uri,
                            replicaSet='runs',
                            readPreference='secondaryPreferred')
    

    
    db = c['run']
    collection = db['runs_new']
    
    #Create a query of the recent days (rc_days)
    # -for LED data
    
    dt_today = datetime.datetime.today()
    dt_recent = timedelta(days=rc_days)
    dt_begin = dt_today-dt_recent
    tags = ['gain_step%d' % i for i in range(5)]
    
    query =  {"source.type": "LED", 
              "start": {'$gt': dt_begin},
              }

    cursor = collection.find(query)
    cursor = list(cursor)
    
    #get rucio:
    safer = {}
    
    for i_c in cursor:
        run_number = i_c['number']
        run_name = i_c['name']
        run_date = i_c['start']
        run_source = None
        
        run_dbtags = []
        if 'tags' in i_c and len(i_c['tags']) > 0:            
            for itag in i_c['tags']:
                run_dbtags.append(itag['name'])
        
        #create a list of remaining led tags which are allowed
        remaining_led_tags = [i for i in tags if i in run_dbtags]
        if len(remaining_led_tags) <= 0:
            continue
        
        if 'source' in i_c:
            run_source = i_c['source']['type']
        #print(run_source, run_number, run_date)
        
        i_data = None
        if 'data' in i_c:
            i_data = i_c['data']
        else:
            continue

        rucio_safe = {}
        rucio_safe['rucio_rse'] = None
        rucio_safe['rucio_rule'] = None
        rucio_safe['rucio_location'] = None
        rucio_safe['tag'] = run_dbtags
        rucio_safe['size'] = i_c['raw_size_byte']
            
        for i_d in i_data:
            if i_d['host'] != 'rucio-catalogue':
                continue
            if i_d['status'] != 'transferred':
                continue
            
            rucio_safe['rucio_rse'] = i_d['rse']
            rucio_safe['rucio_rule'] = i_d['rule_info']
            rucio_safe['rucio_location'] = i_d['location']
        safer[run_name]=rucio_safe
        
    return safer
        
#Main:
def led_purge(led_store=None, purge=-1):
    
    #check for input path first:
    if led_store == None:
        return False
    if purge == -1:
        return False
    
    #1) Check for folders in the calibration dir:
    dt_today = datetime.datetime.today()
    dt_recent = timedelta(days=purge)
    dt_begin = dt_today-dt_recent
        
    #Grab only folders which are not hidden and follow the pmt raw data pattern:
    level1 = [f for f in os.listdir(led_store) if (not f.startswith('.') and f.startswith('led_raw_data_'))]
    
    purge_level = []
    print("Remove folders which are older then {d} days".format(d=purge))
    for il in level1:
        #stupid condition to get a valid date and be careful to remove too much from the directory
        if 'led_raw_data_' not in il:
            continue
        if len(il.split("_")[3]) != 6:
            continue
        if 'PMTGainCalibration' == il or 'make_hist' == il or 'gain_calculation' == il:
            continue
            
        date_ext = il.split("_")[3]
            
        date_ext = datetime.datetime.strptime(date_ext, '%y%m%d')
        rmfolder = os.path.join(led_store, il)
        if date_ext < dt_begin:
            #shutil.rmtree(rmfolder)
            print("  <> folder", rmfolder)
            purge_level.append(rmfolder)
        else:
            print(" KEEP! -> {f}".format(f=rmfolder))
    
    return purge_level

def led_download(led_store=None, get=1):
    
    #Loading the Rucio part:
    _account = "xenon-analysis"
    _host    = "midway2"
    _certpro = "/project/lgrandi/xenon1t/grid_proxy/xenon_service_proxy"

    print("  <> Load Rucio")
    print("     - User {user}".format(user=_account))
    print("     - Host config {hc}".format(hc=_host))
    rc = RucioAPI()
    rc.SetAccount(_account)
    rc.SetHost(_host)
    rc.LoadProxy(_certpro)
    rc.ConfigHost()
    print("  <Rucio loaded>")
    
    #check for input path first:
    if led_store == None:
        return False
    
    #Define some standard paths for LED downloads:
    if led_store[-1] != "/":
        led_store+="/"
    led_dir = "{led_store}led_raw_data_{date}".format(led_store=led_store, date="{date}")

    #Get all DB entries about LED files:
    led_call = getLEDCalibration(get)
    
    
    #Analyse the runDB entries before going to the download section
    download_success = {}
    for key, val in led_call.items():
        cal_day = key.split("_")[0]
        cal_time= key.split("_")[1]
        print("Check paths for {k}".format(k=key))
        
        #check first if date folder exists and create if necessary:
        path_to_check = led_dir.format(date=cal_day)
        if not os.path.isdir(path_to_check):
            os.makedirs(path_to_check)
        
        #check for the subfolders:
        path_to_check_sub = os.path.join(path_to_check, "{date}_{time}".format(date=cal_day, time=cal_time) )
        if not os.path.isdir(path_to_check_sub):
            os.makedirs(path_to_check_sub)
        
        f_size = int(get_size(path_to_check_sub))
        f_size_db = int(val['size'])
        
        if f_size == f_size_db:
            download_success["{date}_{time}".format(date=cal_day, time=cal_time)] = "Available"
            continue
        
        #Download:
        print("Start download: {k}".format(k=key))
        rc_loc = led_call[ "{date}_{time}".format(date=cal_day, time=cal_time)]['rucio_location']
        if rc_loc == None:
            continue
        rc_scope = rc_loc.split(":")[0]
        rc_dname = rc_loc.split(":")[1]
                
        rc.Download(scope=rc_scope, dname=rc_dname, destination=path_to_check_sub)
        print(" Downloaded to: ", path_to_check_sub)
        
        #check for success by database and folder comparison:
        f_size = int(get_size(path_to_check_sub))
        f_size_db = int(val['size'])
        
        if f_size == f_size_db:
            download_success["{date}_{time}".format(date=cal_day, time=cal_time)] = True
        
        print("Download success {k}".format(k=download_success))
    
    return download_success
        
def led_keeper():

    parser = argparse.ArgumentParser(description="Submit ruciax tasks to batch queue.")

    parser.add_argument('--get', type=int,
                        help="Get LED data of he past N days (--get <N>) with default N=1",
                        default=0)
    parser.add_argument('--purge', type=int, default=-1,
                        help="Purge LED data of he past N days (--get <N>) with default N=-1")
    

    args = parser.parse_args()
    _get  = args.get
    _purge = args.purge

    #basic path for led calibration:
    led_store = "/project/lgrandi/pmt_calibration/PMTGainCalibration/"
    
    ##Get all DB entries about LED files:
    led_call = getLEDCalibration(_get)
    
    #get a list of dates:
    dates = []
    for i, j in led_call.items():
        date = i.split("_")[0]
        if date not in dates:
            dates.append(date)
    
    #Do downloads if necessary:
    if int(_get) > 0:
        print("Download to path {path}".format(path=led_store))
        dw_status = led_download(led_store, _get)
        for dwS_key, dwS_val in dw_status.items():
            print(dwS_key, dwS_val)
    
    #Delete folders which are older then N days:
    if int(_purge) > -1:
        print("Purge LED calibration data oder than {purge} days:".format(purge=_purge))
        dw_purge = led_purge(led_store, _purge)
        for ifolders in dw_purge:
            print("purged:", ifolders)

    
if __name__ == '__main__':
    led_keeper()