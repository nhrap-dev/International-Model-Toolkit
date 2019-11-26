# International-Model-Toolkit

This repository contains two scripts that convert a Hazus inventory state to an international state or country: 1) hazus-import-os.py; and 2) hazus-import-esri.py.

Both scripts function similarly; however, hazus-import-os.py is an open-source tool avilable if the ESRI tool (hazus-import-esri.py) requires extensions you don't have. The use notes below are for the open-source tool, use notes for the ESRI tool are included in the script. Please provide any feedback you have for the open-source to FEMA_NHRAP@fema.dhs.gov so we can continue to develop it.

<h2>To use</h2>

1. download Hazus_State.mdb, syHazus.mdb and hazus-import-mdb.py
2. fill out the Hazus_State.mdb and syHazus.mdb with your own data
3. download a Hazus state database to overwrite from https://msc.fema.gov/portal/resources/hazus and extract it in the Hazus inventory folder (generally: C:\HazusData\Inventory)
    1. Tsunami only works with the following states: Alaska, American Samoa (TS only), California, Guam (TS only), Hawaii, Northern Mariana Islands (TS only), Oregon, Puerto Rico, Virgin Islands (TS only), Washington
4. open SQL Server Management Studio, connect to the Hazus server
    1. user: hazuspuser
    2. pw: Gohazusplus_02
5. attach the newly downloaded state database.
6. change the name of the database to the StateID used in your syHazus.mdb in the table syState
7. point the script inputs at your MDB files and specify the database name as "state" and run
 
<h2>Notes</h2>
 
* This script has been tested successfully for:
  - [x] earthquake
  - [x] tsunami
  - [ ] hurricane
  - [ ] flood
* once a state has been added to the syHazus database, it has to be removed before reading
 
<h2>!!!Warning!!!</h2>
Data overwritten will be irretrievable.  Please proceed with caution. We recommend backing up syHazus and the state database before running the script.  
<br/>
<br/>
The author of this tool provides it as is, and is not responsible for any data lost
or corrupted in this process.  Use this tool at your own risk.
