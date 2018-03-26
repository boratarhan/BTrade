import datetime
import pandas as pd
import os
import tstables  
import tables 
import cufflinks as cf
import configparser  
import plotly.plotly as ply

# configuration
config = configparser.ConfigParser()
config.read('..\..\configinfo.cfg')

ply.sign_in(config['plotly']['user_name'], config['plotly']['api_key'])  

file_path_h5 = '..\\..\\datastore\\_practice\\USD_TRY\\S5.h5'

f = tables.open_file(file_path_h5,'r')
ts = f.root.data._f_get_timeseries()

read_start_dt = datetime.datetime(2017,1,1,00,00)
read_end_dt = datetime.datetime(2017,8,1,00,00)

rows = ts.read_range(read_start_dt,read_end_dt)

f.close()

ohlc_dict = {                                                                                                             
    'ask_o':'first',                                                                                                    
    'ask_h':'max',                                                                                                       
    'ask_l':'min',                                                                                                        
    'ask_c': 'last',                                                                                                    
    'bid_o':'first',                                                                                                    
    'bid_h':'max',                                                                                                       
    'bid_l':'min',                                                                                                        
    'bid_c': 'last',                                                                                                    
    'volume': 'sum'                                                                                                        
}

df = rows.resample('1H', closed='left', label='left').apply(ohlc_dict).dropna()

df = df[['bid_o','bid_h','bid_l','bid_c','volume']]

df = df.rename(columns={'bid_o':'open','bid_h':'high','bid_l':'low','bid_c':'close'})

qf = cf.QuantFig(df, title= 'USD_TRY')
rangeselector = dict(steps=[ 'Reset', '3M' ], bgcolor=('rgb(150,200,250)',.1),fontsize=12,fontfamily='monospace')
qf.layout.update(rangeselector=rangeselector)
qf.iplot()

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return '<iframe src="https://plot.ly/create/?fid=btarhan7%3A10" width="750px" height="550px"></iframe>'


if __name__ == '__main__':
    app.run(port=5555, debug=True)
    