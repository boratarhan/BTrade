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
    
    granularity = '1M'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_1M, folderpath, filename)
       
    #-------------------------------------------------------------------------------------------------------------
    df_1H = df_5S.resample('1H', closed='left', label='left').apply(ohlc_dict).dropna()
    df_1H = df_1H.reset_index()
    df_1H = df_1H.rename(columns={'index': 'date'})
    df_1H = df_1H.set_index('date')
    
    granularity = '1H'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_1H, folderpath, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_4H = df_5S.resample('4H', closed='left', label='left').apply(ohlc_dict).dropna()
    df_4H = df_4H.reset_index()
    df_4H = df_4H.rename(columns={'index': 'date'})
    df_4H = df_4H.set_index('date')
    
    granularity = '4H'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_4H, folderpath, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_8H = df_5S.resample('8H', closed='left', label='left').apply(ohlc_dict).dropna()
    df_8H = df_8H.reset_index()
    df_8H = df_8H.rename(columns={'index': 'date'})
    df_8H = df_8H.set_index('date')
    
    granularity = '8H'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_8H, folderpath, filename)

    #-------------------------------------------------------------------------------------------------------------
    df_1D = df_5S.resample('1D', closed='left', label='left').apply(ohlc_dict).dropna()
    df_1D = df_1D.reset_index()
    df_1D = df_1D.rename(columns={'index': 'date'})
    df_1D = df_1D.set_index('date')
    
    granularity = '1D'
    filename = '{}.hdf'.format(granularity)
    uf.write_df_to_hdf(df_1D, folderpath, filename)

def split_5S_data_to_years(symbol, granularity):

    account_type = 'live'
    
    for e_year in [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]:

        read_start_dt = datetime.datetime(e_year,1,1,0,0,0)
        read_end_dt = datetime.datetime(e_year+1,1,1,0,0,0)
        df_5S = uf.read_database(symbol, granularity, account_type, read_start_dt, read_end_dt)

        df_5S_year = df_5S.iloc[ ( df_5S.index >= datetime.datetime(e_year,1,1,0,0,0) ) & ( df_5S.index < datetime.datetime(e_year+1,1,1,0,0,0) ), : ]

        folderpath = os.path.join( '..\\..\\datastore', '_live', '{}'.format(symbol) )
        filename = 'S5_{}.hdf'.format(e_year)
        uf.write_df_to_hdf(df_5S_year, folderpath, filename)
    
    
if __name__ == '__main__':

    #list_pairs = ['AUD_USD', 'EUR_USD', 'GBP_USD', 'NZD_USD', 'USD_CAD', 'USD_CHF', 'USD_JPY', 'USD_TRY', 'AUD_NZD', 'EUR_CHF', 'AUD_JPY' ]
    list_pairs = ['EUR_USD']

    df_5S = pd.DataFrame()
    
    for e_symbol in list_pairs:
    
        symbol = e_symbol
        granularity = 'S5'
        #split_5S_data_to_years(symbol, granularity)
    
        read_start_dt = datetime.datetime(2010,1,1,0,0,0)
        read_end_dt = datetime.datetime(2021,1,1,0,0,0)
        create_research_data(symbol, granularity, read_start_dt, read_end_dt)
        