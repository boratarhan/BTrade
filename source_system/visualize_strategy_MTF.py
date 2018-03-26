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

def visualize_1H(symbol, trades, rows):
           
    rows = rows.reset_index()
    rows = rows.rename(columns={'index': 'date'})
    
    trace1 = dict( type = 'candlestick', x=rows.date, yaxis='y1', open=rows['bid_o'], high=rows['bid_h'], low=rows['bid_l'], close=rows['bid_c'], name='1H', showlegend=False )

    trace2 = dict( type = 'scatter', x=rows.date, y=rows['slowk'], yaxis='y2', mode = 'lines', line=dict(color='red'), showlegend=False ) 
    trace3 = dict( type = 'scatter', x=rows.date, y=rows['slowd'], yaxis='y2', mode = 'lines', line=dict(color='yellow'), showlegend=False ) 
    
    trace4 = dict( type = 'bar', x=rows.date, y=rows['divergenceregularbuy'], yaxis='y3', name='regularbuy', marker=dict(color='green'), showlegend=False )    
    trace5 = dict( type = 'bar', x=rows.date, y=rows['divergencehiddenbuy'], yaxis='y4', name='hiddenbuy', marker=dict(color='green'), showlegend=False )    
    trace6 = dict( type = 'bar', x=rows.date, y=rows['divergenceregularsell'], yaxis='y5', name='regularsell', marker=dict(color='green'), showlegend=False )    
    trace7 = dict( type = 'bar', x=rows.date, y=rows['divergencehiddensell'], yaxis='y6', name='hiddensell', marker=dict(color='green'), showlegend=False )    

    trace8 = dict( type = 'bar', x=rows.date, y=rows['long_term_filter'], yaxis='y7', name='long_term_filter', marker=dict(color='green'), showlegend=False )    

    trace9 = dict( type = 'scatter', x=rows.date, y=rows['vwap_high'], yaxis='y1', mode = 'lines', line=dict(color='yellow'), showlegend=False ) 
    trace10 = dict( type = 'scatter', x=rows.date, y=rows['vwap_low'], yaxis='y1', mode = 'lines', line=dict(color='yellow'), showlegend=False ) 

    trace11 = dict( type = 'bar', x=rows.date, y=rows['macdhist'], yaxis='y8', name='MACD-Hist', marker=dict(color='green'), showlegend=False )    
    trace12 = dict( type = 'scatter', x=rows.date, y=rows['macd'], yaxis='y8', mode = 'lines', line=dict(color='yellow'), showlegend=False ) 
    trace13 = dict( type = 'scatter', x=rows.date, y=rows['macdsignal'], yaxis='y8', mode = 'lines', line=dict(color='red'), showlegend=False )

    data = [trace1, trace9, trace10,
            trace2, trace3, 
            trace11, trace12, trace13,
            trace4, trace5, trace6, trace7,
            trace8
            ]

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
    
    chart_title = symbol + '-1H'
    layout = go.Layout(title=chart_title, plot_bgcolor = 'black', paper_bgcolor = 'black', font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40),
        yaxis = dict( domain = [0.80, 1], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis2 = dict( domain = [0.65, 0.80], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis8 = dict( domain = [0.50, 0.65], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),

        yaxis3 = dict( domain = [0.40, 0.50], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis4 = dict( domain = [0.30, 0.40], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis5 = dict( domain = [0.20, 0.30], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis6 = dict( domain = [0.10, 0.20], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),

        yaxis7 = dict( domain = [0.00, 0.10], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),

        xaxis = dict( showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, 
            anchor = 'y7',
            rangeslider = dict(
                visible = False,
            ),
        ),
    )
   
    fig = dict(data=data, layout=layout)
    ply.offline.plot(fig, filename='ohlc_1H.html')


def visualize_4H(symbol, trades, rows):
           
    rows = rows.reset_index()
    rows = rows.rename(columns={'index': 'date'})

    trace1 = dict( type = 'candlestick', x=rows.date, yaxis='y1', open=rows['bid_o'], high=rows['bid_h'], low=rows['bid_l'], close=rows['bid_c'], name='4H', showlegend=False )

    trace2 = dict( type = 'scatter', x=rows.date, y=rows['waveclose'], yaxis='y1', mode = 'lines', line=dict(color='purple'), showlegend=False )
    trace3 = dict( type = 'scatter', x=rows.date, y=rows['wavehigh'], yaxis='y1', mode = 'lines', line=dict(color='purple'), showlegend=False )
    trace4 = dict( type = 'scatter', x=rows.date, y=rows['wavelow'], yaxis='y1', mode = 'lines', line=dict(color='purple'), showlegend=False )

    trace5 = dict( type = 'scatter', x=rows.date, y=rows['atr+1'], yaxis='y1', mode = 'lines', line=dict(color='yellow', width=.5), showlegend=False )
    trace6 = dict( type = 'scatter', x=rows.date, y=rows['atr+2'], yaxis='y1', mode = 'lines', line=dict(color='yellow', width=.5), showlegend=False )
    trace7 = dict( type = 'scatter', x=rows.date, y=rows['atr+3'], yaxis='y1', mode = 'lines', line=dict(color='yellow', width=.5), showlegend=False )
    trace8 = dict( type = 'scatter', x=rows.date, y=rows['atr-1'], yaxis='y1', mode = 'lines', line=dict(color='yellow', width=.5), showlegend=False )
    trace9 = dict( type = 'scatter', x=rows.date, y=rows['atr-2'], yaxis='y1', mode = 'lines', line=dict(color='yellow', width=.5), showlegend=False )
    trace10 = dict( type = 'scatter', x=rows.date, y=rows['atr-3'], yaxis='y1', mode = 'lines', line=dict(color='yellow', width=.5), showlegend=False )

    trace11 = dict( type = 'bar', x=rows.date, y=rows['macdhist'], yaxis='y2', name='MACD-Hist', marker=dict(color='green'), showlegend=False )    
    trace12 = dict( type = 'scatter', x=rows.date, y=rows['macd'], yaxis='y2', mode = 'lines', line=dict(color='yellow'), showlegend=False ) 
    trace13 = dict( type = 'scatter', x=rows.date, y=rows['macdsignal'], yaxis='y2', mode = 'lines', line=dict(color='red'), showlegend=False )

    trace14 = dict( type = 'bar', x=rows.date, y=rows['long_term_filter'], yaxis='y3', name='long_term_filter', marker=dict(color='green'), showlegend=False )    
    
    data = [trace1, 
            trace2, trace3, trace4, 
            trace5, trace6, trace7, trace8, trace9, trace10,
            trace11, trace12, trace13, 
            trace14
            ]

    chart_title = symbol + '-4H'
    layout = go.Layout(title=chart_title, plot_bgcolor = 'black', paper_bgcolor = 'black', font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40),
        yaxis = dict( domain = [0.40, 1], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis2 = dict( domain = [0.20, 0.40], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),
        yaxis3 = dict( domain = [0.00, 0.20], showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, ),

        xaxis = dict( showgrid=True, mirror='ticks', gridcolor='grey', gridwidth=0.5, 
            anchor = 'y3',
            rangeslider = dict(
                visible = False,
            ),
        ),
    )
   
    fig = dict(data=data, layout=layout)
    ply.offline.plot(fig, filename='..\\..\\visualizations\\ohlc_4H.html')
   

