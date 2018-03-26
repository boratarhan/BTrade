import datetime
import pandas as pd
import os
import tstables  
import tables 
import configparser  
import plotly as ply
from plotly import tools
import plotly.graph_objs as go

# configuration
config = configparser.ConfigParser()
config.read('..\..\configinfo.cfg')

ply.plotly.sign_in(config['plotly']['user_name'], config['plotly']['api_key'])  

ohlc_dict = { 'ask_o':'first', 'ask_h':'max', 'ask_l':'min', 'ask_c': 'last',                                                                                                    
              'bid_o':'first', 'bid_h':'max', 'bid_l':'min', 'bid_c': 'last',
              'volume': 'sum'                                                                                                        
            }

def visualize(symbol, rows, trades = []):
        
    df1 = rows.resample('1H', closed='left', label='left').apply(ohlc_dict).dropna()
    df1 = df1[['bid_o','bid_h','bid_l','bid_c','volume']]
    df1 = df1.rename(columns={'bid_o':'open','bid_h':'high','bid_l':'low','bid_c':'close'})
    df1 = df1.reset_index()
    df1 = df1.rename(columns={'index': 'date'})
    
    df2 = rows.resample('1D', closed='left', label='left').apply(ohlc_dict).dropna()
    df2 = df2[['bid_o','bid_h','bid_l','bid_c','volume']]
    df2 = df2.rename(columns={'bid_o':'open','bid_h':'high','bid_l':'low','bid_c':'close'})
    df2 = df2.reset_index()
    df2 = df2.rename(columns={'index': 'date'})
   
    trace1 = dict( type = 'candlestick', x=df1.date, yaxis='y1', open=df1['open'], high=df1['high'], low=df1['low'], close=df1['close'], name='1H', showlegend=False )
    trace2 = dict( type = 'candlestick', x=df2.date, yaxis='y2', open=df2['open'], high=df2['high'], low=df2['low'], close=df2['close'], name='1H', showlegend=False )
    
    data = [trace1, trace2]

    if len(trades) > 0:

        for eTrade in trades:

            print( eTrade.entrydate, eTrade.entryprice )
            
            for eTradeExitTransaction in eTrade.exittransactions:
        
                print( eTradeExitTransaction['date'], eTradeExitTransaction['price'] )
        
                if eTradeExitTransaction['realized P&L'] >= 0:
                
                    linecolor = 'green'
                    
                else:
                    
                    linecolor = 'red'

                traceline = dict( type = 'scatter', 
                              x = [ eTrade.entrydate, eTradeExitTransaction['date'] ],  
                              y = [ eTrade.entryprice, eTradeExitTransaction['price'] ], 
                              yaxis='y1',
                              mode = 'lines', line = dict( color = linecolor, dash = 'dot'), showlegend=False )

                data.append(traceline)
    
    layout = go.Layout(title=symbol, plot_bgcolor = 'black', paper_bgcolor = 'black', font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40),
        yaxis = dict( domain = [0.25, 1], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis2 = dict( domain = [0, 0.2], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        xaxis = dict( showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, 
            anchor = 'y2',
            rangeslider = dict(
                visible = False,
            ),
        ),
    )
   
    fig = dict(data=data, layout=layout)
    ply.offline.plot(fig, filename='..\\..\\visualizations\\visualizationssimple_ohlc.html')
