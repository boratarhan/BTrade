
import configparser

try:
    config = configparser.ConfigParser()
    config.read('..\..\configinfo.cfg')
    print( config['plotly']['username'] )
    print( config['plotly']['api_key'] )
    username = config['plotly']['username']
    api_key = config['plotly']['api_key']
                     
except:
    print( 'Error in reading configuration file' )


import plotly.plotly as py
import plotly.graph_objs as go

py.sign_in(username, api_key)

import pandas_datareader.data as web
from datetime import datetime

df = web.DataReader("aapl", 'yahoo', datetime(2007, 10, 1), datetime(2009, 4, 1))

trace = go.Ohlc(x=df.index,
                open=df.Open,
                high=df.High,
                low=df.Low,
                close=df.Close)
data = [trace]

# Plotting offline
py.plot(data, filename='simple_ohlc')

# Plotting online
#py.iplot(data, filename='simple_ohlc')