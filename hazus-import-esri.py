# -*- coding: utf-8 -*-
"""
Hazus-MH International Model Toolkit
Created by Jesse Rozelle, FEMA

This script assumes you're working with the Hazus-MH International Model Toolkit
blank State_DB.mdb and syHazusDB.mdb personal geodatabases.  If you are, then first 
attach a sampel PR.mdf database to HAZUSPLUSSRVR through SQL Server Management Studio.

Next point the tool to the folder containing your Hazus-MH International Model Toolkit
geodatabases.  The tool will then insert your data into the PR database, and syHazus database
overwriting the data contained with your new international study region data.

!!!!!!!WARNING!!!!!!! This step is irreversible and the data overwritten will be 
irretrievable.  Please proceed with caution.   

The author of this tool provides it as is, and is not responsible for any data lost
or corrupted in this process.  Use this tool at your own risk.

Enjoy!
"""

import arcpy
from arcpy import env
import os
env.overwriteOutput = 1
from time import clock
start = clock()


"""
!!!!!IMPORTANT:  The folderpath variable below is the only variable you need to edit. 
Point this to the folder containing your completed Hazus-MH International Model Toolkit
geodatabases.  !!!!!!!WARNING!!!!!!! This step is irreversible and the data overwritten will be 
irretrievable.  Please proceed with caution.  
"""
folderpath = r'C:\UCD\Thesis\Data\Hazus_Data_4_2\Nepal_Study_Region\Maui_Build2_No_Adobe'

env.workspace = folderpath
compname = os.environ['COMPUTERNAME']
sqlname = 'HAZUSPLUSSRVR'

print "SQl Connection Established"

servername = (compname + '\\' + sqlname)
service = 'sde:sqlserver:' + servername

state= 'NP'

statedb = (state + '_Hazus.sde')

authtype = 'DATABASE_AUTH'
username = 'hazuspuser'
password = 'Gohazusplus_02'
statepath = (folderpath + '\\' + statedb)
gdbpath = (folderpath + '\\' + 'Hazus_State.mdb')
sygdb = (folderpath + '\\' + 'syHazus.mdb')
#os.remove(folderpath + '\\' +'HazusExport.sde')

print "Creating SDE connection files"
arcpy.CreateArcSDEConnectionFile_management(env.workspace,'syHazus.sde',servername,service,'syHazus', authtype,username,password)
arcpy.CreateArcSDEConnectionFile_management(env.workspace,statedb,servername,service,state, authtype,username,password)
print "Hazus SQL Server SDE connection created at",statepath

sySQL = (folderpath + '\\syHazus.sde')

env.workspace = gdbpath
featureclasses = arcpy.ListFeatureClasses()
tables = arcpy.ListTables()

print "Custom State Database Feature Class List:"
print featureclasses

print "Custom State Database Table List:"
print tables

print "Deleting Problem Tables"
arcpy.Delete_management(statepath + '/' +'huUserDefinedFlty')
arcpy.Delete_management(statepath + '/' +'eqUserDefinedFlty')
arcpy.Delete_management(statepath + '/' +'flUserDefinedFlty')

print "Importing Custom State Database Tables"

for i, elem in enumerate(tables):
    print "i=",i,"elem", elem
    #if elem !='clBldgTypeHu':
    arcpy.TableToTable_conversion (elem,statepath, tables[i], "", "")

print "Importing Custom State Database Feature Classes"

for i, elem in enumerate(featureclasses):
    print "i=",i,"elem", elem
    arcpy.MakeFeatureLayer_management((featureclasses[i]), (featureclasses[i]), "", "", "")
    arcpy.CopyFeatures_management((featureclasses[i]), (statepath + '\\' + featureclasses[i]), "", "", "")
    fieldcheck = arcpy.ListFields(featureclasses[i])
    for fieldy in fieldcheck:
        if fieldy.name == "Usage_":
            print fieldy, "Usage Field Error Rectified"
            arcpy.AddField_management((statepath + '\\' + (featureclasses[i])), 'Usage', 'TEXT', 10)
            #arcpy.CalculateField_management((statepath + '\\' + (featureclasses[i])), 'Usage', '(!Usage_!)', 'python_9.3')
            arcpy.DeleteField_management((statepath + '\\' + (featureclasses[i])),'Usage_')
            arcpy.AddField_management((statepath + '\\' + (featureclasses[i])), 'Usage', 'TEXT', 10)
            #arcpy.CalculateField_management((statepath + '\\' + (featureclasses[i])), 'Usage', '(!Usage_!)', 'python_9.3')
            arcpy.DeleteField_management((statepath + '\\' + (featureclasses[i])),'Usage_')    

print "Importing Custom syHazus Content"
#Import syHazus data
env.workspace = sygdb
featureclasses2 = arcpy.ListFeatureClasses()
tables2 = arcpy.ListTables()

print "Custom syHazus Feature Class List"
print featureclasses2

print "Custom syHazus Table List"
print tables2

print "Importing Custom syHazus Tables"
for j, elem2 in enumerate(tables2):
    print "j=",j,"elem2", elem2
    arcpy.TableToTable_conversion (elem2,sySQL, tables2[j], "", "")
    
print "Importing Custom syHazus Feature Classes"

for j, elem2 in enumerate(featureclasses2):
    print "j=",j,"elem2", elem2
    arcpy.MakeFeatureLayer_management((featureclasses2[j]), (featureclasses2[j]), "", "", "")
    arcpy.CopyFeatures_management((featureclasses2[j]), (sySQL + '\\' + featureclasses2[j]), "", "", "")


print 'Elapsed processing time : ' + str(round(clock()-start,2)) + ' seconds'

