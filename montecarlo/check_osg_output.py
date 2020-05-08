#!/usr/bin/python

import sys
import os
from datetime import date
#import tqdm

import subprocess
from pexpect import pxssh
##### INPUT PARAMETER #####
DATE_STRING = "20191125"
##### ##### #####
N_FILES = 10
flag = 0 #0 doesn't move the files, 1 does . 


localfile = DATE_STRING+"T"
mc_dir =  "/scratch/arianna/er/processing/montecarlo/ariannarocchetti/pegasus/montecarlo/"
scp_path = "ariannarocchetti@login.xenon.ci-connect.net"
scp_domain="login.xenon.ci-connect.net"

command = ("ssh ariannarocchetti@login.xenon.ci-connect.net ls  /scratch/arianna/er/processing/montecarlo/ariannarocchetti/pegasus/montecarlo/")
list_=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
(out, err)=list_.communicate()
out = out.decode("utf-8")
out = out.split("\n")
counter = 0
file_ok = 0
file_corrupted = 0
for i in range(0, len(out)-1):
    
    PATH = scp_path+mc_dir+out[i]+"/00/00/"

    for file in os.listdir(PATH):

            if file.endswith(".out.000"):
            
                counter = counter +1
                path_file = os.path.join(PATH, file)
                fp = open(path_file, 'r')

                if "fileMerger::CleanUp() Done" in fp.read():
                    file_ok = file_ok +1
                    fp.close()
                else:
                    fp = open(path_file, 'r')
                    lineList = fp.readlines()
                    print(lineList[-1])
                    print("check ---> ", path_file)
                    file_corrupted = file_corrupted +1
                    fp.close()

print("file success:", file_ok, "\ ", counter)
print("file bad :", file_corrupted)

