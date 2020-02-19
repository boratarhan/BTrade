import datetime
import tables 
import tstables  
import os
import pandas as pd
from _utility import *

ohlc_dict = { 'ask_o':'first', 'ask_h':'max', 'ask_l':'min', 'ask_c': 'last',                                                                                                    
              'bid_o':'first', 'bid_h':'max', 'bid_l':'min', 'bid_c': 'last',
              'volume': 'sum'                                                                                                        
            }

def create_research_data(account_type, symbol, granularity, read_start_dt, read_end_dt):
    
    df_5S = read_database(account_type, symbol, granularity, read_start_dt, read_end_dt)

    filename = '{}_{}.hdf'.format(symbol, granularity)
    write_hdf_file(df_5S, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_1M = df_5S.resample('1T', closed='left', label='left').apply(ohlc_dict).dropna()
    #df_1H = df_1H[['bid_o','bid_h','bid_l','bid_c','volume']]
    df_1M = df_1M.reset_index()
    df_1M = df_1M.rename(columns={'index': 'date'})
    df_1M = df_1M.set_index('date')
    df_1M = df_1M.loc[~ ( (df_1M['bid_o'] == df_1M['bid_h']) & (df_1M['bid_o'] == df_1M['bid_l']) & (df_1M['bid_o'] == df_1M['bid_c']) ) ]

    granularity = '1M'
    filename = '{}_{}.hdf'.format(symbol, granularity)
    write_hdf_file(df_1M, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_1H = df_5S.resample('1H', closed='left', label='left').apply(ohlc_dict).dropna()
    #df_1H = df_1H[['bid_o','bid_h','bid_l','bid_c','volume']]
    df_1H = df_1H.reset_index()
    df_1H = df_1H.rename(columns={'index': 'date'})
    df_1H = df_1H.set_index('date')
    df_1H = df_1H.loc[~ ( (df_1H['bid_o'] == df_1H['bid_h']) & (df_1H['bid_o'] == df_1H['bid_l']) & (df_1H['bid_o'] == df_1H['bid_c']) ) ]

    granularity = '1H'
    filename = '{}_{}.hdf'.format(symbol, granularity)
    write_hdf_file(df_1H, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_4H = df_5S.resample('4H', closed='left', label='left').apply(ohlc_dict).dropna()
    #df_4H = df_4H[['bid_o','bid_h','bid_l','bid_c','volume']]
    df_4H = df_4H.reset_index()
    df_4H = df_4H.rename(columns={'index': 'date'})
    df_4H = df_4H.set_index('date')
    df_4H = df_4H[~ ( (df_4H['bid_o'] == df_4H['bid_h']) & (df_4H['bid_o'] == df_4H['bid_l']) & (df_4H['bid_o'] == df_4H['bid_c']) ) ]

    granularity = '4H'
    filename = '{}_{}.hdf'.format(symbol, granularity)
    write_hdf_file(df_4H, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_8H = df_5S.resample('8H', closed='left', label='left').apply(ohlc_dict).dropna()
    #df_8H = df_8H[['bid_o','bid_h','bid_l','bid_c','volume']]
    df_8H = df_8H.reset_index()
    df_8H = df_8H.rename(columns={'index': 'date'})
    df_8H = df_8H.set_index('date')
    df_8H = df_8H[~ ( (df_8H['bid_o'] == df_8H['bid_h']) & (df_8H['bid_o'] == df_8H['bid_l']) & (df_8H['bid_o'] == df_8H['bid_c']) ) ]

    granularity = '8H'
    filename = '{}_{}.hdf'.format(symbol, granularity)
    write_hdf_file(df_8H, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_1D = df_5S.resample('1D', closed='left', label='left').apply(ohlc_dict).dropna()
    #df_1D = df_1D[['bid_o','bid_h','bid_l','bid_c','volume']]
    df_1D = df_1D.reset_index()
    df_1D = df_1D.rename(columns={'index': 'date'})
    df_1D = df_1D.set_index('date')
    df_1D = df_1D[~ ( (df_1D['bid_o'] == df_1D['bid_h']) & (df_1D['bid_o'] == df_1D['bid_l']) & (df_1D['bid_o'] == df_1D['bid_c']) ) ]

    granularity = '1D'
    filename = '{}_{}.hdf'.format(symbol, granularity)
    write_hdf_file(df_1D, filename)
    
if __name__ == '__main__':

    account_type = 'live'
    symbol = 'EUR_USD'
    granularity = 'S5'
    read_start_dt = datetime.datetime(2010,1,1,0,0,0)
    read_end_dt = datetime.datetime(2020,1,1,0,0,0)
    #create_research_data(account_type, symbol, granularity, read_start_dt, read_end_dt)
    
    #df_1D['bid_c'].plot()
    #print(df_1D.tail())
    
    