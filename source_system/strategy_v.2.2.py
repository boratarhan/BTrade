try:
    
    import zmq
    import os
    import sys
    import tables  
    import tstables  
    import pandas as pd
    from pandas.tseries.offsets import BDay
    import datetime
    import talib
    import numpy as np
    import time
    import utility_functions as uf
    from strategy import *
    from indicators import *

except Exception as e:
    
    print(e) 
    
class Strategy_v_2_2(strategy):
    
    def __init__(self,config,strategy_name,symbol,account_type,daily_lookback,granularity,socket_number_feeder,socket_number_portfolio):
        
        strategy.__init__(self,config,strategy_name,symbol,account_type,daily_lookback,granularity,socket_number_feeder,socket_number_portfolio)
                       
    def core_strategy(self):
        
        self.resample_data('M1')
            
        self.add_indicators()

        self.create_order_signal()
                            
        self.df_aggregate['1T']= pd.concat([self.df_aggregate['1T'], self.df_status['signal']], axis=1)
        print(self.df_aggregate['1T'].tail())
        
    def add_indicators(self):
        
        WindowLenght = 60
        self.df_aggregate['1T'].loc[:, 'mean_bid_c'] = self.df_aggregate['1T'].loc[:,  'bid_c'].rolling(WindowLenght+1).mean()
        self.df_aggregate['1T'].loc[:, 'H-L'] = self.df_aggregate['1T'].loc[:,'bid_h'] - self.df_aggregate['1T'].loc[:,'bid_l']
        self.df_aggregate['1T'].loc[:, 'cum-move'] = self.df_aggregate['1T'].loc[:,'H-L'].rolling(WindowLenght+1).sum()
        self.df_aggregate['1T'].loc[:, 'net-move'] = np.abs( self.df_aggregate['1T'].loc[:,'bid_c'] - self.df_aggregate['1T'].loc[:,'bid_c'].shift(WindowLenght))
        self.df_aggregate['1T'].loc[:, 'ratio-move'] = self.df_aggregate['1T'].loc[:, 'net-move'] / self.df_aggregate['1T'].loc[:, 'cum-move']
        self.df_aggregate['1T'] = self.df_aggregate['1T'].dropna()
                     
    def create_order_signal(self):

        try:
            
            temp_index = self.df_aggregate['1T'].index[-1]
            
            if self.net_position == 0:
        
                if ( self.df_aggregate['1T'].loc[temp_index,'net-move'] < 0.002 ) and ( self.df_aggregate['1T'].loc[temp_index, 'ratio-move'] < 0.05 ):
                               
                    if np.random.random() >= 0.5:
                    
                        self.df_status.loc[temp_index,'time'] = datetime.datetime.utcnow()
                        self.df_status.loc[temp_index,'signal'] = 1
            
                        msg = '{} {} {} {} {} {} {} {}'.format('MARKET', 'Long', self.symbol, 1000, 0 , 0, 0, 0 )
                        print("Sending message: {}".format(msg))                   
                        self.socket_pub_portfolio.send_string(msg)
                    
                    else:
                                    
                        self.df_status.loc[temp_index,'time'] = datetime.datetime.utcnow()
                        self.df_status.loc[temp_index,'signal'] = -1
        
                        msg = '{} {} {} {} {} {} {} {}'.format('MARKET', 'Short', self.symbol, 1000, 0 , 0, 0, 0 )
                        print("Sending message: {}".format(msg))                   
                        self.socket_pub_portfolio.send_string(msg)

            else:
                
                if self.unrealizedPL > 6:
                
                    self.close_position(1000)
                
                elif self.unrealizedPL <= -3:
                
                    self.close_position(1000)
                                                                                              
        except Exception as e:
            
            print(e)
            print('Something went wrong in order creation')

if __name__ == '__main__':
        
    import configparser
    
    try:
        
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')

    except:
        print( 'Error in reading configuration file' )

    try:
        
        strategy_name = "Trading Strategy v.2.2"
        
        symbol = sys.argv[1]
        granularity = sys.argv[2]
        account_type = sys.argv[3]
        socket_number_feeder = int(sys.argv[4])
        socket_number_portfolio = int(sys.argv[5])
        daily_lookback = int(sys.argv[6])

        '''
        # For testing:
        symbol = 'EUR_USD'
        granularity = 'S5'
        account_type = 'practice'
        socket_number_feeder = 5556
        socket_number_portfolio = 5552
        daily_lookback = 10
        '''
        
        print("--- STRATEGY ---")
        print("Strategy name:", strategy_name)
        print("symbol:", symbol)
        print("granularity:", granularity)
        print("account_type:", account_type)
        print("socket_number (w/ Feeder):", socket_number_feeder)
        print("socket_number (w/ Portfolio):", socket_number_portfolio)
        print("daily_lookback:", daily_lookback)
        print("--------------")

            
        # execute only if run as the entry point into the program
        s1 = Strategy_v_2_2(config,strategy_name,symbol,account_type,daily_lookback,granularity,socket_number_feeder,socket_number_portfolio)
        s1.start()
        
    except Exception as e:
        
        print( 'Error in starting strategy object' )
        
        AppendLogFile(e)
                
        time.sleep(30)
        
