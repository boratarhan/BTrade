import zmq
import os
import tables  
import tstables  
import pandas as pd
from pandas.tseries.offsets import BDay
import datetime
import talib
import numpy as np
import time
import utility_functions as uf
from indicators import *
import time
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.forexlabs as labs

class strategy(object):

    def __init__(self,symbol,account_type,daily_lookback,granularity,socket_number):

        self.config = config
        self.symbol = symbol
        self.account_type = account_type
        self.daily_lookback = daily_lookback

        self.granularity = granularity
        self.file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(self.account_type,self.symbol,self.granularity)

        self.socket_sub_socket_number = socket_number
        self.context_sub = zmq.Context()
        self.socket_sub = self.context_sub.socket(zmq.SUB)
        self.socket_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket_sub.connect("tcp://127.0.0.1:{}".format(self.socket_sub_socket_number))

        self.socket_pub_forwarder_socket_number = socket_number + 1
        self.context_pub_forwarder = zmq.Context()
        self.socket_pub_forwarder = self.context_pub_forwarder.socket(zmq.PUB)
        self.socket_pub_forwarder.set_hwm(0)
        self.socket_pub_forwarder.connect("tcp://127.0.0.1:{}".format(self.socket_pub_forwarder_socket_number))

        self.socket_pub_porfolio_socket_number = 5554   # THIS NEEDS TO BE MADE DYNAMIC WHEN MULTIPLE STRATEGIES ARE RUNNING
        self.context_pub_porfolio = zmq.Context()
        self.socket_pub_porfolio = self.context_pub_porfolio.socket(zmq.PUB)
        self.socket_pub_porfolio.set_hwm(0)
        self.socket_pub_porfolio.bind("tcp://127.0.0.1:{}".format(self.socket_pub_porfolio_socket_number))

        time.sleep(5) # Since binding takes time, sleep for a few seconds before running

        self.df = pd.DataFrame()
        self.df_aggregate = {}
        self.df_status = pd.DataFrame()
        self.df_status['signal'] = 0

        self.indicatorlist = []

    def connect_broker(self):

        ''' 
        Connect to OANDA through account ID and access token based on account type.
        '''    
        
        try: 
   
            self.accountID = self.config['oanda_v20']['account_number_{}'.format(self.account_type)]
            self.access_token = self.config['oanda_v20']['access_token_{}'.format(self.account_type)]
            self.api = oandapyV20.API(access_token=self.access_token, environment="{}".format(self.account_type))
    
        except V20Error as err:
            print("V20Error occurred: {}".format(err))
                                     
    def start(self):

        print('Strategy Ready to go')
                
        while True:

            msg = self.socket_sub.recv_string()
            print("Received message: {}".format(msg))
        
            self.read_data()

            self.core_strategy()
    
            msg = 'Strategy step completed...'
            print("Sending message: {0}".format(msg))
            self.socket_pub.send_string(msg)

    def core_strategy(self):
        
        pass

    def add_indicators(self):
        
        pass

    def add_calendar_data(self):
        
        params = {"instrument": list(self.symbol), "period": 217728000 } #period seems to capture the length of future in seconds, default was 86400
        r = labs.Calendar(params=params)
        self.df_calendar = pd.DataFrame(self.api.request(r))

    def add_orderbook_data(self):
        
        r = instruments.InstrumentsOrderBook(instrument=self.symbol)
        self.df_orederbook = pd.DataFrame(self.api.request(r))

    def add_positionbook_data(self):
        
        r = instruments.InstrumentsPositionBook(instrument=self.symbol)
        self.df_positionbook = pd.DataFrame(self.api.request(r))

    def create_order_signal(self):
        ''' 
        Send order signal to Portfolio object
        '''
        pass
    
    def read_data(self):
        ''' 
        Open an existing h5 file or throw an error 
        '''
        
        try: 
    
            self.h5 = tables.open_file(self.file_path, 'r')
            self.ts = self.h5.root.data._f_get_timeseries()
            
            read_end_dt = pd.datetime.now(datetime.timezone.utc)
            read_start_dt = pd.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=self.daily_lookback)
                            
            self.df = self.ts.read_range(read_start_dt,read_end_dt)
            self.h5.close()

        except: 

            print('Database does not exist')
            print('Expected location: {}'.format(os.path.exists(self.file_path)))
            time.sleep(30)
            exit()
    
    def resample_data(self,aggregate_frequency):
        
        ohlc_dict = {   'ask_o':'first',                                                                                                    
                        'ask_h':'max',                                                                                                       
                        'ask_l':'min',                                                                                                        
                        'ask_c': 'last',                                                                                                    
                        'bid_o':'first',                                                                                                    
                        'bid_h':'max',                                                                                                       
                        'bid_l':'min',                                                                                                        
                        'bid_c': 'last',                                                                                                    
                        'volume': 'sum' }

        if aggregate_frequency == 'M1':
            freq = '1T'
        elif aggregate_frequency == 'H1':
            freq = '1H'
        elif aggregate_frequency == 'H4':
            freq = '4H'
        elif aggregate_frequency == 'D1':
            freq = '1D'
        else:
            print('aggregate_frequency not recognized')
                        
        self.df_aggregate[freq] = self.df.resample(freq, closed='left', label='left').apply(ohlc_dict).dropna()

