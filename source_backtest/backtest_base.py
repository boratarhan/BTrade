import sys
from sys import exit
import os
import math
import numpy as np
import pandas as pd
from pandas_datareader import data as web
import matplotlib.pyplot as plt
import datetime
import tables 
import tstables  
plt.style.use('seaborn')

sys.path.append('..\\source_system')
from indicators import *
from visualizer import *
from utility_functions import *
sys.path.remove('..\\source_system')

 # A standard lot = 100,000 units of base currency. 
 # A mini lot = 10,000 units of base currency.
 # A micro lot = 1,000 units of base currency.

class Trade(object):
    
    def __init__(self, symbol, units, entrydate, entrypricebid, entrypriceask, marginrate ):
        self.symbol = symbol
        self.units = units #number of units of base currency
        self.longshort = 'long' if self.units > 0 else 'short'
        self.entrydate = entrydate
        self.entryprice = entrypriceask if self.units > 0 else entrypricebid
        self.marginrate = marginrate
        self.exittransactions = [] 
        self.IsOpen = True
        self.unrealizedprofitloss = 0.0
        self.realizedprofitloss = 0.0
        self.highwatermark = 0.0
        self.maxdrawndown = 0.0
#        self.update( entrypricebid, entrypriceask )
    
    def update(self, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l ):
        price_c = price_bid_c if self.units > 0 else price_ask_c      
        price_h = price_bid_h if self.units > 0 else price_ask_h      
        price_l = price_bid_l if self.units > 0 else price_ask_l      
        
        self.unrealizedprofitloss = self.units * ( price_c - self.entryprice )
        self.required_margin = ( self.entryprice * abs(self.units) - self.unrealizedprofitloss ) * self.marginrate

        temphighwatermark = 0.0
        tempmaxdrawndown = 0.0

        if self.units > 0:
            temphighwatermark = self.units * ( price_h - self.entryprice )
            tempmaxdrawndown = self.units * ( price_l - self.entryprice )
        if self.units < 0:
            temphighwatermark = self.units * ( price_l - self.entryprice )
            tempmaxdrawndown = self.units * ( price_h - self.entryprice )

        if temphighwatermark > self.highwatermark:
            self.highwatermark = temphighwatermark
        if tempmaxdrawndown < self.maxdrawndown:
            self.maxdrawndown = tempmaxdrawndown
                               
        print('units:', self.units, 'p/l:', self.unrealizedprofitloss, 'highwatermark:', self.highwatermark, 'maxdrawndown:', self.maxdrawndown)
        
                
    def close(self, units, exitdate, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l ):
        exitprice = price_bid_c if self.units > 0 else price_ask_c
        # ask price > bid pricez
        # if i am selling, i get bid price
        # if i am buying, i get ask price
        
        if abs(self.units) > abs(units):

            self.realizedprofitloss = self.realizedprofitloss - units * ( exitprice - self.entryprice )            
            self.transaction = { 'date' : exitdate, 'units' : units, 'price' : exitprice, 'realized P&L': self.realizedprofitloss }
            self.exittransactions.append(self.transaction)
            self.units = self.units - units
            unclosedunits = 0
            self.IsOpen = True
        
        elif abs(self.units) == abs(units):
            
            self.realizedprofitloss = self.realizedprofitloss - units * ( exitprice - self.entryprice )            
            self.transaction = { 'date' : exitdate, 'units' : units, 'price' : exitprice, 'realized P&L': self.realizedprofitloss }
            self.exittransactions.append(self.transaction)
            self.units = self.units + units
            unclosedunits = 0
            self.IsOpen = False
        
        elif abs(self.units) < abs(units):

            self.realizedprofitloss = self.realizedprofitloss - units * ( exitprice - self.entryprice )
            self.transaction = { 'date' : exitdate, 'units' : self.units, 'price' : exitprice, 'realized P&L': self.realizedprofitloss }
            self.exittransactions.append(self.transaction)
            self.units = 0
            unclosedunits = self.units + units 
            self.IsOpen = False
            
        self.update(price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l)
            
        return self.IsOpen, unclosedunits
        
class backtest_base(object):
    ''' Base class for event-based backtesting of trading strategies.
    '''

    def __init__(self, symbol, account_type, granularity, decision_frequency, start, end, amount, marginrate, ftc=0.0, ptc=0.0):
        self.symbol = symbol
        self.account_type = account_type
        self.granularity = granularity
        self.decision_frequency = decision_frequency
        self.file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(self.account_type,self.symbol,self.granularity)
        self.start = start
        self.end = end
        self.indicatorlist = []
        self.listofOpenTrades = []
        self.listofClosedTrades = []        
        
        # Notation:
        # Equity = Balance + UnrealizedP&L
        # Equity = Required margin	+ Free margin
        
        self.initial_equity = amount
        self.equity = self.initial_equity
        self.marginrate = marginrate # = 1 / Leverage
        self.required_margin = 0.0
        self.free_margin = self.equity
        self.balance = self.equity
        self.unrealizedprofitloss = 0.0
        self.realizedprofitloss = 0.0
        
        self.units_to_buy = 0
        self.units_to_sell = 0
        self.units_net = 0

        self.ftc = ftc
        self.ptc = ptc
        self.trades = 0
        self.verbose = True
        self.get_data()
        
    def get_data(self):

        self.h5 = tables.open_file(self.file_path, 'r')
        self.ts = self.h5.root.data._f_get_timeseries()
        raw = self.ts.read_range(self.start,self.end)
        raw = pd.DataFrame(raw)
                
        # Aggregate the high frequency data to the decision frequency
        ohlc_dict = {   'ask_o':'first', 'ask_h':'max', 'ask_l':'min', 'ask_c': 'last',                                                                                                    
                        'bid_o':'first', 'bid_h':'max', 'bid_l':'min', 'bid_c': 'last',                                                                                                    
                        'volume': 'sum' }

        raw_aggregate = raw.resample(self.decision_frequency, closed='left', label='left').apply(ohlc_dict).dropna()

        if len(raw_aggregate) == 0:
            
            print('There is no data available.')
            exit(0)
        
        else:            
        
            self.data = raw_aggregate.dropna()
            
            self.data.loc[:,'units_to_buy'] = 0
            self.data.loc[:,'units_to_sell'] = 0
            self.data.loc[:,'units_net'] = 0
        
    def add_indicators(self):
        
        pass

    def run_strategy(self):

        msg = '\n\nRunning strategy '
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        print('=' * 55)
        
        self.equity = self.initial_equity
        self.required_margin = 0.0
        self.free_margin = self.equity
        self.balance = self.equity
        self.profit_loss = 0.0

        for date, _ in self.data.iterrows():
    
            print(date)
            ''' Get signal
                Create buy/sell order
                -	Calculate PL
                -	Calculate required margin
                Check all open orders
                	Either add to the list
                	Eliminate some from list, move to ListofClosedOrders
            '''
            self.run_core_strategy()

        self.close_all_trades(date)
        self.update(date)
        self.close_out()
    
    def run_core_strategy(self):
        pass
        
    def plot_data(self):
        ''' Plots the (adjusted) closing prices for symbol.
        '''
        self.data['ask_c'].plot(figsize=(10, 6), title=self.symbol)

    def get_price(self, date):
        ''' Return price for a date.
        '''

        price_ask_c = self.data.loc[date,'ask_c']
        price_bid_c = self.data.loc[date,'bid_c']

        price_ask_h = self.data.loc[date,'ask_h']
        price_bid_h = self.data.loc[date,'bid_h']

        price_ask_l = self.data.loc[date,'ask_l']
        price_bid_l = self.data.loc[date,'bid_l']
            
        return price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l

    def open_long_trade(self, units, date):

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)
        self.data.loc[date,'units_to_buy'] = self.data.loc[date,'units_to_buy'] + units
                     
        if self.verbose:
            print('%s | buying  %4d units at ask %7.5f' %(date, units, price_ask_c))
        
        while True:

            self.listofOpenShortTrades = [ etrade for etrade in self.listofOpenTrades if etrade.units < 0 ]
        
            if len(self.listofOpenShortTrades) == 0:
               
                etrade = Trade(self.symbol, units, date, price_bid_c, price_ask_c, self.marginrate )
                self.units_net = self.units_net + units
                self.listofOpenTrades.append(etrade)
                                
                break
            
            else:

                etrade = self.listofOpenShortTrades[-1]

                IsOpen, unclosedunits = etrade.close(-units, date, price_bid_c, price_ask_c )
                self.units_net = self.units_net + units

                if not IsOpen:
                    self.listofOpenTrades.remove(etrade)
                    self.listofClosedTrades.append(etrade)

                if unclosedunits != 0:
                    
                    continue
                    units = unclosedunits
                    
                else:
                
                    break
                
    def close_long_trades(self, date):

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)
        self.data.loc[date,'units_to_sell'] = self.units_net

        if self.verbose:
            print('%s | closing long trades' %date)

        self.listofOpenLongTrades = [ etrade for etrade in self.listofOpenTrades if etrade.units > 0 ]
        
        for etrade in self.listofOpenLongTrades:
            self.units_net = self.units_net - etrade.units
            etrade.close(-etrade.units, date, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
            self.listofOpenTrades.remove(etrade)
            self.listofClosedTrades.append(etrade)
    
    def open_short_trade(self, units, date):
        
        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)
        self.data.loc[date,'units_to_sell'] = self.data.loc[date,'units_to_sell'] - units

        if self.verbose:
            print('%s | shorting %4d units at ask %7.5f' %(date, units, price_bid_c))
        
        while True:

            self.listofOpenLongTrades = [ etrade for etrade in self.listofOpenTrades if etrade.units > 0 ]
        
            if len(self.listofOpenLongTrades) == 0:
               
                etrade = Trade(self.symbol, units, date, price_bid_c, price_ask_c, self.marginrate )
                self.units_net = self.units_net + units
                self.listofOpenTrades.append(etrade)
                self.longshort = 'short'
                                
                break
            
            else:

                etrade = self.listofOpenLongTrades[-1]

                IsOpen, unclosedunits = etrade.close(units, date, price_bid_c, price_ask_c )
                self.units_net = self.units_net + units - unclosedunits

                if not IsOpen:
                    self.listofOpenTrades.remove(etrade)
                    self.listofClosedTrades.append(etrade)

                if unclosedunits != 0:
                    
                    continue
                    units = unclosedunits
                    
                else:
                
                    break
        
            
    def close_short_trades(self, date):

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)
        self.data.loc[date,'units_to_buy'] = -self.units_net

        if self.verbose:
            print('%s | closing short trades' %date)

        self.listofOpenShortTrades = [ etrade for etrade in self.listofOpenTrades if etrade.units < 0 ]
        
        for etrade in self.listofOpenShortTrades:
            self.units_net = self.units_net - etrade.units
            etrade.close(-etrade.units, date, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
            self.listofOpenTrades.remove(etrade)
            self.listofClosedTrades.append(etrade)
    
    def close_all_trades(self, date):
        ''' Closing out all long or short positions.
        '''
        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)
        if self.units_net < 0:
            self.data.loc[date,'units_to_buy'] = self.data.loc[date,'units_to_buy'] - self.units_net
        elif self.units_net > 0:
            self.data.loc[date,'units_to_sell'] = self.data.loc[date,'units_to_sell'] + self.units_net

        if self.verbose:
            print('%s | closing all trades' %date)
        
        self.listofOpenTrades = [ etrade for etrade in self.listofOpenTrades]
        
        for etrade in self.listofOpenTrades:
            self.units_net = self.units_net - etrade.units
            etrade.close(-etrade.units, date, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
            self.listofOpenTrades.remove(etrade)
            self.listofClosedTrades.append(etrade)
    
    def update(self, date):

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)
        for etrade in self.listofOpenTrades:
            etrade.update( price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
        
        self.realizedprofitloss = sum( etrade.realizedprofitloss for etrade in self.listofClosedTrades )
        self.unrealizedprofitloss = sum( etrade.unrealizedprofitloss for etrade in self.listofOpenTrades )
        self.balance = self.initial_equity + self.realizedprofitloss
        self.equity = self.balance + self.unrealizedprofitloss
        self.required_margin = sum( etrade.required_margin for etrade in self.listofOpenTrades )
        self.free_margin = self.equity - self.required_margin
        
        self.data.loc[date,'units_net'] = self.units_net
        self.data.loc[date,'equity'] = self.equity                    
        self.data.loc[date,'balance'] = self.balance                    
        self.data.loc[date,'realized P/L'] = self.realizedprofitloss                   
        self.data.loc[date,'unrealized P/L'] = self.unrealizedprofitloss                   
        self.data.loc[date,'required margin'] = self.required_margin                   
        self.data.loc[date,'free margin'] = self.free_margin                   
        
    def close_out(self):
    
        if self.verbose:
            print('=' * 55)
        print('Final equity   [$] %13.2f' % self.equity)
        print('Net Performance [%%] %13.2f' % ((self.equity - self.initial_equity) / self.initial_equity * 100))
        print('Number of transactions: ', len(self.listofClosedTrades) )
        print('=' * 55)

        self.data['return-asset'] = self.data['ask_c'] / self.data.ix[0,'ask_c']
        self.data['cumret-strategy'] = self.data['equity'] / self.data.ix[0,'equity']
        self.data['cumret-max'] = self.data['cumret-strategy'].cummax()
        self.data['cumret-min'] = self.data['cumret-strategy'].cummin()

    def optimizer(self, args):
        pass

if __name__ == '__main__':

     symbol = 'USD_TRY'
     account_type = 'practice'
     granularity = 'S5'
     decision_frequency = '1H'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2017,8,1,0,0,0)
     marginrate = 0.1
            
     bb = backtest_base(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, 10000, marginrate)

     visualize(bb.symbol, bb.data, bb.listofClosedTrades)
        
#     bb.plot_data()
#     plt.savefig('../plot.pdf')

