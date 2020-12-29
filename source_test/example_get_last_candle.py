import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.forexlabs as labs
from oandapyV20.exceptions import V20Error
from oandapyV20.exceptions import StreamTerminated
from requests.exceptions import ConnectionError
import oandapyV20.endpoints.accounts as accounts

import zmq
import pandas as pd
import tables 
import tstables 
import json
import configparser
import datetime
import time
import utility_functions as uf
import threading
import os
import sys

'''
The code should be updated based on deprecation warnings. However, it may require extensive work.
I will keep it in this version as long as it works.
Turn off warnings for keeping the screen cleaner.
'''
import warnings
warnings.filterwarnings("ignore", category=Warning) 

'''
import logging
logging.basicConfig(
    filename="v20.log",
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s : %(message)s',
)
'''

isAlive = True

class desc(tables.IsDescription):
    ''' 
    Description of TsTables table structure.
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

class feeder(object):
    ''' 
    Feeder receives data from broker and publishes messages for the rest of the objects in the system
    Ideally, feeder only deals with tick data and the rest of the objects handle resampling. However,
    OANDA streams only a portion of the entire tick data therefore feeder is designed to collect 5S data. 
    Also, since my strategies are not suitable for tick data, so it does not lose any advantage by using S5 data.
    Tick data may be collected only for future analysis or visual purposes.
    '''

    def __init__(self,config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date):

        self.config = config
        self.symbol = symbol
        self.granularity = granularity
        self.account_type = account_type
        self.download_frequency = download_frequency
        self.update_signal_frequency = update_signal_frequency
        self.download_data_start_date = download_data_start_date
        self.askbidmid = 'AB'
         
    def connect_broker(self):

        print("Connecting to broker...")
        try: 
   
            self.accountID = self.config['oanda_v20']['account_number_{}'.format(self.account_type)]
            self.access_token = self.config['oanda_v20']['access_token_{}'.format(self.account_type)]
            self.api = oandapyV20.API(access_token=self.access_token, environment="{}".format(self.account_type))
            print("Connection successful")
    
        except V20Error as err:
            print("V20Error occurred: {}".format(err))
             

    def get_last_candle(self):
        
        try:
            
            params = {"count": 1,
                      "granularity": "S5"}
            self.r = instruments.InstrumentsCandles(self.symbol, params)
            self.api.request(self.r)
            
            if self.r.response.get('candles')[0]['complete'] == True:
                print("candles is complete")
                print(self.r.response.get('candles')[0]['time'])
                
                print(self.r.response)
            
            #RAW = r.response.get('candles')
            

        except:
            
            print("Error in getting candle...")
        
if __name__ == '__main__':
   
    try:
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')
        
        # For testing:
        symbol = 'EUR_USD'
        granularity = 'S5'
        account_type = 'live'
        socket_number = 5555
        daily_lookback = 10
        download_frequency = datetime.timedelta(seconds=60)
        update_signal_frequency = datetime.timedelta(seconds=60)
        download_data_start_date = pd.datetime(2010,1,1,0,0,0,0,datetime.timezone.utc)
       
        print("--- FEEDER ---")
        print("symbol:", symbol)
        print("granularity:", granularity)
        print("account_type:", account_type)
        print("socket_number:", socket_number)
        print("--------------")

        f1 = feeder(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date)
        
        f1.connect_broker()
        
        f1.get_last_candle()


        '''
                params = {"from": start_datetime,
                  "to": end_datetime,
                  "granularity": granularity,
                  "price": askbidmid }
        
        r = instruments.InstrumentsCandles(instrument=self.symbol, params=params)
        self.api.request(r)
        
        raw = r.response.get('candles')
        raw = [cs for cs in raw if cs['complete']]
        '''


    except:
        
        print( 'Error in reading configuration file' )
        

        
    