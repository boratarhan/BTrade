try:
    
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
    import oandapyV20
    import oandapyV20.endpoints.instruments as instruments
    import oandapyV20.endpoints.pricing as pricing
    import oandapyV20.endpoints.accounts as accounts
    import oandapyV20.endpoints.orders as orders
    from oandapyV20.exceptions import V20Error
    
except Exception as e:
    
    print(e) 
    
class strategy(object):

    '''
    This is the base class for various strategies to be customized in the future
    It receives data from forwarder/feeder and sends signals to portfolio object
    '''
    def __init__(self,config,strategy_name,symbol,account_type,daily_lookback,granularity,socket_number_feeder,socket_number_portfolio):
           
        self.config = config
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.account_type = account_type
        self.daily_lookback = daily_lookback
        self.granularity = granularity
        self.net_position = 0.0
        self.unrealizedPL = 0.0
        self.path_input_data = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(self.account_type,self.symbol,self.granularity)
        self.path_results_live = '..\\..\\results_live'
        self.path_timestamp = datetime.datetime.utcnow()
        
        '''
        This is the socket subscribing to Forwarder/Feeder on socket 5556
        It received the signal that the data is ready
        '''
        self.socket_sub_socket_number_feeder = socket_number_feeder
        self.context_sub_feeder = zmq.Context()
        self.socket_sub_feeder = self.context_sub_feeder.socket(zmq.SUB)
        self.socket_sub_feeder.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket_sub_feeder.connect("tcp://127.0.0.1:{}".format(self.socket_sub_socket_number_feeder))

        '''
        This is the socket publishing back to Forwarder/Feeder on socket 5557
        It received the signal that the data is ready
        '''
        self.socket_pub_socket_number_feeder = socket_number_feeder + 1
        self.context_pub_feeder = zmq.Context()
        self.socket_pub_feeder = self.context_pub_feeder.socket(zmq.PUB)
        self.socket_pub_feeder.set_hwm(0)
        self.socket_pub_feeder.connect("tcp://127.0.0.1:{}".format(self.socket_pub_socket_number_feeder))
    
        '''
        This is the socket subscribing to Forwarder/Portfolio on socket 5552
        It received the signal that the response from broker is okay.
        Strategy then can use this data to decide on the next buy/sell signal.
        '''
        self.socket_sub_socket_number_portfolio = socket_number_portfolio
        self.context_sub_portfolio = zmq.Context()
        self.socket_sub_portfolio = self.context_sub_portfolio.socket(zmq.SUB)
        self.socket_sub_portfolio.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket_sub_portfolio.connect("tcp://127.0.0.1:{}".format(self.socket_sub_socket_number_portfolio))

        '''
        This is the socket publishing to Forwarder/Portfolio on socket 5553
        Note that multiple strategies can use the same socket to send messages to Portfolio.
        '''
        self.socket_pub_socket_number_portfolio = socket_number_portfolio + 1
        self.context_pub_portfolio = zmq.Context()
        self.socket_pub_portfolio = self.context_pub_portfolio.socket(zmq.PUB)
        self.socket_pub_portfolio.set_hwm(0)
        self.socket_pub_portfolio.connect("tcp://127.0.0.1:{}".format(self.socket_pub_socket_number_portfolio))
        
        time.sleep(5) # Since binding takes time, sleep for a few seconds before running

        self.df = pd.DataFrame()
        self.df_aggregate = {}
        self.df_status = pd.DataFrame(columns=['time','signal'])

        self.indicatorlist = []
        
        self.connect_broker()
        
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
            msg = self.socket_sub_feeder.recv_string()
            print("Received message: {}".format(msg))

            self.read_data()

            self.get_position_for_instrument()
            
            self.core_strategy()

            '''
            Send message back to forwarder/feeder, so that feeder 
            can open the database and appended new data
            '''
            msg = 'Strategy step completed...'
            print("Sending message: {0}".format(msg))
            self.socket_pub_feeder.send_string(msg)
        
            self.update_results_log()

    def update_results_log(self):
                
        filename = '{0}_{1}-{2:02d}-{3:02d}-{4:02d}-{5:02d}-{6:02d}_data.xlsx'.format(self.symbol, self.path_timestamp.year, self.path_timestamp.month, self.path_timestamp.day, self.path_timestamp.hour, self.path_timestamp.minute, self.path_timestamp.second)
        uf.write_df_to_excel(self.df_aggregate['1T'], self.path_results_live, filename)
                
        filename = '{0}_{1}-{2:02d}-{3:02d}-{4:02d}-{5:02d}-{6:02d}_data.pkl'.format(self.symbol, self.path_timestamp.year, self.path_timestamp.month, self.path_timestamp.day, self.path_timestamp.hour, self.path_timestamp.minute, self.path_timestamp.second)
        uf.pickle_df(self.df_aggregate['1T'], self.path_results_live, filename)
       
    def close_position(self, units):

        if self.net_position > 0:
        
            msg = '{} {} {} {} {} {} {} {}'.format('MARKET', 'Short', self.symbol, units, 0 , 0, 0, 0 )
            print("Sending message: {}".format(msg))                   
            self.socket_pub_portfolio.send_string(msg)
        
        else:
        
            msg = '{} {} {} {} {} {} {} {}'.format('MARKET', 'Long', self.symbol, units, 0 , 0, 0, 0 )
            print("Sending message: {}".format(msg))                   
            self.socket_pub_portfolio.send_string(msg)
        
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
            
            self.h5 = tables.open_file(self.path_input_data, 'r')
            self.ts = self.h5.root.data._f_get_timeseries()
            
            read_end_dt = pd.datetime.now(datetime.timezone.utc)
            read_start_dt = pd.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=self.daily_lookback)

            self.df = self.ts.read_range(read_start_dt,read_end_dt)
            self.h5.close()

        except: 

            print('Database does not exist')
            print('Expected location: {}'.format(os.path.exists(self.path_input_data)))
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

    def get_position_for_instrument(self):

        r = accounts.AccountDetails(accountID=self.accountID)
        df = pd.DataFrame(self.api.request(r))
                
        print("--------------------------------------")
        print('Net Positions:') 

        for e_position in df['account']['positions']:

            if e_position['instrument'] == self.symbol:                         
            
                self.net_position = int(e_position['long']['units'])+int(e_position['short']['units'])
                self.unrealizedPL = e_position['unrealizedPL']
                print('Net position: {}'.format(self.net_position), "P&L: {}".format(self.unrealizedPL))

                
        print("--------------------------------------")
        
def AppendLogFile(error_message):
    
    path_logfile = '..\\..\\results_live\\log_strategy.log'
    f = open( path_logfile, 'a')
    f.write( '{}: Error: {} \n'.format(datetime.datetime.utcnow(), error_message) )
    f.close() 
       