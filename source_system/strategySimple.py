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
                       
    def core_strategy(self):
        
        self.resample_data('M1')

        self.create_order_signal()
        
        result = pd.concat([self.df_aggregate['1T'], self.df_status], axis=1)
        print(result.tail)
                            
    def create_order_signal(self):

        try:
            
            temp_index = self.df_aggregate['1T'].index[-1]

            if self.df_aggregate['1T']['SMA_5_bid_c'][-1] > self.df_aggregate['1T']['SMA_3_bid_c'][-1]:
    
                self.df_status.loc[temp_index,'signal'] = -1
               
                #order_type, longshort, symbol, units, priceBound, limit_price, takeProfitOnFill, stopLossOnFill
                msg = '{} {} {} {} {} {} {} {}'.format('MARKET', 'Short', self.symbol, 1000, 0 , 0, 0, 0 )
                print("Sending message: {}".format(msg))                   
                self.socket_pub_porfolio.send_string(msg)
                            
            elif self.df_aggregate['1T']['SMA_5_bid_c'][-1] < self.df_aggregate['1T']['SMA_3_bid_c'][-1]:
    
                self.df_status.loc[temp_index,'signal'] = 1
    
                #order_type, longshort, symbol, units, priceBound, limit_price, takeProfitOnFill, stopLossOnFill
                msg = '{} {} {} {} {} {} {} {}'.format('MARKET', 'Long', self.symbol, 1000, 0 , 0, 0, 0 )
                print("Sending message: {}".format(msg))                   
                self.socket_pub_porfolio.send_string(msg)
                        
            else:
                
                pass
                
            print( self.df_status.tail() )
            
            self.file_path = '..\\..\\datastore_results\\orders_{}.xlsx'.format(self.symbol)
            uf.write2excel( self.df_status, self.file_path )

                    
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
        
        symbol = sys.argv[1]
        granularity = sys.argv[2]
        account_type = sys.argv[3]
        socket_number = int(sys.argv[4])
        daily_lookback = int(sys.argv[5])
    
        print("--- STRATEGY ---")
        print("symbol:", symbol)
        print("granularity:", granularity)
        print("account_type:", account_type)
        print("socket_number:", socket_number)
        print("daily_lookback:", daily_lookback)
        print("--------------")
            
        # execute only if run as the entry point into the program
        s1 = SimpleStrategy(symbol,account_type,daily_lookback,granularity,socket_number)
        s1.start()
        
    except:
        print( 'Error in starting strategy object' )
        time.sleep(30)
        exit()



