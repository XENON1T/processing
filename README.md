# Processing

## Processing scripts for XENON data

The ```reconstruction``` directory has the scripts for reconstruction processing on OSG

The ```montecarlo``` directory has the scripts for running monte carlo simulations on OSG

## Software and Database Preparation

The ```deploy``` directory contains scripts for installing all XENON1T software. These are typically run automatically via https://xenon1t.deployhq.com

The ```RunsDB``` directory contains example notebooks for updating the RunsDB and CorrectionsDB whenever there are changes to correction maps in pax, etc.

## File distribution tools

The ```processing/grid_proxy``` contains scripts for automatically creating common-use grid proxies for grid (Rucio) transfers.
### Setup:
Put common grid certificate (cert/key file) onto OSG in the directory: 
  * ```/xenon/grid_certificate/rucio_service_cert.pem'```
  * ```/xenon/grid_certificate/rucio_service_key.pem'```
  
If not yet done, create a softlink at OSG:
  * ```ln -s /xenon/processing/grid_proxy grid_proxy```

Add a cronjob (cronjob -e)//
  * ```00 23 * * 5 /xenon/grid_proxy/renew-cron.sh```

### Check:
Check if read/write permissions are correct at Midway: 
```-rw-r----- 1 <user_who_runs_the_cronjob> pi-lgrandi   6517 Oct  1 08:29 xenon_service_proxy```

