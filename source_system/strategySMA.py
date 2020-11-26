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

class SMA_Crossover(strategy):
    
    def __init__(self,symbol,account_type,daily_lookback,granularity,socket_number):
        
        strategy.__init__(self,symbol,account_type,daily_lookback,granularity,socket_number)
        
        self.strategy_name = "SMA_Crossover"
        
        self.start()

    def start(self):
        print('Strategy Ready to go')
                
        while True:

            msg = self.socket_sub.recv_string()
            print("Strategy Received message: {}".format(msg))
        
            self.read_data()

            self.core_strategy()
    
            msg = 'Resampler completed...'
            print("Sending message: {0}".format(msg))
            self.socket_pub.send_string(msg)
                
    def core_strategy(self):
        
        self.resample_data('M1')
        
        self.add_indicators()

        self.create_order_signal()
        
        result = pd.concat([self.df_aggregate['1T'], self.df_status], axis=1)
        print(result.tail)
        
        
    def add_indicators(self):

        self.df_aggregate['1T'], self.indicatorlist = AddSMA( self.df_aggregate['1T'], self.indicatorlist, 'bid', 'c', 5)
        self.df_aggregate['1T'], self.indicatorlist = AddSMA( self.df_aggregate['1T'], self.indicatorlist, 'bid', 'c', 3)
        self.df_aggregate['1T'] = self.df_aggregate['1T'].dropna()
                     
    def create_order_signal(self):

        try:
            
            temp_index = self.df_aggregate['1T'].index[-1]
                       
            if self.df_aggregate['1T']['SMA_5_bid_c'][-1] > self.df_aggregate['1T']['SMA_3_bid_c'][-1]:
    
                print('Short')
                self.df_status.loc[temp_index,'signal'] = -1
               
                msg = 'Short {}'.format(self.symbol)
                print("Sending message: {0}".format(msg))                   
                self.socket_pub_porfolio.send_string(msg)
                            
            elif self.df_aggregate['1T']['SMA_5_bid_c'][-1] < self.df_aggregate['1T']['SMA_3_bid_c'][-1]:
    
                print('Long')
                self.df_status.loc[temp_index,'signal'] = 1
    
                msg = 'Long {}'.format(self.symbol)
                print("Sending message: {0}".format(msg))                   
                self.socket_pub_porfolio.send_string(msg)
                        
            else:
                
                pass
                
            print( self.df_status )
            
            uf.write2excel( self.df_status, 'orders_{}'.format(self.symbol) )
                    
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

    symbol = sys.argv[1]
    granularity = sys.argv[2]
    account_type = sys.argv[3]
    socket_number = int(sys.argv[4])
    daily_lookback = int(sys.argv[5])
    download_frequency = datetime.timedelta(seconds=60)
    update_signal_frequency = datetime.timedelta(seconds=60)

    print("symbol:", symbol)
    print("granularity:", granularity)
    print("account_type:", account_type)
    print("socket_number:", socket_number)
    print("daily_lookback:", daily_lookback)
        
    # execute only if run as the entry point into the program
    s1 = SMA_Crossover(symbol,account_type,daily_lookback,granularity,socket_number)