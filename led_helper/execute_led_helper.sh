# .bashrc

#Load the lastest anaconda environment (pax_head):
export PATH=/project/lgrandi/anaconda3/bin:$PATH
source activate pax_head

#Execute the led helper:
#SCRIPT_PATH='/project/lgrandi/xenon1t/processing/led_helper/'
SCRIPT_PATH='/home/bauermeister/ToolBox/processing/led_helper/'
SCRIPT_EXE='led_helper.py'
SCRIPT_GET=' --get 7'
SCRIPT_PURGE=' --purge 50'
EXECUTE=$SCRIPT_PATH$SCRIPT_EXE$SCRIPT_GET$SCRIPT_PURGE
python $EXECUTE