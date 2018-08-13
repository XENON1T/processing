# Processing

## Processing scripts for XENON data

The ```reconstruction``` directory has the scripts for reconstruction processing on OSG

The ```montecarlo``` directory has the scripts for running monte carlo simulations on OSG

## Software and Database Preparation

The ```deploy``` directory contains scripts for installing all XENON1T software. These are typically run automatically via https://xenon1t.deployhq.com

The ```RunsDB``` directory contains example notebooks for updating the RunsDB and CorrectionsDB whenever there are changes to correction maps in pax, etc.

## File distribution tools

The ```grid_proxy``` contains scripts for automatically creating common-use grid proxies for grid (Rucio) transfers. See ```renew-cron.sh``` for additional details and procedures.
