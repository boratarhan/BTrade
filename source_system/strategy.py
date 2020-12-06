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

class strategy(object):

    '''
    This is the base class for various strategies to be customized in the future
    It receives data from forwarder/feeder and sends signals to portfolio object
    '''
    def __init__(self,config,strategy_name,symbol,account_type,daily_lookback,granularity,socket_number):
           
        self.config = config
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.account_type = account_type
        self.daily_lookback = daily_lookback
        self.granularity = granularity
        self.file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(self.account_type,self.symbol,self.granularity)
    
        '''
        This is the socket subscribing to Forwarder/Feeder on socket 5556
        It received the signal that the data is ready
        '''
        self.socket_sub_socket_number = socket_number
        self.context_sub_forwarder = zmq.Context()
        self.socket_sub_forwarder = self.context_sub_forwarder.socket(zmq.SUB)
        self.socket_sub_forwarder.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket_sub_forwarder.connect("tcp://127.0.0.1:{}".format(self.socket_sub_socket_number))

        '''
        This is the socket publishing back to Forwarder/Feeder on socket 5557
        It received the signal that the data is ready
        '''
        self.socket_pub_forwarder_socket_number = socket_number + 1
        self.context_pub_forwarder = zmq.Context()
        self.socket_pub_forwarder = self.context_pub_forwarder.socket(zmq.PUB)
        self.socket_pub_forwarder.set_hwm(0)
        self.socket_pub_forwarder.connect("tcp://127.0.0.1:{}".format(self.socket_pub_forwarder_socket_number))

        '''
        This is the socket publishing to Portfolio object on socket 5554
        Note that multiple strategies can use the same socket to send messages to Portfolio.
        '''
        self.socket_pub_porfolio_socket_number = 5554
        self.context_pub_porfolio = zmq.Context()
        self.socket_pub_porfolio = self.context_pub_porfolio.socket(zmq.PUB)
        self.socket_pub_porfolio.connect("tcp://127.0.0.1:{}".format(self.socket_pub_porfolio_socket_number))

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

            '''
            Receive message from forwarder/feeder
            '''
            msg = self.socket_sub_forwarder.recv_string()
            print("Received message: {}".format(msg))

            self.read_data()
            
            self.core_strategy()

            '''
            Send message back to forwarder/feeder, so that feeder 
            can open the database and appended new data
            '''
            msg = 'Strategy step completed...'
            print("Sending message: {0}".format(msg))
            self.socket_pub_forwarder.send_string(msg)
 
    def core_strategy(self):
        
        pass

    def add_indicators(self):
        
        pass

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
        '''
        Since the feeder receives and stores S5 data, strategy can resample with needed granularity.
        '''

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

    def read_calendar_data(self):
        
        path = '..\\..\\datastore\\_{0}\\{1}\\calendar.pkl'.format(self.account_type,self.symbol)
        self.df_calendar = pd.read_pickle(path)
      
    def read_orderbook_data(self):
        
        path = '..\\..\\datastore\\_{0}\\{1}\\orderbook.pkl'.format(self.account_type,self.symbol)
        self.df_orderbook = pd.read_pickle(path)
        
    def read_positionbook_data(self):
        
        path = '..\\..\\datastore\\_{0}\\{1}\\positionbook.pkl'.format(self.account_type,self.symbol)
        self.df_positionbook = pd.read_pickle(path)