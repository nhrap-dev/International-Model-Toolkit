"""
Hazus-MH International Model Toolkit
Created by James Raines, FEMA
Adapted from Jesse Rozelle, FEMA

This script assumes you're working with the Hazus-MH International Model Toolkit
blank Hazus_State.mdb and syHazus.mdb personal geodatabases.

This tool overwrites a Hazus state inventory file with your Hazus_State.mdb. To start,
first attach a state inventory file HAZUSPLUSSRVR through SQL Server Management Studio.
(example state inventory file: PR.mdf)

Second, in SQL Server Management Studio, change the name of the database to the StateID
used in your syHazus.mdb in the table syState

Next, scroll to the bottom of the script and assign the following variables:
state, gdb_file_state, gdb_file_syhazus

Finally, run this function:
create_new_hazus_state(state, gdb_file_state, gdb_file_syhazus)

!!!!!!!WARNING!!!!!!! This step is irreversible and the data overwritten will be 
irretrievable.  Please proceed with caution. Recommend backing up syHazus a state data.

The author of this tool provides it as is, and is not responsible for any data lost
or corrupted in this process.  Use this tool at your own risk.

Enjoy!
"""

import pyodbc
import sqlalchemy
import urllib
import os
from osgeo import ogr
import geopandas as gpd
import pandas as pd
import numpy as np
from time import time

def setup_connections(state):
    """ Sets up connections to Hazus state and syHazus databases

    Keyword arguments:
        state: str -- state abbreviation of state database; ex: 'TX'

    Returns:
        cnxn_syhazus: pyodbc connection -- connection to hyHazus database
        cnxn_state: pyodbc connection -- connection to state database
    """
    compname = os.environ['COMPUTERNAME']
    try:
        username = 'hazuspuser'

        cnxn_syhazus = pyodbc.connect('Driver=ODBC Driver 11 for SQL Server;SERVER=' +
        compname + '\HAZUSPLUSSRVR;DATABASE=syHazus' +
        ';UID='+username+';PWD=Gohazusplus_02;MARS_Connection=Yes')

        cnxn_state = pyodbc.connect('Driver=ODBC Driver 11 for SQL Server;SERVER=' +
        compname + '\HAZUSPLUSSRVR;DATABASE='+ state +
        ';UID='+username+';PWD=Gohazusplus_02;MARS_Connection=Yes')
        return cnxn_syhazus, cnxn_state
    except:
        username = 'SA'

        cnxn_syhazus = pyodbc.connect('Driver=ODBC Driver 11 for SQL Server;SERVER=' +
        compname + '\HAZUSPLUSSRVR;DATABASE=syHazus' +
        ';UID='+username+';PWD=Gohazusplus_02;MARS_Connection=Yes')

        cnxn_state = pyodbc.connect('Driver=ODBC Driver 11 for SQL Server;SERVER=' +
        compname + '\HAZUSPLUSSRVR;DATABASE='+ state +
        ';UID='+username+';PWD=Gohazusplus_02;MARS_Connection=Yes')
        return cnxn_syhazus, cnxn_state

def getFeatureInfoDB(cnxn):
    """ Returns the name, type and columns for all tables in the Hazus database

    Keyword arguments:
        cnxn: pyodbc connection -- connection to Hazus database

    Returns:
        df: pandas dataframe
    """
    cursor = cnxn.cursor()
    sql = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
    cursor.execute(sql)
    req = cursor.fetchall()
    table_names = [x[2] for x in req]

    table_cols = []
    table_type = []
    for table in table_names:
        sql = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'"+table+"'"
        cursor.execute(sql)
        req = cursor.fetchall()
        col_names = list(map(lambda x: x[0], req))
        if 'shape' in list(map(lambda x: x.lower(), col_names)):
            table_type.append('SPATIAL')
        else:
            table_type.append('TABLE')
        remove_names = ['shape', 'Shape', 'SHAPE']
        for col in remove_names:
            if col in col_names:
                col_names.remove(col)
        table_cols.append(col_names)
    df = pd.DataFrame({'name': table_names, 'type': table_type, 'columnNames': table_cols})
    return df

def update_sql(gdb_file, tables, cnxn, database):
    """ Updates a Hazus database with a MDB database

    Keyword arguments:
        gdb_file: str -- file directory of the MDB database
        tables: pandas dataframe -- dataframe returned by getFeatureInfo method
        database: str -- name of database; either state abbreviation or 'syHazus'
    """
    engine = start_engine(database)
    for row in range(len(tables)):
        # set properties
        name = tables.loc[row, 'name']
        type = tables.loc[row, 'type']
        cols = tables.loc[row, 'columnNames']
        try:
            # set up connection to MDB
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' +
                'DBQ='+gdb_file+';'
                )
            cnxn_mdb = pyodbc.connect(conn_str)
            # get data from MDB
            cursor = cnxn_mdb.cursor()
            sql = "SELECT * FROM " + name
            df = pd.read_sql(sql, cnxn_mdb)
            # reconciles column names
            # removes unnecessary columns
            for col in df.columns:
                if col.lower() not in list(map(lambda x: x.lower(), cols)):
                    df = df.drop([col], axis=1)
            # add missing columns
            for col in cols:
                if col.lower() not in list(map(lambda x: x.lower(), df.columns)):
                    df[col] = np.nan
                if 'ZONE_' in df.columns:
                    df['ZONE'] = df['ZONE_']
            # Post to database
            # Post spatial table
            if type == 'SPATIAL':
                driver = ogr.GetDriverByName("PGeo")
                gdb = driver.Open(gdb_file, 0)
                layer = gdb.GetLayerByName(name)
                geoms = []
                for feature in layer:
                    try:
                        geom = feature.GetGeometryRef()
                        geoms.append(geom.ExportToWkt())
                    except: 
                        geoms.append('')
                df['geom'] = geoms
                cursor = cnxn.cursor()
                if database == 'syHazus':
                    cursor.execute("ALTER TABLE dbo."+name+" ADD geom TEXT")
                    cursor.commit()
                    df.to_sql(name, engine, if_exists='append', index=False)
                    cursor.execute("UPDATE dbo."+name+" SET Shape = geometry::STGeomFromText(geom, 4326) WHERE geom IS NOT NULL")
                    cursor.commit()
                    cursor.execute("ALTER TABLE "+name+" DROP COLUMN geom")
                    cursor.commit()
                else:
                    df.to_sql(name, engine, if_exists='replace', index=False)
                    cursor = cnxn.cursor()
                    cursor.execute("ALTER TABLE "+name+" ADD Shape geometry")
                    cursor.commit()
                    cursor.execute("UPDATE "+name+" SET Shape = geometry::STGeomFromText(geom, 4326) FROM "+ name)
                    cursor.commit() 
                    cursor.execute("ALTER TABLE "+name+" DROP COLUMN geom")
                    cursor.commit()
                print(name + ' success')
            # Post aspatial table
            else:
                if database == 'syHazus':
                    df.to_sql(name, engine, if_exists='append', index=False)
                else:
                    df.to_sql(name, engine, if_exists='replace', index=False)
                print(name + ' success')
        except Exception as e:
            print(name + '--' + str(e))

def drop_problem_tables(cnxn):
    """ Drops user defined tables in database that may cause problems

    Keyword arguments:
        cnxn: pyodbc connection -- connection to Hazus database
    """
    # tables to drop
    sql_query_drop = ["DROP TABLE dbo.huUserDefinedFlty;", 
    "DROP TABLE dbo.eqUserDefinedFlty",
    "DROP TABLE dbo.flUserDefinedFlty",
    "DROP TABLE dbo.tsUserDefinedFlty"]

    # drop problem tables
    for query in sql_query_drop:
        try:
            cursor = cnxn.cursor()
            cursor.execute(query)
            cursor.commit()
            print(query + ' successful')
        except Exception as e:
            print(str(e))

# create engine to post to database
def start_engine(database):
    """ Creates a sqlalchemy connection engine for pushing and putting data to SQL

    Keyword arguments:
        database: str -- name of database; either state abbreviation or 'syHazus'
    """
    compname = os.environ['COMPUTERNAME']
    try:
        username = 'hazuspuser'
        quoted = urllib.parse.quote_plus('Driver=ODBC Driver 11 for SQL Server;SERVER=' +
            compname + '\HAZUSPLUSSRVR;DATABASE='+ database +
            ';UID='+username+';PWD=Gohazusplus_02;MARS_Connection=Yes')
        engine = sqlalchemy.create_engine('mssql+pyodbc:///?odbc_connect={}'.format(quoted))
        return engine
    except:
        username = 'SA'
        quoted = urllib.parse.quote_plus('Driver=ODBC Driver 11 for SQL Server;SERVER=' +
            compname + '\HAZUSPLUSSRVR;DATABASE='+ database +
            ';UID='+username+';PWD=Gohazusplus_02;MARS_Connection=Yes')
        engine = sqlalchemy.create_engine('mssql+pyodbc:///?odbc_connect={}'.format(quoted))
        return engine

def rename_database(state, cursor):
    """ Renames SQL database

    Keyword arguments:
        current_name: str -- current name of database
        new_name: str -- new name of database
        cursor: pyodbc connection cursor object
    """
    cursor.execute("SELECT TOP (1) State from "+state+".dbo.hzCounty")
    new_name = cursor.fetchall()[0][0]
    query = """USE master;
        ALTER DATABASE """+state+"""
        SET SINGLE_USER
        WITH ROLLBACK IMMEDIATE
        ALTER DATABASE """+state+"""
        MODIFY NAME = """+new_name+""";
        ALTER DATABASE """+new_name+"""
        SET MULTI_USER"""

    try:
        cursor.execute(query)
        cursor.commit()
        print(query)
    except Exception as e:
        print(str(e))

def create_new_hazus_state(state, gdb_file_state, gdb_file_syhazus):
    """ Creates a new state in the Hazus database

    Keyword arguments:
        state: str -- name of database; either state abbreviation or 'syHazus'
        gdb_file_state: str -- file directory of a personal geodatabase (.mdb) with update data for a state database
        gdb_file_syhazus: str -- file directory of a personal geodatabase (.mdb) with update data for the syHazus database
    """
    t0 = time()
    print('Setting up connection to the databases')
    t1 = time()
    cnxn_syhazus, cnxn_state = setup_connections(state)
    print(time() - t1)
    print('Getting the name and file type of everything to be imported')
    t1 = time()
    # state_tables= getFeatureInfo(gdb_file_state)
    # syhazus_tables = getFeatureInfo(gdb_file_syhazus)
    state_tables= getFeatureInfoDB(cnxn_state)
    syhazus_tables = getFeatureInfoDB(cnxn_syhazus)
    print(time() - t1)
    print('Updating Hazus SQL state database')
    t1 = time()
    update_sql(gdb_file_state, state_tables, cnxn_state, state)
    print(time() - t1)
    print('Updating Hazus SQL syHazus database')
    t1 = time()
    update_sql(gdb_file_syhazus, syhazus_tables, cnxn_syhazus, 'syHazus')
    print(time() - t1)
    # print('Dropping problem tables')
    # t0 = time()
    # drop_problem_tables(cnxn_state)
    # print(time() - t1)
    print('Total elapsed time: ' + str(time() - t0))
    # rename_database(state, cnxn_state.cursor())
    

# Define inputs
state= 'NP'
gdb_file_state = r'C:\projects\International_syHazus\Hazus_State.mdb'
gdb_file_syhazus = r'C:\projects\International_syHazus\syHazus.mdb'


# Run import
create_new_hazus_state(state, gdb_file_state, gdb_file_syhazus)
