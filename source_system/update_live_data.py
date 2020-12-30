try:
        
    import configparser
    import datetime
    import feeder
    import sys
    import tables 
    import tstables  
    import time
    import utility_functions as uf

except Exception as e:
    
    print(e) 
    
def ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose,retries):
    
    DownloadCompleted = False

    while not DownloadCompleted:
            
        f1 = feeder.feeder(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose)
    
        try:
         
            f1.connect_broker()
        
            f1.open_database()
        
            f1.download_missing_data()

            DownloadCompleted = True
            f1.h5.close()

            print('Downloading for {} completed.'.format(symbol))
            
        except Exception as e:
            
            print(e)

            AppendLogFile(f1.symbol, e)
                
            retries += 1        
            print('Trying to restart feeder:', retries)
            ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose,retries)
            
def AppendLogFile(symbol, error_message):
    
    path_logfile = '..\\..\\results_live\\log_feeder_{0}.log'.format(symbol)                
    f = open( path_logfile, 'a')
    f.write( '{}: Error: {} \n'.format(datetime.datetime.utcnow(), error_message) )
    f.close() 
    
if __name__ == '__main__':
   
    try:
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')

        list_pairs = ['AUD_USD', 'EUR_USD', 'GBP_USD', 'NZD_USD', 'USD_CAD', 'USD_CHF', 'USD_JPY', 'USD_TRY', 'AUD_NZD', 'EUR_CHF', 'AUD_JPY' ]
        #list_pairs = ['USD_CAD', 'EUR_CHF', 'AUD_JPY' ]

        account_type = 'live'
        socket_number = 5555

        daily_lookback = 10
        download_frequency = datetime.timedelta(seconds=60)
        update_signal_frequency = datetime.timedelta(seconds=60)
        download_data_start_date = datetime.datetime(2010,1,1,0,0,0,0,datetime.timezone.utc)
        download_data_end_date = None
        verbose = False

        for e_symbol in list_pairs:
        
            symbol = e_symbol
            granularity = 'S5'
                
            print("--- FEEDER ---")
            print("symbol:", symbol)
            print("granularity:", granularity)
            print("account_type:", account_type)
            print("--------------")
        
            if account_type not in ['live', 'practice', 'backtest']:
                print('Error in account type, it should be either live, practice, or backtest')
                time.sleep(30)
                exit()

            ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose,retries=0)
            
        print("--- SUMMARY ---")
        for e_symbol in list_pairs:
        
            symbol = e_symbol
            granularity = 'S5'
            
            file_path_h5 = '..\\..\\datastore\\_live\\{}\\S5.h5'.format(symbol)

            f = tables.open_file(file_path_h5,'r')
            ts = f.root.data._f_get_timeseries()
            
            read_end_dt = datetime.datetime.now()
            read_start_dt = read_end_dt - datetime.timedelta(days=30)
                
            rows = ts.read_range(read_start_dt,read_end_dt)
            
            print("{} last bar data time is {}.".format(symbol, rows.index[-1]))
        
    except Exception as e:
        
        print( 'Error in starting the object' )
        print(e)
        AppendLogFile(symbol, e)
        
        