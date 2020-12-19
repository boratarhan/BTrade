import datetime
import pandas as pd
import os
import tables 
import tstables  
import configparser
import strategy

symbol = 'EUR_USD'

file_path_h5 = '..\\..\\datastore\\_live\\{}\\S5.h5'.format(symbol)

f = tables.open_file(file_path_h5,'r')
ts = f.root.data._f_get_timeseries()

read_start_dt = datetime.datetime(2020,1,1,00,00)
read_end_dt = datetime.datetime(2021,1,1,00,00)

rows = ts.read_range(read_start_dt,read_end_dt)

f.close()
    