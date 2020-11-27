
import datetime
import pandas as pd
import os
import tstables  
import tables 
import utility_functions as uf
import time

# Reading ts file
account_type = 'live'
symbol = 'EUR_USD'
granularity = 'S5'
file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(account_type,symbol,granularity)

f = tables.open_file(file_path,'r')
ts = f.root.data._f_get_timeseries()

read_start_dt = datetime.datetime(2020,1,1,0,0,0)
read_end_dt = datetime.datetime.utcnow()

rows = ts.read_range(read_start_dt,read_end_dt)

f.close()

print(rows.tail)
