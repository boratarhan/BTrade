
import datetime
import pandas as pd
import os
import tstables  
import tables 
import utility_functions as uf
import time

class desc(tables.IsDescription):
    ''' Description of TsTables table structure.
    '''
    timestamp = tables.Int64Col(pos=0)  
    ask_c = tables.Float64Col(pos=1)  
    ask_h = tables.Float64Col(pos=2)  
    ask_l = tables.Float64Col(pos=3)  
    ask_o = tables.Float64Col(pos=4)  

    bid_c = tables.Float64Col(pos=5)  
    bid_h = tables.Float64Col(pos=6)  
    bid_l = tables.Float64Col(pos=7)  
    bid_o = tables.Float64Col(pos=8)  

    volume = tables.Int64Col(pos=9)

symbol = 'USD_TRY'
account_type = 'practice'
granularity = 'S5'
        
file_path_1 = '..\\..\\datastore\\_practice\\USD_TRY\\S5_2016.h5'

f = tables.open_file(file_path_1,'r')
ts = f.root.data._f_get_timeseries()
read_start_dt = datetime.datetime(2016,1,1,00,00)
read_end_dt = datetime.datetime.utcnow()

rows1 = ts.read_range(read_start_dt,read_end_dt)

f.close()

file_path_2 = '..\\..\\datastore\\_practice\\USD_TRY\\S5_2017.h5'

f = tables.open_file(file_path_2,'r')
ts = f.root.data._f_get_timeseries()
read_start_dt = datetime.datetime(2017,1,1,00,00)
read_end_dt = datetime.datetime.utcnow()

rows2 = ts.read_range(read_start_dt,read_end_dt)

f.close()

rows = rows1.append(rows2)

file_path = '..\\..\\datastore\\_practice\\USD_TRY\\S5.h5'

f = tables.open_file(file_path, 'w')
ts = f.create_ts('/', 'data', desc)
ts.append(rows)
f.close()


