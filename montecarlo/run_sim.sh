#!/usr/bin/env bash
# Arguments
# $1 - job id
# $2 - mc_flavor
# $3 - mc_config
# $4 - events to simulate
# $5 - mc_version
# $6 - fax_version
# $7 - pax_version
# $8 - save_raw setting
# $9 - science run
# $10 - preinit_macro
# $11 - preinit_belt
# $12 - preinit_field
# $13 - optical_setup
# $14 - source_macro

function terminate {

    # tar all files                                                                         
    cd ${OUTDIR}
    tar cvjf ${start_dir}/${JOBID}_output.tar.bz2 *
    
    # copy files on stash                                                                    
    #gfal-copy -p file://${G4_FILENAME}.tgz gsiftp://gridftp.grid.uchicago.edu:2811/cephfs/srm/xenon/xenon1t/simulations/mc_$MCVERSION/pax_$PAXVERSION/$MCFLAVOR/$CONFIG/${JOBID}_output.tar.bz2
    
    # Cleanup
    rm -fr $work_dir
    
    cd $start_dir

    exit $1
}


echo "Start time: " `/bin/date`
echo "Job is running on node: " `/bin/hostname`
echo "Job running as user: " `/usr/bin/id`
echo "Job is running in directory: $PWD"

# used to label output
JOBID=$1

# Select MC code flavor
# (G4, NEST, G4p10)
MCFLAVOR=$2

# Specify simulation configuration
# (TPC_Kr83m TPC_Kr85 WholeLXe_Rn220 WholeLXe_Rn222)
CONFIG=$3

# Specify number of events
NEVENTS=$4

# Select MC version
MCVERSION=$5

# Select fax version
FAXVERSION=$6

# Select pax version
PAXVERSION=$7

# Save raw waveforms (0: no, 1: yes)
SAVE_RAW=0
if [[ "$8" == 1 ]]; then
    SAVE_RAW=$8
fi

# For configuring model parameters and cuts
# Warning: Currently only used for G4-NEST, fax and lax, but NOT nSort emission models 
SCIENCERUN=$9
echo "Assuming science run " ${SCIENCERUN}

# Taken from lax (https://github.com/XENON1T/lax/pull/62)
# e-lifetime: https://xecluster.lngs.infn.it/dokuwiki/doku.php?id=xenon:xenon1t:org:commissioning:meetings:20170628#electron_lifetime
if [[ ${SCIENCERUN} == 0 ]]; then
    DIFFUSION_CONSTANT=22.8  # cm^2/s
    DRIFT_VELOCITY=1.44      # um/ns
    ELECTRON_LIFETIME=450    # us
    EFIELD=124               # V/cm
else
    DIFFUSION_CONSTANT=31.73 # cm^2/s
    DRIFT_VELOCITY=1.335     # um/ns
    ELECTRON_LIFETIME=550    # us
    EFIELD=82                # V/cm
fi

# runPatch argument corresponding to CONFIG variable above
if [[ ${CONFIG} == *"Kr83m"* ]]; then
    PATCHTYPE=83
elif [[ ${CONFIG} == *"Kr85"* ]]; then
    PATCHTYPE=85
elif [[ ${CONFIG} == *"Rn220"* ]]; then
    PATCHTYPE=21
elif [[ ${CONFIG} == *"Rn222"* ]]; then
    PATCHTYPE=31
fi
 
start_dir=$PWD


# Setup CVMFS directories
CVMFSDIR=/cvmfs/xenon.opensciencegrid.org
RELEASEDIR=${CVMFSDIR}/releases/mc/${MCVERSION}

# Get the directory where libopcodes is located, LD_LIBRARY_PATH gets wiped
# when source activate is run so we should set it after that for safety
PAX_LIB_DIR=${CVMFSDIR}/releases/anaconda/2.4/envs/pax_${PAXVERSION}/lib/

# Setup Geant4 macros
MACROSDIR=${RELEASEDIR}/macros

PREINIT_MACRO=${10}
if [[ -z $PREINIT_MACRO ]];
then
    PREINIT_MACRO=preinit_TPC.mac
    if [[ ${CONFIG} == *"muon"* || ${CONFIG} == *"MV"* ]]; then
        PREINIT_MACRO=preinit_MV.mac
    fi
    PREINIT_MACRO=${MACROSDIR}/${PREINIT_MACRO}
else
    if [[ -f ${start_dir}/${PREINIT_MACRO} ]]; then
        PREINIT_MACRO=${start_dir}/${PREINIT_MACRO}
    else
        PREINIT_MACRO=${MACROSDIR}/${PREINIT_MACRO}
    fi
fi
echo "Preinit macro: $PREINIT_MACRO" 

PREINIT_BELT=${11}
if [[ -z $PREINIT_BELT ]];
then
    PREINIT_BELT=preinit_B_none.mac
    if [[ ${CONFIG} == *"B_"* ]]; then
        for belt_type in ib ub NGpos
        do
            if [[ ${CONFIG} == *"_${belt_type}"* ]]; then
                belt_config=${belt_type}`echo ${CONFIG} | sed -e "s/.*${belt_type}\(.*\)/\1/"`
            fi
        done

        PREINIT_BELT=preinit_B_${belt_config}.mac
    fi
    PREINIT_BELT=${MACROSDIR}/${PREINIT_BELT}
else
    if [[ -f ${start_dir}/${PREINIT_BELT} ]]; then
        PREINIT_BELT=${start_dir}/${PREINIT_BELT}
    else
        PREINIT_BELT=${MACROSDIR}/${PREINIT_BELT}
    fi
fi
echo "Preinit belt: $PREINIT_BELT" 

PREINIT_EFIELD=${12}
if [[ -z $PREINIT_EFIELD ]];
then
    if [[ ${SCIENCERUN} == 0 ]]; then
        PREINIT_EFIELD=preinit_EF_C12kVA4kV.mac
    else
        PREINIT_EFIELD=preinit_EF_C8kVA4kV.mac
    fi
    PREINIT_EFIELD=${MACROSDIR}/${PREINIT_EFIELD}
else
    if [[ -f ${start_dir}/${PREINIT_EFIELD} ]]; then
        PREINIT_EFIELD=${start_dir}/${PREINIT_EFIELD}
    else
        PREINIT_EFIELD=${MACROSDIR}/${PREINIT_EFIELD}
    fi
fi
echo "Preinit efield: $PREINIT_EFIELD"

OPTICAL_SETUP=${13}
if [[ -z $OPTICAL_SETUP ]];
then
    OPTICAL_SETUP=${MACROSDIR}/setup_optical.mac
else
    if [[ -f ${start_dir}/${OPTICAL_SETUP} ]]; then
        OPTICAL_SETUP=${start_dir}/${OPTICAL_SETUP}
    else        
        OPTICAL_SETUP=${MACROSDIR}/${OPTICAL_SETUP}
    fi
fi
echo "Optical macro: $OPTICAL_SETUP" 

SOURCE_MACRO=${14}
if [[ -z $SOURCE_MACRO ]];
then
    SOURCE_MACRO=${MACROSDIR}/run_${CONFIG}.mac
else
    if [[ -f ${start_dir}/${SOURCE_MACRO} ]]; then
        SOURCE_MACRO=${start_dir}/${SOURCE_MACRO}
    else
        SOURCE_MACRO=${MACROSDIR}/${SOURCE_MACRO}
    fi
fi
echo "Source macro: $SOURCE_MACRO"

# set HOME directory if it's not set
if [[ ${HOME} == "" ]];
then
    export HOME=$PWD
fi

########################################

# Set pipe to propagate error codes to $?
set -o pipefail

# Setup the software
export PATH="${CVMFSDIR}/releases/anaconda/2.4/bin:$PATH"
source activate mc

# make sure libopcodes is in the LD_LIBRARY_PATH
if [[ ! `/bin/env` =~ .*${PAX_LIB_DIR}.* ]];
then
    export LD_LIBRARY_PATH=$PAX_LIB_DIR:$LD_LIBRARY_PATH
fi

if [ $? -ne 0 ];
then
  exit 1
fi

if [[ ${MCFLAVOR} == G4p10 ]]; then
    source ${CVMFSDIR}/software/mc_setup.sh
else
    source ${CVMFSDIR}/software/mc_old_setup.sh
fi
if [ $? -ne 0 ];
then
  exit 2
fi

source ${RELEASEDIR}/setup.sh
if [ $? -ne 0 ];
then
  exit 3
fi

# Setting up directories

OUTDIR=$start_dir/output
mkdir -p  ${OUTDIR}
if [ $? -ne 0 ];
then
  exit 4
fi

if [ "$OSG_WN_TMP" == "" ];
then
    OSG_WN_TMP=$PWD
fi

work_dir=`mktemp -d --tmpdir=$OSG_WN_TMP`
cd $work_dir

# Filenaming
SUBRUN=`printf "%05d\n" $JOBID`
FILEROOT=Xenon1T_${CONFIG}
FILENUM=${FILEROOT}_${SUBRUN}
FILENAME=${OUTDIR}/${FILENUM}
G4_FILENAME=${FILENAME}_g4mc_${MCFLAVOR}
G4PATCH_FILENAME=${G4_FILENAME}_Patch
G4NSORT_FILENAME=${G4_FILENAME}_Sort

# Start of simulations #

# Geant4 stage
G4EXEC=${RELEASEDIR}/xenon1t_${MCFLAVOR}
ln -sf ${MACROSDIR} # For reading e.g. input spectra from CWD

(time ${G4EXEC} -p ${PREINIT_MACRO} -b ${PREINIT_BELT} -e ${PREINIT_EFIELD} -s ${OPTICAL_SETUP} -f ${SOURCE_MACRO} -n ${NEVENTS} -o ${G4_FILENAME}.root;) 2>&1 | tee ${G4_FILENAME}.log
if [ $? -ne 0 ];
then
    terminate 10
fi

# Skip the rest for optical photons
if [[ ${CONFIG} == *"optPhot"* ]]; then
    terminate 0
fi

source ${CVMFSDIR}/software/mc_old_setup.sh

if [[ ${MCFLAVOR} == NEST ]]; then
    # Patch stage
    if [[ ${PATCHTYPE} != "" ]]; then
        PATCHEXEC=${RELEASEDIR}/runPatch
        (time ${PATCHEXEC} -i ${G4_FILENAME}.root -o ${G4PATCH_FILENAME}.root -t ${PATCHTYPE};) 2>&1 | tee ${G4PATCH_FILENAME}.log
        if [ $? -ne 0 ];
        then
          terminate 11
        fi
        PAX_INPUT_FILENAME=${G4PATCH_FILENAME}

    # Some configurations do not require Patch (or are not yet implemented)
    else
        PAX_INPUT_FILENAME=${G4_FILENAME}
    fi
else
    # nSort Stage
    ln -sf ${RELEASEDIR}/data
    
    # Old nSort executable
    #NSORTEXEC=${RELEASEDIR}/nSort
    #(time ${NSORTEXEC} -m 2 -s 2 -i ${G4_FILENAME} -f ${EFIELD};) 2>&1 | tee ${G4NSORT_FILENAME}.log
    
    # XENON1T SR0 models
    ln -sf ${RELEASEDIR}/nSortSrc/* .
    source deactivate
    source activate pax_${FAXVERSION}
    python GenerateGeant4.py --InputFile ${G4_FILENAME}.root --OutputFilename ${G4NSORT_FILENAME}.root
    
    if [ $? -ne 0 ];
    then
      terminate 12
    fi
    PAX_INPUT_FILENAME=${G4NSORT_FILENAME}
fi

RAW_FILENAME=${PAX_INPUT_FILENAME}_raw
PAX_FILENAME=${PAX_INPUT_FILENAME}_pax
HAX_FILENAME=${PAX_INPUT_FILENAME}_hax
FAX_FILENAME=${FILENAME}_faxtruth
LAX_FILENAME=${PAX_INPUT_FILENAME}_lax

# fax+pax stages
source deactivate
source activate pax_${FAXVERSION}
# make sure libopcodes is in the LD_LIBRARY_PATH
if [[ ! `/bin/env` =~ .*${PAX_LIB_DIR}.* ]];
then
    export LD_LIBRARY_PATH=$PAX_LIB_DIR:$LD_LIBRARY_PATH
fi

# fax+pax run-dependent configuration
FAX_PAX_CONFIG="[WaveformSimulator]truth_file_name=\"${FAX_FILENAME}\";"

# Do not save raw waveforms
if [[ ${SAVE_RAW} == 0 && ${PAXVERSION} == ${FAXVERSION} ]]; then
    (time paxer --input ${PAX_INPUT_FILENAME}.root --config XENON1T SimulationMCInput SR${SCIENCERUN}_parameters --config_string "${FAX_PAX_CONFIG}" --output ${PAX_FILENAME};) 2>&1 | tee ${PAX_FILENAME}.log

    if [ $? -ne 0 ];
    then
	terminate 13
    fi

# Save raw waveforms or different fax/pax versions
else
    (time paxer --input ${PAX_INPUT_FILENAME}.root --config XENON1T reduce_raw_data SimulationMCInput SR${SCIENCERUN}_parameters --config_string "${FAX_PAX_CONFIG}" --output ${RAW_FILENAME};) 2>&1 | tee ${RAW_FILENAME}.log

    if [ $? -ne 0 ];
    then
	terminate 14
    fi

    if [[ ${PAXVERSION} != ${FAXVERSION} ]];
    then
	    source activate pax_${PAXVERSION}
        # make sure libopcodes is in the LD_LIBRARY_PATH
        if [[ ! `/bin/env` =~ .*${PAX_LIB_DIR}.* ]];
        then
            export LD_LIBRARY_PATH=$PAX_LIB_DIR:$LD_LIBRARY_PATH
        fi

    fi

    (time paxer --ignore_rundb --input ${RAW_FILENAME} --config XENON1T SR${SCIENCERUN}_parameters --config_string "${FAX_PAX_CONFIG}" --output ${PAX_FILENAME};) 2>&1 | tee ${PAX_FILENAME}.log

    if [ $? -ne 0 ];
    then
	terminate 15
    fi

    if [[ ${SAVE_RAW} == 0 ]]; then
	rm -r ${RAW_FILENAME}
    fi
fi

source activate pax_${FAXVERSION}
# make sure libopcodes is in the LD_LIBRARY_PATH
if [[ ! `/bin/env` =~ .*${PAX_LIB_DIR}.* ]];
then
    export LD_LIBRARY_PATH=$PAX_LIB_DIR:$LD_LIBRARY_PATH
fi

# Flatten fax truth info
FAXSORT_FILENAME=${FAX_FILENAME}_sort
FAXSORT_OUTPUT_FORMAT=2 # Pickle + ROOT
(time python ${CVMFSDIR}/releases/processing/montecarlo/fax_waveform/TruthSorting_arrays.py ${FAX_FILENAME}.csv ${FAXSORT_FILENAME} ${FAXSORT_OUTPUT_FORMAT};) 2>&1 | tee ${FAXSORT_FILENAME}.log
if [ $? -ne 0 ];
then
    terminate 16
fi
rm ${FAX_FILENAME}.*  # Peak-by-peak file with all photoionization info


# hax stage
HAX_TREEMAKERS="Corrections Basics Fundamentals CorrectedDoubleS1Scatter LargestPeakProperties TotalProperties Extended"

# ROOT output
(time haxer --main_data_paths ${OUTDIR} --input ${PAX_FILENAME##*/} --pax_version_policy loose --treemakers ${HAX_TREEMAKERS} --force_reload;) 2>&1 | tee ${HAX_FILENAME}.log
if [ $? -ne 0 ];
then
  terminate 17
fi

# Pickle output
(time haxer --main_data_paths ${OUTDIR} --input ${PAX_FILENAME##*/} --pax_version_policy loose --treemakers ${HAX_TREEMAKERS} --force_reload --preferred_minitree_format pklz;) 2>&1 | tee -a ${HAX_FILENAME}.log
if [ $? -ne 0 ];
then
  terminate 18
fi

# Move hax output
cp *.root *.pklz ${OUTDIR} 

# lax stage
(time laxer --run_number -1 --sciencerun ${SCIENCERUN} --pax_version ${PAXVERSION#"v"} --minitree_path ${OUTDIR} --filename ${PAX_FILENAME##*/} --output_path ${LAX_FILENAME};) 2>&1 | tee ${LAX_FILENAME}.log

if [ $? -ne 0 ];
then
  terminate 19
fi

#rm ${PAX_FILENAME}.root  # Delete pax output for now

terminate 0
