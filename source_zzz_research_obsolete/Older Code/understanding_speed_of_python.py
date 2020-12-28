import math
import numpy as np
import pandas as pd
from pandas_datareader import data as web
import matplotlib.pyplot as plt
#%matplotlib notebook
import datetime
import tables 
import tstables  
import os
from indicators import *

def write2excel( df, filename ):
    filepath = os.path.join('..', '..', 'datastore', filename) + '.xlsx'
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    df.to_excel(writer )
    writer.save()
    
symbol = 'EUR_USD'
account_type = 'practice'
granularity = 'S5'
start_datetime = datetime.datetime(2016,1,1,0,0,0)
end_datetime = datetime.datetime(2017,12,20,0,0,0)
decision_frequency = '1T'

file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(account_type,symbol,granularity)

h5 = tables.open_file(file_path, 'r')
ts = h5.root.data._f_get_timeseries()
raw = ts.read_range(start_datetime,end_datetime)
raw = pd.DataFrame(raw)
                
# Aggregate the high frequency data to the decision frequency
ohlc_dict = {   'ask_o':'first', 'ask_h':'max', 'ask_l':'min', 'ask_c': 'last',                                                                                                    
                'bid_o':'first', 'bid_h':'max', 'bid_l':'min', 'bid_c': 'last',                                                                                                    
                'volume': 'sum' }

df = raw.resample(decision_frequency, closed='left', label='left').apply(ohlc_dict).dropna()

indicator_list = []


df.bid_c.plot()
plt.show()

index=1
for row in df.iterrows():
    print(index)
    index=index+1