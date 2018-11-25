# -*- coding: utf-8 -*-

import datetime
import pandas as pd
import v20
import os
import tables 
import tstables 

def download_historical_tick_data_from_Dukascopy(instrument,start_date,end_date):
    ''' Download tick data for the instrument for each day
        Example input arguments for the method are as follows:
        instrument = 'EUR_USD'
        start_date = datetime.date(2015,1,1)
        end_date = datetime.date.today()
    '''

    iterator = start_date
    
    while iterator <= end_date:
        
        instrumentname = instrument.replace("_","")
        date = str(iterator).replace("-","_")
        filename = instrumentname + '-' + date + '-' + date +'.csv'
        filelocation = os.path.join('..', '..', 'datastore', 'tick_data', instrument, filename)
        print(filelocation)
    
        if( not os.path.exists( filelocation ) and not iterator.isoweekday() == 6 ):
                
            print('Downloading ', instrument, ' for', str(iterator) )
            
            download_tick_data_through_duka( instrument, str(iterator), str(iterator) )
        
        iterator = iterator + datetime.timedelta(1,0)

def merge_historical_tick_data_to_hdf5(instrument,start_date,end_date):
    ''' Merge daily tick data to a single h5 file
        Example input arguments for the method are as follows:
        instrument = 'EUR_USD'
        start_date = datetime.date(2015,1,1)
        end_date = datetime.date.today()
    '''

    class desc(tables.IsDescription):
        ''' Description of TsTables table structure.
        '''
        timestamp = tables.Int64Col(pos=0)  
        ask = tables.Float64Col(pos=1)  
        bid = tables.Float64Col(pos=2)
        ask_volume = tables.Int64Col(pos=3)
        bid_volume = tables.Int64Col(pos=4)

    ''' Open an existing h5 file or create a new file and table 
    '''
    
    #instrument = instrument.replace("_","")
    file_path_h5 = '..\\..\\datastore\\tick_data\\{}.h5'.format(instrument)
    
    if( os.path.exists( file_path_h5) ):
    
        os.remove(file_path_h5)
    
        h5 = tables.open_file(file_path_h5, 'w')
        ts = h5.create_ts('/', 'data', desc)
    
    iterator = start_date
    
    while iterator <= end_date:
    
        temp_df = pd.DataFrame()
    
        instrumentname = instrument.replace("_","")
        date = str(iterator).replace("-","_")
        filename = instrumentname + '-' + date + '-' + date +'.csv'
        filelocation = os.path.join('..', '..', 'datastore', 'tick_data', instrument, filename)
        if( os.path.exists( filelocation ) and not iterator.isoweekday() == 6 ):
        
            print( 'Reading: ', filelocation )
            
            temp_df = pd.read_csv(filelocation, header=None, parse_dates=[0])
            temp_df = temp_df.sort_values([0], ascending=[True])
            
            temp_df = temp_df.set_index(0)
            ts.append(temp_df)
    
        iterator = iterator + datetime.timedelta(1,0)
        
    h5.close()
    
def download_tick_data_through_duka( instrument, start_date, end_date ):
    
    instrumentname = instrument.replace("_","")
    command = 'duka {} -s {} -e {}'.format(instrumentname, start_date, end_date)
    os.system(command)
    
    start_date = start_date.replace("-","_")
    end_date = end_date.replace("-","_")
    
    filename = instrumentname + '-' + start_date + '-' + end_date +'.csv'

    if( os.path.exists( filename ) ):

        if( os.path.getsize(filename) > 0 ):
            filenamefrom = filename
            filenameto = os.path.join('..', '..', 'datastore', 'tick_data', instrument, filename)
            filenametopath = os.path.join('..', '..', 'datastore', 'tick_data', instrument)
            
            if not os.path.exists(filenametopath):
                os.makedirs(filenametopath)
            
            os.rename(filenamefrom, filenameto)

        else:
            os.remove(filename)

def parse_date(timestamp):
    
    if len(timestamp.split('.')) > 1:
        
        extra_digits = len(timestamp.split('.')[-1]) - 6
        
        if extra_digits > 0:
        
            timestamp = timestamp[:-extra_digits]
        
    try:
    
        timestamp = datetime.datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S.%f")
    
    except:
    
        timestamp = datetime.datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S")
    
    return timestamp

def write2excel( df, filename ):
    
    try:
        
        filepath = os.path.join('..', '..', 'datastore', filename) + '.xlsx'
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        df.to_excel(writer )
        writer.save()

    except:
        
        print('Problem writing to file. Please make sure that the file is closed.')

def write_hdf_file(df, filename):
    filepath = os.path.join('..', '..', 'datastore', filename)
    df.to_hdf(filepath, 'time', mode='w')
   
def read_hdf_file(filename):
    df_temp = pd.DataFrame()
    filepath = os.path.join('..', '..', 'datastore', filename)
    if os.path.exists( filepath ):
        df_temp = pd.read_hdf(filepath)
    return df_temp

def convert_datetime_to_Oanda_format(dt):
    
    return dt.isoformat('T')+'Z'

def convert_Oanda_format_to_datetime(dt):
    
    dt = dt.replace('T',' ').replace('Z','')
    try:
    
        dt = datetime.datetime.strptime(dt,"%Y-%m-%d %H:%M:%S.%f")
    
    except:
    
        dt = datetime.datetime.strptime(dt,"%Y-%m-%d %H:%M:%S")
        
    return dt

