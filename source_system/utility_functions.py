try:
    
    import datetime
    import pandas as pd
    import os
    import tables 

except Exception as e:
    
    print(e) 
    
class desc(tables.IsDescription):
    ''' Description of TsTables table structure.
    '''
    timestamp = tables.Int64Col(pos=0)  
    ask_c = tables.Float64Col(pos=1)  
    ask_h = tables.Float64Col(pos=2)  
    ask_l = tables.Float64Col(pos=3)  
    ask_o = tables.Float64Col(pos=4)  

    bid_c = tables.Float64Col(pos=5)  
    bid_h = tables.Float64Col(pos=6)  
    bid_l = tables.Float64Col(pos=7)  
    bid_o = tables.Float64Col(pos=8)  

    volume = tables.Int64Col(pos=9)

def read_database(symbol, granularity, account_type, read_start_dt, read_end_dt):

    file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(account_type,symbol,granularity)
    print("Reading from database located at: ", file_path)

    f = tables.open_file(file_path,'r')
    print(type(f))
    ts = f.root.data._f_get_timeseries()
    print(type(ts))    
    rows = ts.read_range(read_start_dt,read_end_dt)
    print(type(rows))
    f.close()
    
    return rows
    
def combine_databases(symbol, granularity, account_type):
        
    file_path_1 = '..\\..\\datastore\\_{}\\{}\\{}_2016.h5'.format(account_type,symbol,granularity)
    
    f = tables.open_file(file_path_1,'r')
    ts = f.root.data._f_get_timeseries()
    read_start_dt = datetime.datetime(2016,1,1,00,00)
    read_end_dt = datetime.datetime.utcnow()
    
    rows1 = ts.read_range(read_start_dt,read_end_dt)
    
    f.close()
    
    file_path_2 = '..\\..\\datastore\\_{}\\{}\\{}_2017.h5'.format(account_type,symbol,granularity)
    
    f = tables.open_file(file_path_2,'r')
    ts = f.root.data._f_get_timeseries()
    read_start_dt = datetime.datetime(2017,1,1,00,00)
    read_end_dt = datetime.datetime.utcnow()
    
    rows2 = ts.read_range(read_start_dt,read_end_dt)
    
    f.close()
    
    rows = rows1.append(rows2)
    
    file_path = '..\\..\\datastore\\_{}\\{}\\{}.h5'.format(account_type,symbol,granularity)
    
    f = tables.open_file(file_path, 'w')
    ts = f.create_ts('/', 'data', desc)
    ts.append(rows)
    f.close()

def write_df_to_excel(df, folderpath, filename):
              
    try:
        
        filepath = os.path.join( folderpath, filename)
        if( not os.path.exists(folderpath)):
            os.mkdir(folderpath) 

        print("Writing to file located at: ", filepath)
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        df.to_excel(writer)
        writer.save()

    except:
        
        print('Problem writing df to excel file. Please make sure that the file is closed.')

def write_df_to_hdf(df, folderpath, filename):

    try:
        
        filepath = os.path.join( folderpath, filename)
        if( not os.path.exists(folderpath)):
            os.mkdir(folderpath) 

        print("Writing to file located at: ", filepath)
        df.to_hdf(filepath, 'time', mode='w')

    except:
        
        print('Problem writing df to hdf file. Please make sure that the file is closed.')

def pickle_df(df, folderpath, filename):

    try:
        
        filepath = os.path.join( folderpath, filename)
        if( not os.path.exists(folderpath)):
            os.mkdir(folderpath) 
        
        print("Pickling to file located at: ", filepath)
        df.to_pickle(filepath)
        
    except:
        
        print('Problem pickling dataframe.')

def read_hdf_to_df(folderpath, filename):
        
    df_temp = pd.DataFrame()
    filepath = os.path.join( folderpath, filename)
    print(filepath)
    if os.path.exists( filepath ):
        df_temp = pd.read_hdf(filepath)
        df_temp = df_temp[['ask_o', 'ask_h', 'ask_l', 'ask_c', 'bid_o', 'bid_h', 'bid_l', 'bid_c', 'volume']]
    else:
        print("Filepath ({}) for reading hdf file does not exist".format(filepath))

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

