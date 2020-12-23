import datetime
import pandas as pd
import os
import tables 
import tstables  
import configparser
import strategy
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.forexlabs as labs
from oandapyV20.exceptions import V20Error
from oandapyV20.exceptions import StreamTerminated
import utility_functions as uf
import time
import feeder

config = configparser.ConfigParser()
config.read('..\..\configinfo.cfg')

# For testing:
symbol = 'EUR_USD'
granularity = 'S5'
account_type = 'live'
askbidmid = 'AB'
socket_number = 5555
daily_lookback = 10
download_frequency = datetime.timedelta(seconds=60)
update_signal_frequency = datetime.timedelta(seconds=60)
#download_data_start_date = datetime.datetime.utcnow()
download_data_start_date = pd.datetime(2020,12,22,0,0,0,0,datetime.timezone.utc)
download_data_end_date = download_data_start_date + datetime.timedelta(hours=36)

verbose = False

# -----------------------------------------------------------------------------------------------------
if 0==1:
    
    print("--- FEEDER ---")
    print("symbol:", symbol)
    print("granularity:", granularity)
    print("account_type:", account_type)
    print("socket_number:", socket_number)
    print("--------------")
    
    if account_type not in ['live', 'practice', 'backtest']:
        print('Error in account type, it should be either live, practice, or backtest')
        time.sleep(30)
        exit()
    
    f1 = feeder.feeder(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose)
    f1.start()  

if 0==1:

    # Save real-time data as excel
    
    file_path_h5 = '..\\..\\datastore\\_live\\{}\\S5.h5'.format(symbol)
    
    f = tables.open_file(file_path_h5,'r')
    ts = f.root.data._f_get_timeseries()
    
    start_time = download_data_start_date
    end_time = download_data_end_date
    
    df_realtime = ts.read_range(start_time,end_time)
    
    filename = "Realtime.xlsx"
    folderpath = '..\\..\\datastore'           
    
    uf.write_df_to_excel(df_realtime, folderpath, filename)
    
    f.close()

# -----------------------------------------------------------------------------------------------------
# Download historical data
if 0==0:
   
    start_time = datetime.datetime(2020, 12, 22, 23, 0, 0)
    end_time = datetime.datetime.utcnow()
     
    suffix = '000Z'     
    start_datetime = start_time.isoformat('T') + suffix  
    end_datetime = end_time.isoformat('T') + suffix  
    
    params = {"from": start_datetime,
              "to": end_datetime,
              "granularity": granularity,
              "price": askbidmid }
    
    config = configparser.ConfigParser()
    config.read('..\..\configinfo.cfg')
    accountID = config['oanda_v20']['account_number_{}'.format(account_type)]
    access_token = config['oanda_v20']['access_token_{}'.format(account_type)]
    api = oandapyV20.API(access_token=access_token, environment="{}".format(account_type))
               
    print("requesting...")
    r = instruments.InstrumentsCandles(instrument=symbol, params=params)
    api.request(r)
    print("received...")
    
    raw = r.response.get('candles')
    raw = [cs for cs in raw if cs['complete']]
                    
    data = pd.DataFrame()

    if len(raw) > 0:

        for cs in raw:
            cs['ask_o'] = cs['ask']['o']
            cs['ask_h'] = cs['ask']['h']
            cs['ask_l'] = cs['ask']['l']
            cs['ask_c'] = cs['ask']['c']
            cs['bid_o'] = cs['bid']['o']
            cs['bid_h'] = cs['bid']['h']
            cs['bid_l'] = cs['bid']['l']
            cs['bid_c'] = cs['bid']['c']
            del cs['ask']
            del cs['bid']
            del cs['complete']
    
        data = pd.DataFrame(raw)
                   
        data = data.set_index('time')  
        data.index = pd.DatetimeIndex(data.index)  
                
        data[['ask_c', 'ask_h', 'ask_l', 'ask_o','bid_c', 'bid_h', 'bid_l', 'bid_o']] = data[['ask_c', 'ask_h', 'ask_l', 'ask_o','bid_c', 'bid_h', 'bid_l', 'bid_o']].astype('float64')
     
        data = data[['ask_c', 'ask_h', 'ask_l', 'ask_o','bid_c', 'bid_h', 'bid_l', 'bid_o','volume']]
    
    df_historical = data.tz_localize(None)
    
    filename = "DownloadedHistorical.xlsx"
    folderpath = '..\\..\\datastore'           
    
    uf.write_df_to_excel(df_historical, folderpath, filename)
    
# -----------------------------------------------------------------------------------------------------
# Final Analysis
if 0==1:

    # Check if two dataframes are identical:
    print(df_realtime.eq(df_historical))
    
    # Tyically there will be some indices on the top/bottom that will not exiss in one dataframe.
    # Check the indices that exists in both dataframes
    idx = df_realtime.index.intersection(df_historical.index)
    df_compare = df_realtime.loc[idx,:].eq(df_historical.loc[idx,:])
    print(df_compare.describe())


                