#!/usr/bin/env bash
# Arguments used
# job_id
# mc_flavor
# mc_config
# events to simulate
# mc_version
# science run
# preinit_macro
# preinit_belt
# preinit_field
# optical_setup
# source_macro
# experiment



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
CVMFS_DIR=/cvmfs/xenon.opensciencegrid.org
RELEASE_DIR=${CVMFS_DIR}/releases/mc/${MC_VERSION}

# Setup Geant4 macros
MACROS_DIR=${RELEASE_DIR}/macros/${EXPERIMENT}

if [[ -z $PREINIT_MACRO ]];
then
    PREINIT_MACRO=preinit_TPC.mac
    if [[ ${MC_CONFIG} == *"muon"* || ${MC_CONFIG} == *"MV"* ]]; then
        PREINIT_MACRO=preinit_MV.mac
    fi
    PREINIT_MACRO=${MACROS_DIR}/${PREINIT_MACRO}
else
    if [[ -f ${start_dir}/${PREINIT_MACRO} ]]; then
        PREINIT_MACRO=${start_dir}/${PREINIT_MACRO}
    else
        PREINIT_MACRO=${MACROS_DIR}/${PREINIT_MACRO}
    fi
fi
echo "Preinit macro: $PREINIT_MACRO"

if [[ -z $PREINIT_BELT ]];
then
    PREINIT_BELT=preinit_B_none.mac
    if [[ ${MC_CONFIG} == *"B_"* ]]; then
        for belt_type in ib ub NGpos
        do
            if [[ ${MC_CONFIG} == *"_${belt_type}"* ]]; then
                belt_config=${belt_type}`echo ${MC_CONFIG} | sed -e "s/.*${belt_type}\(.*\)/\1/"`
            fi
        done

        PREINIT_BELT=preinit_B_${belt_config}.mac
    fi
    PREINIT_BELT=${MACROS_DIR}/${PREINIT_BELT}
else
    if [[ -f ${start_dir}/${PREINIT_BELT} ]]; then
        PREINIT_BELT=${start_dir}/${PREINIT_BELT}
    else
        PREINIT_BELT=${MACROS_DIR}/${PREINIT_BELT}
    fi
fi
echo "Preinit belt: $PREINIT_BELT"

if [[ -z $PREINIT_EFIELD ]];
then
    if [[ ${SCIENCE_RUN} == 0 ]]; then
        PREINIT_EFIELD=preinit_EF_C12kVA4kV.mac
    else
        PREINIT_EFIELD=preinit_EF_C8kVA4kV.mac
    fi
    PREINIT_EFIELD=${MACROS_DIR}/${PREINIT_EFIELD}
else
    if [[ -f ${start_dir}/${PREINIT_EFIELD} ]]; then
        PREINIT_EFIELD=${start_dir}/${PREINIT_EFIELD}
    else
        PREINIT_EFIELD=${MACROS_DIR}/${PREINIT_EFIELD}
    fi
fi
echo "Preinit efield: $PREINIT_EFIELD"

if [[ -z $OPTICAL_SETUP ]];
then
    OPTICAL_SETUP=${MACROS_DIR}/setup_optical.mac
else
    if [[ -f ${start_dir}/${OPTICAL_SETUP} ]]; then
        OPTICAL_SETUP=${start_dir}/${OPTICAL_SETUP}
    else
        OPTICAL_SETUP=${MACROS_DIR}/${OPTICAL_SETUP}
    fi
fi
echo "Optical macro: $OPTICAL_SETUP"

if [[ -z $SOURCE_MACRO ]];
then
    SOURCE_MACRO=${MACROS_DIR}/run_${MC_CONFIG}.mac
else
    if [[ -f ${start_dir}/${SOURCE_MACRO} ]]; then
        SOURCE_MACRO=${start_dir}/${SOURCE_MACRO}
    else
        SOURCE_MACRO=${MACROS_DIR}/${SOURCE_MACRO}
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
export PATH="${CVMFS_DIR}/releases/anaconda/2.4/bin:$PATH"
source activate mc

if [[ ${MC_FLAVOR} == G4p10 ]]; then
    source ${CVMFS_DIR}/software/mc_setup_G4p10.sh
else
    source ${CVMFS_DIR}/software/mc_setup_G4p9.sh
fi
if [ $? -ne 0 ];
then
  exit 2
fi

source ${RELEASE_DIR}/setup.sh
if [ $? -ne 0 ];
then
  exit 3
fi

# Setting up directories

OUT_DIR=$start_dir/output
mkdir -p  ${OUT_DIR}
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
SUBRUN=`printf "%05d\n" $JOB_ID`
FILEROOT=Xenon1T_${MC_CONFIG}
FILENUM=${FILEROOT}_${SUBRUN}
FILENAME=${OUT_DIR}/${FILENUM}
G4_FILENAME=${FILENAME}_g4mc_${MC_FLAVOR}
G4PATCH_FILENAME=${G4_FILENAME}_Patch
G4NSORT_FILENAME=${G4_FILENAME}_Sort

# Start of simulations #

# Geant4 stage
G4EXEC=${RELEASE_DIR}/xenon1t_${MC_FLAVOR}
SPECTRA_DIR=${RELEASE_DIR}/macros
ln -sf ${SPECTRA_DIR} # For reading e.g. input spectra from CWD

(time ${G4EXEC} -p ${PREINIT_MACRO} -b ${PREINIT_BELT} -e ${PREINIT_EFIELD} -s ${OPTICAL_SETUP} -f ${SOURCE_MACRO} \
                -n ${NEVENTS} -d ${EXPERIMENT} -o ${G4_FILENAME}.root;) 2>&1 | tee ${G4_FILENAME}.log
if [ $? -ne 0 ];
then
    terminate 10 "Error while running Geant4"
fi


terminate 0 "Geant4 successfully run" geant
