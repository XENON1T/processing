# This script is to be run as a crontab on login.xenon.ci-connect.net:
#     00 06 * * * /xenon/processing/led_helper/renew-cron.sh

ssh bauermeister@128.135.112.68 /project/lgrandi/xenon1t/processing/led_helper/execute_led_helper.sh
