#!/usr/bin/env bash

function terminate {
    # arguments
    # $1 - exit code to terminate with
    # $2 - optional exit message
    # $3 - optional file name to use

    # tar all files
    cd ${OUTDIR}
    if [[ -z $2 ]]
    then
        tar cvjf ${start_dir}/${JOBID}_output.tar.bz2 *
    else
        tar cvjf ${start_dir}/${JOBID}_$2_output.tar.bz2 *
    fi

    # copy files on stash
    #gfal-copy -p file://${G4_FILENAME}.tgz gsiftp://gridftp.grid.uchicago.edu:2811/cephfs/srm/xenon/xenon1t/simulations/mc_$MCVERSION/pax_$PAXVERSION/$MCFLAVOR/$CONFIG/${JOBID}_output.tar.bz2

    # Cleanup
    rm -fr $work_dir

    cd $start_dir

    exit $1
}

function print_job_info {
    # output job/node information
    echo "Start time: " `/bin/date`
    echo "Job is running on node: " `/bin/hostname`
    echo "Job running as user: " `/usr/bin/id`
    echo "Job is running in directory: $PWD"

    if [[ -n $MC_DEBUG ]]
    then
        echo "Arguments: "
        i=1
        for var in $@
        do
          echo "$i -- '$var'"
          let i++
        done
    fi

}

function parse_args {
    while ( "$#" )
    do
        case $1 in
          -j|--jobid)
            JOB_ID=$2
            shift 2
            ;;
          -f|--mc-flavor)
            MCFLAVOR=$2
            shift 2
            ;;
          -c|--mc-config)
            MC_CONFIG=$2
            shift 2
            ;;
          -n|--num-events)
            NEVENTS=$2
            shift 2
            ;;
          -m|--mc-version)
            MC_VERSION=$2
            shift 2
            ;;
          -f|--fax-version)
            FAXVERSION=$2
            shift 2
            ;;
          -p|--pax-version)
            PAXVERSION=$2
            shift 2
            ;;
          -r|--save-raw)
            SAVE_RAW=1
            shift
            ;;
          -s|--science-run)
            SCIENCE_RUN=$2
            shift 2
            ;;
          --preinit-macro)
            PREINIT_MACRO=$2
            shift 2
            ;;
          --preinit-belt)
            PREINIT_BELT=$2
            shift 2
            ;;
          --preinit-efield)
            PREINIT_EFIELD=$2
            shift 2
            ;;
          --optical-setup)
            OPTICAL_SETUP=$2
            shift 2
            ;;
          --source_macro)
            SOURCE_MACRO=$2
            shift 2
            ;;
          --experiment)
            EXPERIMENT=$2
            shift 2
            ;;
          *)
            echo "Unknown option: $1"
            echo "Skipping"
            shift
            ;;
        esac
    done
}
