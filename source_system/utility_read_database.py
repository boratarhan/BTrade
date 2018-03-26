
import datetime
import pandas as pd
import os
import tstables  
import tables 
import utility_functions as uf
import time

# Reading ts file
#symbol = 'USD_JPY'
#file_path_h5 = '..\\..\\datastore\\S5_data\\USD_JPY.h5'
#file_path_h5 = '..\\..\\datastore\\M1_data\\EUR_USD.h5'
file_path_h5 = '..\\..\\datastore\\_practice\\USD_TRY\\S5.h5'

f = tables.open_file(file_path_h5,'r')
ts = f.root.data._f_get_timeseries()

read_start_dt = datetime.datetime(2017,1,1,00,00)
read_end_dt = datetime.datetime(2017,9,1,00,00)

rows = ts.read_range(read_start_dt,read_end_dt)

f.close()

print(rows.tail)
#
#ohlc_dict = {                                                                                                             
#    'ask_o':'first',                                                                                                    
#    'ask_h':'max',                                                                                                       
#    'ask_l':'min',                                                                                                        
#    'ask_c': 'last',                                                                                                    
#    'bid_o':'first',                                                                                                    
#    'bid_h':'max',                                                                                                       
#    'bid_l':'min',                                                                                                        
#    'bid_c': 'last',                                                                                                    
#    'volume': 'sum'                                                                                                        
#}
#
#data_rows_aggregate = rows.resample('1H', closed='left', label='left').apply(ohlc_dict).dropna()
#print(data_rows_aggregate.tail)
        
        

#count_dict = {                                                                                                             
#    'ask_o':'count',                                                                                                    
#}
#
#rows2 = rows.resample('1H', closed='left', label='left').apply(count_dict)

#uf.write2excel(rows, 'rows')
#uf.write2excel(rows2, 'rows2')



#
## Creating a file for testing strategy object
#symbol = 'EURUSD'
#file_path_h5 = '..\\..\\datastore\\{}.h5'.format(symbol)
#f = tables.open_file(file_path_h5,'r')
#ts = f.root.data._f_get_timeseries()
#read_start_dt = datetime.datetime(2016,1,1,00,00)
#read_end_dt = datetime.datetime(2016,2,1,00,00)
#rows = ts.read_range(read_start_dt,read_end_dt)
#
#class desc(tables.IsDescription):
#    ''' Description of TsTables table structure.
#    '''
#    timestamp = tables.Int64Col(pos=0)  
#    ask = tables.Float64Col(pos=1)  
#    ask_volume = tables.Float64Col(pos=2)
#    bid = tables.Float64Col(pos=3)
#    bid_volume = tables.Float64Col(pos=4)
#    
#h5 = tables.open_file('..\\..\\datastore\\xxx.h5', 'w')
#ts = h5.create_ts('/', 'data', desc)
#ts.append(rows)
#h5.close()
#
#rows.to_hdf('..\\..\\datastore\\ut_strategy.h5','a', mode='w')
#
#
#mcs = pd.read_hdf('..\\..\\datastore\\ut_strategy.h5')
