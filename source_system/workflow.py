import datetime
import pandas as pd
import os
import tables 
import tstables  
import configparser
import strategy

symbol = 'EUR_USD'

# 1) Run update_data.py: download tick data from Dukascopy and merge them to form a h5 file in datastore
# update_data.py

# 2) Check tick data downloaded

file_path_h5 = '..\\..\\datastore\\_practice\\{}\\S5.h5'.format(symbol)

f = tables.open_file(file_path_h5,'r')
ts = f.root.data._f_get_timeseries()

read_start_dt = datetime.datetime(2020,12,6,00,00)
read_end_dt = datetime.datetime(2021,1,1,00,00)

rows = ts.read_range(read_start_dt,read_end_dt)

f.close()
#
## 3) Create backtesting data
## create_testing_data.py
#
## 4) Check test data
#
#file_path_h5 = '..\\..\\datastore\\backtest_data\\{}-new.h5'.format(symbol)
#f = tables.open_file(file_path_h5,'r')
#ts = f.root.data._f_get_timeseries()
#
#read_start_dt = datetime.datetime(2017,3,1,00,00)
#read_end_dt = datetime.datetime.today()
#
#rows = ts.read_range(read_start_dt,read_end_dt)
#
#f.close()
#
## 5) Test feeder
#
#import feeder
#
#config = configparser.ConfigParser()
#config.read('..\..\configinfo.cfg')
#
#symbol_list = ['EUR_USD']
#account_type = 'backtest'
#    
#f1 = feeder.feeder(config,symbol_list,account_type)
#
## 6)  Test router
#''' Commandline: python router.py
#    Commandline: python feeder.py
#'''
#
#file_path_h5 = '..\\..\\datastore\\backtest_data\\{}-temp.h5'.format(symbol)
#f = tables.open_file(file_path_h5,'r')
#ts = f.root.data._f_get_timeseries()
#
#read_start_dt = datetime.datetime(2017,3,1,00,00)
#read_end_dt = datetime.datetime.today()
#
#rows = ts.read_range(read_start_dt,read_end_dt)
#
#f.close()
#
## 7)  Test strategy
#
#symbol = 'EUR_USD'
#account_type = 'backtest'
#daily_lookback = 240
#freq_data_update = '1H'
#freq_order = '1D'
#
## execute only if run as the entry point into the program
#s1 = strategy.SMA_Crossover(symbol,account_type,daily_lookback,freq_data_update,freq_order)
#    
    