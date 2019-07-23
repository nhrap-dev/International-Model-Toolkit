# International-Model-Toolkit

<h2>To use</h2>

1) download Hazus_State.mdb, syHazus.mdb and hazus-import-mdb.py
2) fill out the Hazus_State.mdb and syHazus.mdb with your own data
3) download a Hazus state database to overwrite from https://msc.fema.gov/portal/resources/hazus
3) open SQL Server Management Studio, connect to the Hazus server
 1) user: hazuspuser
 2) pw: Gohazusplus_02
4) attach the newly downloaded state database.
5) change the name of the database to the StateID used in your syHazus.mdb in the table syState
6) point the script inputs at your MDB files and specify the database name as "state" and run
 
<h2>Notes</h2>
 
* This script currently supports:
  [x] earthquake
  [x] tsunami
  [] hurricane
  [] flood
* once a state has been added to the syHazus database, it has to be removed before readding
 
<h2>!!!Warning!!!</h2>
Data overwritten will be irretrievable.  Please proceed with caution. We recommend backing up syHazus and the state database before running the script.

The author of this tool provides it as is, and is not responsible for any data lost
or corrupted in this process.  Use this tool at your own risk.
