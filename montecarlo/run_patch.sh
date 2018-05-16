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
# $15 - experiment


source common_functions.sh
print_job_info
parse_args



echo "Assuming science run " ${SCIENCE_RUN}

# Taken from lax (https://github.com/XENON1T/lax/pull/62)
# e-lifetime: https://xecluster.lngs.infn.it/dokuwiki/doku.php?id=xenon:xenon1t:org:commissioning:meetings:20170628#electron_lifetime
if [[ ${SCIENCE_RUN} == 0 ]]; then
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

start_dir=$PWD


# Setup CVMFS directories
CVMFSDIR=/cvmfs/xenon.opensciencegrid.org
RELEASEDIR=${CVMFSDIR}/releases/mc/${MCVERSION}

# Get the directory where libopcodes is located, LD_LIBRARY_PATH gets wiped
# when source activate is run so we should set it after that for safety
PAX_LIB_DIR=${CVMFSDIR}/releases/anaconda/2.4/envs/pax_${PAXVERSION}/lib/

# Setup Geant4 macros
MACROSDIR=${RELEASEDIR}/macros/${EXPERIMENT}


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
    source ${CVMFSDIR}/software/mc_setup_G4p10.sh
else
    source ${CVMFSDIR}/software/mc_setup_G4p9.sh
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

# runPatch argument corresponding to MC_CONFIG variable above
case ${MC_CONFIG} in
    *"Kr83m"*)
        PATCH_TYPE=83
        ;;
    *"Kr85"*)
        PATCH_TYPE=85
        ;;
    *"Rn220"*)
        PATCH_TYPE=21
        ;;
    *"Rn222"*)
        PATCH_TYPE=31
        ;;
    *)
        echo "Unknown MC_CONFIG value: ${MC_CONFIG}"
        terminate 10

esac



# Start of simulations #
CPATH=${OLD_CPATH}
source ${CVMFSDIR}/software/mc_setup_G4p9.sh

if [[ ${MC_FLAVOR} == NEST ]]; then
    # Patch stage
    PATCHEXEC=${RELEASEDIR}/runPatch
    (time ${PATCHEXEC} -i ${G4_FILENAME}.root -o ${G4PATCH_FILENAME}.root -t ${PATCH_TYPE};) 2>&1 | tee ${G4PATCH_FILENAME}.log
    if [ $? -ne 0 ];
    then
      terminate 11 "Error running patch"
    fi
    PAX_INPUT_FILENAME=${G4PATCH_FILENAME}

    terminate 0 "patch successfully completed" patch
else
    # nSort Stage
    ln -sf ${RELEASEDIR}/data

    # Old nSort executable
    #NSORTEXEC=${RELEASEDIR}/nSort
    #(time ${NSORTEXEC} -m 2 -s 2 -i ${G4_FILENAME} -f ${EFIELD};) 2>&1 | tee ${G4NSORT_FILENAME}.log

    # XENON1T SR0 models
    ln -sf ${RELEASEDIR}/nSortSrc/* .
    source deactivate
    CPATH=${OLD_CPATH}
    rm -r ~/.cache/rootpy/*
    source activate pax_${FAXVERSION}
    python GenerateGeant4.py --InputFile ${G4_FILENAME}.root --OutputFilename ${G4NSORT_FILENAME}.root

    if [ $? -ne 0 ];
    then
      terminate 12 "Error running nSort"
    fi
    PAX_INPUT_FILENAME=${G4NSORT_FILENAME}
    terminate 0 "nSort successfully completed" patch

fi

