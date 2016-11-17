#!/usr/bin/env bash
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

# Select MC version
MCVERSION=$4

# Specify number of events
NEVENTS=$5

# Select fax+pax version
PAXVERSION=$6



# runPatch argument corresponding to CONFIG variable above
if [[ ${CONFIG} == *"Kr83m"* ]]; then
    PATCHTYPE=83
elif [[ ${CONFIG} == *"Kr85"* ]]; then
    PATCHTYPE=85
elif [[ ${CONFIG} == *"Rn220"* ]]; then
    PATCHTYPE=21
elif [[ ${CONFIG} == *"Rn222"* ]]; then
    PATCHTYPE=31
else
    echo "Error: No PATCHTYPE for CONFIG = ${CONFIG}"
    exit
fi
    
########################################

# Setup the software
CVMFSDIR=/cvmfs/xenon.opensciencegrid.org
export PATH="${CVMFSDIR}/releases/anaconda/2.4/bin:$PATH"
source activate mc &> /dev/null

if [[ ${MCFLAVOR} == G4p10 ]]; then
    source ${CVMFSDIR}/software/mc_setup.sh
else
    source ${CVMFSDIR}/software/mc_old_setup.sh
fi

RELEASEDIR=${CVMFSDIR}/releases/mc/${MCVERSION}
source ${RELEASEDIR}/setup.sh

# Setting up directories
start_dir=$PWD

OUTDIR=$start_dir/output
mkdir -p  ${OUTDIR}

if [ "$OSG_WN_TMP" == "" ];
then
    OSG_WN_TMP=$PWD
fi
cd $OSG_WN_TMP

work_dir=`mktemp -d --tmpdir=$OSG_WN_TMP`
cd $work_dir

# Filenaming
SUBRUN=`printf "%06f\n" $JOBID`
FILEROOT=Xenon1T_${CONFIG}
FILENUM=${FILEROOT}_${SUBRUN}
FILENAME=${OUTDIR}/${FILENUM}
G4_FILENAME=${FILENAME}_g4mc_${MCFLAVOR}
G4PATCH_FILENAME=${G4_FILENAME}_Patch
G4NSORT_FILENAME=${G4_FILENAME}_Sort

# Start of simulations #

# Geant4 stage
G4EXEC=${RELEASEDIR}/xenon1t_${MCFLAVOR}
MACROSDIR=${RELEASEDIR}/macros
(time ${G4EXEC} -p ${MACROSDIR}/preinit.mac -f ${MACROSDIR}/run_${CONFIG}.mac -n ${NEVENTS} -o ${G4_FILENAME}.root;) &> ${G4_FILENAME}.log

source ${CVMFSDIR}/software/mc_old_setup.sh

if [[ ${MCFLAVOR} == NEST ]]; then
    # Patch stage
    PATCHEXEC=${RELEASEDIR}/runPatch
    (time ${PATCHEXEC} -i ${G4_FILENAME}.root -o ${G4PATCH_FILENAME}.root -t ${PATCHTYPE};) &> ${G4PATCH_FILENAME}.log
    PAX_INPUT_FILENAME=${G4PATCH_FILENAME}
else
    # nSort Stage
    NSORTEXEC=${RELEASEDIR}/nSort
    ln -sf ${RELEASEDIR}/data
    (time ${NSORTEXEC} -i ${G4_FILENAME};) &> ${G4NSORT_FILENAME}.log
    PAX_INPUT_FILENAME=${G4NSORT_FILENAME}
fi

PAX_FILENAME=${PAX_INPUT_FILENAME}_pax
HAX_FILENAME=${PAX_INPUT_FILENAME}_hax

# fax+pax stage
source deactivate &> /dev/null
source activate pax_${PAXVERSION} &> /dev/null
(time paxer --input ${PAX_INPUT_FILENAME}.root --config_string "[WaveformSimulator]truth_file_name=\"${FILENAME}_faxtruth\"" --config XENON1T SimulationMCInput --output ${PAX_FILENAME};) &> ${PAX_FILENAME}.log

# hax stage
HAXPYTHON="import hax; "
HAXPYTHON+="hax.init(main_data_paths=['${OUTDIR}'], minitree_paths=['${OUTDIR}'], pax_version_policy = 'loose'); "
HAXPYTHON+="hax.minitrees.load('${PAX_FILENAME##*/}', ['Basics', 'Fundamentals', 'DoubleScatter', 'LargestPeakProperties', 'TotalProperties']);"

(time python -c "${HAXPYTHON}";)  &> ${HAX_FILENAME}.log
#hadd ${HAX_FILENAME}.root ${PAX_FILENAME}_*

# Cleanup
rm -f pax*


cd $start_dir
rm -fr $work_dir
