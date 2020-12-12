import datetime
import tables 
import tstables  
import os
import pandas as pd
import sys

sys.path.append('..\\source_system')
import utility_functions as uf
sys.path.remove('..\\source_system')

ohlc_dict = { 'ask_o':'first', 'ask_h':'max', 'ask_l':'min', 'ask_c': 'last',                                                                                                    
              'bid_o':'first', 'bid_h':'max', 'bid_l':'min', 'bid_c': 'last',
              'volume': 'sum'                                                                                                        
            }

def create_research_data(symbol, granularity, read_start_dt, read_end_dt):
    
    account_type = 'live'
    df_5S = uf.read_database(symbol, granularity, account_type, read_start_dt, read_end_dt)

    #-------------------------------------------------------------------------------------------------------------
    folderpath = os.path.join( '..\\..\\datastore', '_backtest', '{}'.format(symbol) )
    filename = 'S5.hdf'
    uf.write_df_to_hdf(df_5S, folderpath, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_1M = df_5S.resample('1T', closed='left', label='left').apply(ohlc_dict).dropna()
    df_1M = df_1M.reset_index()
    df_1M = df_1M.rename(columns={'index': 'date'})
    df_1M = df_1M.set_index('date')
    df_1M = df_1M.loc[~ ( (df_1M['bid_o'] == df_1M['bid_h']) & (df_1M['bid_o'] == df_1M['bid_l']) & (df_1M['bid_o'] == df_1M['bid_c']) ) ]
    
    granularity = '1M'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_1M, folderpath, filename)
    
    #-------------------------------------------------------------------------------------------------------------
    df_1H = df_5S.resample('1H', closed='left', label='left').apply(ohlc_dict).dropna()
    df_1H = df_1H.reset_index()
    df_1H = df_1H.rename(columns={'index': 'date'})
    df_1H = df_1H.set_index('date')
    df_1H = df_1H.loc[~ ( (df_1H['bid_o'] == df_1H['bid_h']) & (df_1H['bid_o'] == df_1H['bid_l']) & (df_1H['bid_o'] == df_1H['bid_c']) ) ]

    granularity = '1H'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_1H, folderpath, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_4H = df_5S.resample('4H', closed='left', label='left').apply(ohlc_dict).dropna()
    df_4H = df_4H.reset_index()
    df_4H = df_4H.rename(columns={'index': 'date'})
    df_4H = df_4H.set_index('date')
    df_4H = df_4H[~ ( (df_4H['bid_o'] == df_4H['bid_h']) & (df_4H['bid_o'] == df_4H['bid_l']) & (df_4H['bid_o'] == df_4H['bid_c']) ) ]

    granularity = '4H'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_4H, folderpath, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_8H = df_5S.resample('8H', closed='left', label='left').apply(ohlc_dict).dropna()
    df_8H = df_8H.reset_index()
    df_8H = df_8H.rename(columns={'index': 'date'})
    df_8H = df_8H.set_index('date')
    df_8H = df_8H[~ ( (df_8H['bid_o'] == df_8H['bid_h']) & (df_8H['bid_o'] == df_8H['bid_l']) & (df_8H['bid_o'] == df_8H['bid_c']) ) ]

    granularity = '8H'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_8H, folderpath, filename)


    #-------------------------------------------------------------------------------------------------------------
    df_1D = df_5S.resample('1D', closed='left', label='left').apply(ohlc_dict).dropna()
    df_1D = df_1D.reset_index()
    df_1D = df_1D.rename(columns={'index': 'date'})
    df_1D = df_1D.set_index('date')
    df_1D = df_1D[~ ( (df_1D['bid_o'] == df_1D['bid_h']) & (df_1D['bid_o'] == df_1D['bid_l']) & (df_1D['bid_o'] == df_1D['bid_c']) ) ]

    granularity = '1D'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_1D, folderpath, filename)
    
if __name__ == '__main__':

    symbol = 'EUR_USD'
    granularity = 'S5'
    read_start_dt = datetime.datetime(2020,1,1,0,0,0)
    read_end_dt = datetime.datetime(2021,1,1,0,0,0)
    create_research_data(symbol, granularity, read_start_dt, read_end_dt)
    
    
    