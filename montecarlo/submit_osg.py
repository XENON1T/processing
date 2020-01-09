import sys
import os
from datetime import date

##### INPUT PARAMETER #####

material_array = ["SS_OuterCryostat",
                "SS_InnerCryostat",
                "OuterCryostatReflector",
                "SS_BellPlate",
                "SS_BellSideWall",
                "PmtTpc",
                "Teflon_Pillar_",
                "SS_AnodeRing",
                "Teflon_TPC",
                "Copper_FieldGuard_",
                "Copper_FieldShaperRing_",
                "Copper_TopRing"
                "Teflon_BottomTPC",
                "Copper_BottomPmtPlate",
                ]

isotope_array = ["U238",
                "Co60",
                "K40",
                "Cs137",
                "Th228",
                "U235",
                "Th232",
                "Ra226",
                #"geantinos"
                ]
#isotope_array =[ "geantinos"]
material_array = ["SS_OuterCryostat"]
isotope_array=["U235"]

N = 100000#500000000 #total number of events
batch_size = 10000 #number events per job


for MATERIAL_STRING in material_array:
    for ISOTOPE_STRING in isotope_array:
        macro = "ER_"+ MATERIAL_STRING +"_" + ISOTOPE_STRING
        print("-------------- ", macro)
        print("python mc_process.py --flavor G4p10 --config %s --batch_size %i --events %i --mc-version er_arianna --fax-version head --pax-version v6.10.1 --sciencerun 1 --experiment XENONnT" %(macro, batch_size, N))
        os.system("python mc_process.py --flavor G4p10 --config %s --batch_size %i --events %i --mc-version er_arianna --fax-version head --pax-version v6.10.1 --sciencerun 1 --experiment XENONnT" %(macro,batch_size, N))
~                                              i
