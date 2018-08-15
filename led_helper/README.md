To make life easier this script will download LED data of the past 7 days (<- adjustable) and keep them for at maximum of 50 days (<- adjustable) on Midway in the standard directory for LED gain calibrations:

  ```/project/lgrandi/pmt_calibration/PMTGainCalibration```
  
The script follows the standard assumption that led raw data are stored in folders (```led_raw_data_*```).

The advantage of this script is to reduce the workload on the shifters to copy LED data to Midway and make the book keeping. Instead it uses the Rucio catalog and copies latest LED raw data to Midway once they are successfully transferred into the Rucio catalog.

The script is executed by a cronjob which runs from OSG once a day. This should be often enough for the moment.
