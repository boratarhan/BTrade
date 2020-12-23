import datetime
import pandas as pd
import os
import tables 
import tstables  
import configparser
import strategy
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.forexlabs as labs
from oandapyV20.exceptions import V20Error
from oandapyV20.exceptions import StreamTerminated
import utility_functions as uf

symbol = 'EUR_USD'
granularity = 'S5'
account_type = 'live'
askbidmid = 'AB'

file_path_h5 = '..\\..\\datastore\\_live\\{}\\S5.h5'.format(symbol)

f = tables.open_file(file_path_h5,'r')
ts = f.root.data._f_get_timeseries()

read_start_dt = datetime.datetime(2020,1,1,00,00)
read_end_dt = datetime.datetime(2021,1,1,00,00)

rows = ts.read_range(read_start_dt,read_end_dt)

filename = "Realtime.xlsx"
folderpath = '..\\..\\datastore'           

uf.write_df_to_excel(rows, folderpath, filename)

f.close()                