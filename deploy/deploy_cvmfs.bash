#!/bin/bash
#
# This script is run on osg-cvmfs.grid.uchicago.edu
# to deploy XENON1T software to CVMFS. Automatically called
# by https://xenon1t.deployhq.com
#
echo $1 $HOSTNAME

DIR=/home/xenon/deployHQ

PROGRAM=$1

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/bash
module load binutils/2.26

cvmfs_server transaction  xenon.opensciencegrid.org || true
echo ${PROGRAM}

# For creating local head installations
CVMFSDIR=/cvmfs/xenon.opensciencegrid.org
export PATH="${CVMFSDIR}/releases/anaconda/2.4/bin:$PATH"
source activate pax_head
pip uninstall -y ${PROGRAM}
cd ${DIR}/${PROGRAM}_deploy
rm -rf build
python setup.py install
source deactivate

# Also install in latest tagged pax environment
if [[ ${PROGRAM} != "pax" ]]; then

# Disable installation into pax versioned environment -PdP 30/05/2017

    # Re-enable for cax only -PdP 30/06/2017
    if [[ ${PROGRAM} == "cax" ]]; then
        LATEST_PAX_TAG=`(cd ${DIR}/pax; git tag | sort -V | tail -n1)`
        source activate pax_${LATEST_PAX_TAG}
        cd ${DIR}/${PROGRAM}
        git pull
        python setup.py install
        source deactivate || true
    fi

    ~/fix_perms -d ${CVMFSDIR}/releases/anaconda/2.4/ --force
    cvmfs_server publish xenon.opensciencegrid.org

    exit  # Don't create tagged installation below
fi

# For creating tagged installations (of pax only)
AXDIR=${DIR}/${PROGRAM}
cd ${AXDIR}

# Update the head
git pull

# Get latest tag in repository
LATEST_TAG=`(git tag | sort -V | tail -n1)`

# Get current conda environments (currently 1 for each pax version)
AVAILABLE_TAGS=(`conda env list | grep pax_ | cut -f1 -d' '`)

echo "Latest tag: " ${LATEST_TAG}
echo "Available tags: " ${AVAILABLE_TAGS[@]}

if [[ ${LATEST_TAG} != "" ]]; then
  if [[ ! " ${AVAILABLE_TAGS[@]} " =~ "${LATEST_TAG}" ]]; then

    echo "Installing ${PROGRAM}_${LATEST_TAG}"

    #conda create --yes -n ${PROGRAM}_${LATEST_TAG} python=3.4.4 root=6 rootpy numpy scipy=0.18.1 pyqt=4.11 qt=4.8.7 hdf5=1.8.16 matplotlib=1.5.1 pandas cython h5py numba pip python-snappy pytables scikit-learn psutil pymongo paramiko dask root_pandas isl=0.12.2 jupyter
    conda create --name pax_${LATEST_TAG} --clone pax_head

    source activate ${PROGRAM}_${LATEST_TAG}

    # Not sure why root_numpy files are different after cloning, uncomment if getting root_numpy import errors  (19/08/2018 PdP)
    #rm -R ${CVMFSDIR}/releases/anaconda/2.4/envs/pax_${LATEST_TAG}/lib/python3.4/site-packages/root_numpy
    #cp -r ${CVMFSDIR}/releases/anaconda/2.4/envs/pax_head/lib/python3.4/site-packages/root_numpy ${CVMFSDIR}/releases/anaconda/2.4/envs/pax_${LATEST_TAG}/lib/python3.4/site-packages/.


    #conda update --yes matplotlib
    #pip install gmpy
    #pip install -U setuptools
    #pip install parsedatetime tqdm prettytable multihist
    #pip install Keras==2.1.2 tensorflow==1.4.1

    git checkout ${LATEST_TAG}

    python setup.py install

    git checkout master

    # Also install lax and hax in this new environment
    for ax in hax lax
    do
       (cd ${DIR}/${ax}; git pull; python setup.py install) 
    done

    # Install OSG branch for cax
    cd ~/deployHQ/cax
    git pull
    git checkout OSG_dev2
    git pull origin OSG_dev2
    python setup.py install
    git checkout master

    # Copy custom activation scripts
    ACTIVATE_SRC_DIR=${CVMFSDIR}/releases/anaconda/2.4/envs/pax_head/etc/conda/activate.d
    cp ${ACTIVATE_SRC_DIR}/*.sh ${CVMFSDIR}/releases/anaconda/2.4/envs/pax_${LATEST_TAG}/etc/conda/activate.d/.

    # Strange gfortran issue on osg-cvmfs
    cp /usr/lib64/libgfortran.so.1* ${CVMFSDIR}/releases/anaconda/2.4/envs/pax_${LATEST_TAG}/lib/. 

    # the code requires the same version of binutil libraries as on this host
    cp /usr/lib64/libopcodes-2.20.51.0.2-5.44.el6.so  ${CVMFSDIR}/releases/anaconda/2.4/envs/pax_${LATEST_TAG}/lib/.

    source deactivate || true
  fi
fi

~/fix_perms -d /cvmfs/xenon.opensciencegrid.org/releases/anaconda/2.4/ --force
cvmfs_server publish xenon.opensciencegrid.org
