#!/usr/bin/env bash
############################################
#
# Usage: Need to modify all parameters and paths below, then:
#           ./run_fax.sh <output directory> <subrun number>
#
############################################

echo "Start time: " `/bin/date`
echo "Job is running on node: " `/bin/hostname`
echo "Job running as user: " `/usr/bin/id`
echo "Job is running in directory: $PWD"

###### General parameters #####
Detector=XENON1T
PaxVersion=v6.0.2

###### Simulation parameters #####
PhotonNumLower=1
PhotonNumUpper=200
ElectronNumLower=1
ElectronNumUpper=400

# Select fax+pax version
PAXVERSION=v6.0.2

# Specify number of events
NumEvents=10

# This run number (from command line argument)
SUBRUN=$2

########################################

# Setup the software
CVMFSDIR=/cvmfs/xenon.opensciencegrid.org
export PATH="${CVMFSDIR}/releases/anaconda/2.4/bin:$PATH"
source activate pax_${PAXVERSION} &> /dev/null

RELEASEDIR=/project/lgrandi/processing/montecarlo/fax_waveform

# Setting up directories
start_dir=$PWD


OUTDIR=$1/${SUBRUN}
mkdir -p ${OUTDIR}
cd ${OUTDIR}

#if [ "$OSG_WN_TMP" == "" ];
#then
#    OSG_WN_TMP=$PWD
#fi
#cd $OSG_WN_TMP
#
#work_dir=`mktemp -d --tmpdir=$OSG_WN_TMP`
#cd $work_dir

# Filenaming
FILEROOT=FakeWaveform_${Detector}_${SUBRUN}
FILENAME=${OUTDIR}/${FILEROOT}
CSV_FILENAME=${FILENAME}.csv       # Fake input data
FAX_FILENAME=${FILENAME}_truth.csv # fax truth info
PKL_FILENAME=${FILENAME}_truth.pkl # converted fax truth info
RAW_FILENAME=${FILENAME}_raw       # fax simulated raw data
PAX_FILENAME=${FILENAME}_pax       # pax processed data
HAX_FILENAME=${FILENAME}_hax       # hax reduced data

# Create the fake input data
python ${RELEASEDIR}/CreateFakeCSV.py ${NumEvents} ${PhotonNumLower} ${PhotonNumUpper} ${ElectronNumLower} ${ElectronNumUpper} ${CSV_FILENAME}

# Start of simulations #

# fax stage
(time paxer --input ${CSV_FILENAME} --config ${Detector} reduce_raw_data Simulation --config_string "[WaveformSimulator]truth_file_name=\"${FAX_FILENAME}\"" --output ${RAW_FILENAME};) &> ${RAW_FILENAME}.log

# convert fax truth to pickle
python ${RELEASEDIR}/ConvertFaxTruthToPickle.py ${FAX_FILENAME} ${PKL_FILENAME}

# pax stage
(time paxer --ignore_rundb --input ${RAW_FILENAME} --config ${Detector} --output ${PAX_FILENAME};) &> ${PAX_FILENAME}.log

# hax stage
HAXPYTHON="import hax; "
HAXPYTHON+="hax.init(main_data_paths=['${OUTDIR}'], minitree_paths=['${OUTDIR}'], pax_version_policy = 'loose'); "
HAXPYTHON+="hax.minitrees.load('${PAX_FILENAME##*/}', ['Basics', 'Fundamentals']);"

(time python -c "${HAXPYTHON}";)  &> ${HAX_FILENAME}.log

# Cleanup
rm -f pax*


cd $start_dir
#rm -fr $work_dir