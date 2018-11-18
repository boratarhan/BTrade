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
from strategy import *
from indicators import *

class SimpleStrategy(strategy):
    
    '''
    Idea is to buy and wait until there is potential positive return
    '''
    
    def __init__(self,symbol,account_type,daily_lookback,granularity,socket_number):
        
        strategy.__init__(self,symbol,account_type,daily_lookback,granularity,socket_number)
        
        self.strategy_name = "SimpleStrategy"
        
        self.start()
               
    def core_strategy(self):
        
        self.resample_data('M1')
        
        self.add_indicators()

        self.create_order_signal()
        
        result = pd.concat([self.df_aggregate['1T'], self.df_status], axis=1)
        print(result.tail)
        
    def add_indicators(self):

        pass
                     
    def create_order_signal(self):

        try:
            
            temp_index = self.df_aggregate['1T'].index[-1]
                
            '''
            self.get_positions_for_instruments()
            
            if self.position[symbol] > 0:
            ''' 
                
                
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

#    symbol = 'USD_JPY'
#    account_type = 'live'
    symbol = 'EUR_USD'
    account_type = 'practice'
    granularity = 'S5'

    daily_lookback = 10
    socket_number = 5556

    # execute only if run as the entry point into the program
    s1 = SMA_Crossover(symbol,account_type,daily_lookback,granularity,socket_number)