import sys
from sys import exit
#import os
#import math
import numpy as np
import pandas as pd
#from pandas_datareader import data as web
import matplotlib.pyplot as plt
import datetime
import tables 
#import tstables  
plt.style.use('seaborn')

sys.path.append('..\\source_system')
from indicators import *
import visualizer as viz
from utility_functions import *
sys.path.remove('..\\source_system')
import random
import statistics
import pickle
from statistics import mean

 # A standard lot = 100,000 units of base currency. 
 # A mini lot = 10,000 units of base currency.
 # A micro lot = 1,000 units of base currency.
 # A nano lot = 100 units of base currency.

class Trade(object):

    trade_counter = 1
        
    def __init__(self, symbol, units, entrydate, entrypricebid, entrypriceask, marginpercent ):
        self.ID = Trade.trade_counter
        Trade.trade_counter += 1
        self.symbol = symbol
        self.units = units #number of units of base currency
        self.longshort = 'long' if self.units > 0 else 'short'
        self.entrydate = entrydate
        self.entryprice = entrypriceask if self.units > 0 else entrypricebid
        self.marginpercent = marginpercent
        self.exittransactions = [] 
        self.IsOpen = True
        self.unrealizedprofitloss = 0.0
        self.realizedprofitloss = 0.0
        self.maxFavorableExcursion = 0.0
        self.maxAdverseExcursion = 0.0
        self.stat_required_margin = []
        self.stat_unrealizedprofitloss = []                                   
        self.duration = 0.0
    
    def update(self, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l ):

        self.duration = datetime.datetime.now() - self.entrydate
                     
        price_c = price_bid_c if self.units > 0 else price_ask_c      
        price_h = price_bid_h if self.units > 0 else price_ask_h      
        price_l = price_bid_l if self.units > 0 else price_ask_l      

        self.unrealizedprofitloss = self.units * ( price_c - self.entryprice )
        self.stat_unrealizedprofitloss.append(self.unrealizedprofitloss)

        self.required_margin = ( self.entryprice * abs(self.units) - self.unrealizedprofitloss ) * self.marginpercent / 100
        self.stat_required_margin.append(self.required_margin)                                   

        tempmaxFavorableExcursion = 0.0
        tempmaxAdverseExcursion = 0.0

        if self.units > 0:
            tempmaxFavorableExcursion = self.units * ( price_h - self.entryprice )
            tempmaxAdverseExcursion = self.units * ( price_l - self.entryprice )
        if self.units < 0:
            tempmaxFavorableExcursion = self.units * ( price_l - self.entryprice )
            tempmaxAdverseExcursion = self.units * ( price_h - self.entryprice )

        if tempmaxFavorableExcursion > self.maxFavorableExcursion:
            self.maxFavorableExcursion = tempmaxFavorableExcursion
        if tempmaxAdverseExcursion < self.maxAdverseExcursion:
            self.maxAdverseExcursion = tempmaxAdverseExcursion
                               
        #print('units:', self.units, 'p/l:', self.unrealizedprofitloss, 'maxFavorableExcursion:', self.maxFavorableExcursion, 'maxAdverseExcursion:', self.maxAdverseExcursion)
                        
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

    def __init__(self, symbol, account_type, granularity, decision_frequency, start, end, amount, marginpercent, ftc=0.0, ptc=0.0, verbose=False):
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
        self.stat_number_of_open_trades = []
        
        # Notation:
        # Equity = Balance + UnrealizedP&L
        # Equity = Required margin	+ Free margin
        
        self.initial_equity = amount
        self.equity = self.initial_equity

        self.marginpercent = marginpercent 
        # leverage = 100 / marginpercent
        # Leverage is conventionally displayed as a ratio, such as 20:1 or 50:1. However, here 
        # we use only the number on the left since the number on the right is always 1.
        
        # It is important to understand the relation between:
        # - Leverage
        # - Free Margin
        # - Trade size
        # - Risk
        # Leverage -> Free Margin -> Trade Size -> Risk (Arrow shows what affects what)
        # In simple case our trade size is fixed so leverage only affects free margin
        # Unless the required margin exceed current equity (definition above), algorithm works.
        # People associate leverage with risk because, typical investor uses high leverage
        # which leads to high free margin, which allows trader to take large trade size
        # It is the large trade size that ruins the trader.
        # Trade size should not exceed 1-2% of equity.
        
        self.required_margin = 0.0
        self.free_margin = self.equity
        self.balance = self.equity
        self.unrealizedprofitloss = 0.0
        self.realizedcumulativeprofitloss = 0.0
        self.listofrealizedprofitloss = np.array([])
        self.sharpe_ratio = 0.0 
        self.df_trades = pd.DataFrame()
            
        self.units_to_buy = 0
        self.units_to_sell = 0
        self.units_net = 0

        self.ftc = ftc # Fixed transaction cost
        self.ptc = ptc # Variable transaction cost
        self.trades = 0
        self.verbose = verbose
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

        print('=' * 55)
        msg = '\n\nRunning strategy '
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        
#        self.equity = self.initial_equity
#        self.required_margin = 0.0
#        self.free_margin = self.equity
#        self.balance = self.equity
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

        self.data.loc[date,'units_to_buy'] = self.data.loc[date,'units_to_buy'] + units
                     
        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)

        if self.verbose:
            print('%s | buying  %4d units at ask %7.5f' %(date, units, price_ask_c))
        
        while True:

            self.listofOpenShortTrades = [ etrade for etrade in self.listofOpenTrades if etrade.units < 0 ]
        
            if len(self.listofOpenShortTrades) == 0:
               
                etrade = Trade(self.symbol, units, date, price_bid_c, price_ask_c, self.marginpercent )
                self.units_net = self.units_net + units
                self.listofOpenTrades.append(etrade)
                                
                break
            
            else:

                etrade = self.listofOpenShortTrades[-1]

                IsOpen, unclosedunits = etrade.close(-units, date, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )

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

        self.data.loc[date,'units_to_sell'] = self.units_net

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)

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
               
                etrade = Trade(self.symbol, units, date, price_bid_c, price_ask_c, self.marginpercent )
                self.units_net = self.units_net + units
                self.listofOpenTrades.append(etrade)
                self.longshort = 'short'
                                
                break
            
            else:

                etrade = self.listofOpenLongTrades[-1]

                IsOpen, unclosedunits = etrade.close(units, date, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
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
        
        self.realizedcumulativeprofitloss = sum( etrade.realizedprofitloss for etrade in self.listofClosedTrades )
        self.unrealizedprofitloss = sum( etrade.unrealizedprofitloss for etrade in self.listofOpenTrades )
        self.balance = self.initial_equity + self.realizedcumulativeprofitloss
        self.equity = self.balance + self.unrealizedprofitloss
        self.required_margin = sum( etrade.required_margin for etrade in self.listofOpenTrades )
        self.free_margin = self.equity - self.required_margin

        self.stat_number_of_open_trades.append(len(self.listofOpenTrades))
        self.data.loc[date,'units_net'] = self.units_net
        self.data.loc[date,'equity'] = self.equity                    
        self.data.loc[date,'balance'] = self.balance                    
        self.data.loc[date,'realized cumulative P/L'] = self.realizedcumulativeprofitloss                   
        self.data.loc[date,'unrealized P/L'] = self.unrealizedprofitloss                   
        self.data.loc[date,'required margin'] = self.required_margin
        self.data.loc[date,'free margin'] = self.free_margin                   
        
    def close_out(self):
    
        self.numberoftrades = len(self.listofClosedTrades)
        self.data['return-asset'] = self.data['ask_c'] / self.data['ask_c'].iloc[0] - 1
        self.data['cumret-strategy'] = ( self.data['equity'] / self.initial_equity - 1 )
        self.data['cumret-max'] = self.data['cumret-strategy'].cummax()
        self.data['cumret-min'] = self.data['cumret-strategy'].cummin()
        self.data['drawdown'] = self.data['cumret-max'] - self.data['cumret-strategy']
    
        self.maxdrawdown = self.data['drawdown'].max()
        
        print('=' * 55)
        print('Initial equity   [$] {0:.2f}'.format(self.initial_equity))
        print('Final equity   [$] {0:.2f}'.format(self.equity))
        print('Net Performance [%] {0:.2f}'.format(self.data['cumret-strategy'][-1] * 100) )
        print('Number of transactions: {}'.format(self.numberoftrades ))
        print('Maximum drawdown: [%] {0:.2f}'.format(self.maxdrawdown * 100) )

    def optimizer(self, args):
        pass

    def plot(self):

        self.plot_data()
        self.plot_returns()
#        self.plot_PnL_vs_Trade_Number()
        self.plot_PnL_histogram()
#        self.plot_drawdown()
        self.plot_MAE()
        self.plot_MFE()

    def plot_data(self):
        ''' Plots the (adjusted) closing prices for symbol.
        '''
        fig1 = self.data['ask_c'].plot(figsize=(10, 6), title=self.symbol)
        fig2 = fig1.get_figure()
        fig2.savefig('C:\\Users\\bora\\Documents\\GitHub\\visualizations\\data.pdf')
        
    def plot_returns(self):

        fig1 = self.data[['cumret-strategy','cumret-max', 'return-asset']].plot(figsize=(10,6))
        fig2 = fig1.get_figure()
        fig2.savefig('C:\\Users\\bora\\Documents\\GitHub\\visualizations\\returns.pdf')

    def plot_PnL_histogram(self):
        
        binwidth = 1
        val_pnl = []
        
        for eTrade in self.listofClosedTrades:
            val_pnl.append(eTrade.realizedprofitloss)
        
        plt.title('PnL Histogram')
        plt.ylabel('Number of Trades')
        plt.xlabel('Profit/Loss')
        plt.hist(val_pnl, bins=range( np.int(np.floor(min(val_pnl))), np.int(np.ceil(max(val_pnl))) + binwidth, binwidth))
        
    def plot_drawdown(self):

        fig1 = self.data[['drawdown']].plot(figsize=(10,6))
        fig2 = fig1.get_figure()
        fig2.savefig('C:\\Users\\bora\\Documents\\GitHub\\visualizations\\drawdown.pdf')

    def plot_PnL_vs_Trade_Number(self):

        plt.autoscale(enable=True, axis='both', tight=None)
        plt.title('PnL vs. Trade Number')
        plt.plot(self.listofrealizedprofitloss, 'ro', markersize = 4)
        plt.savefig('C:\\Users\\bora\\Documents\\GitHub\\visualizations\\PnL_vs_Trade_Number.pdf')
        
    def plot_MAE(self):

        val_ID = []
        val_MAE = []
        val_pnl = []

        for eTrade in self.listofClosedTrades:
            if eTrade.realizedprofitloss >= 0:
                val_ID.append(eTrade.ID)
                val_MAE.append(eTrade.maxAdverseExcursion)
                val_pnl.append(eTrade.realizedprofitloss)
        
        plt.scatter(val_MAE, val_pnl, color='g', marker='o', s = 8)
        plt.title("MAE vs PnL for winning trades")
        plt.xlabel("MAE")
        plt.ylabel("PnL")
        plt.show()
        plt.close()
           
        val_ID = []
        val_MAE = []
        val_pnl = []
        
        for eTrade in self.listofClosedTrades:
            if eTrade.realizedprofitloss < 0:
                val_ID.append(eTrade.ID)
                val_MAE.append(eTrade.maxAdverseExcursion)
                val_pnl.append(eTrade.realizedprofitloss)
        
        plt.scatter(val_MAE, val_pnl, color='r', marker='o', s = 8)
        plt.title("MAE vs PnL for losing trades")
        plt.xlabel("MAE")
        plt.ylabel("PnL")
        plt.show()
        plt.close()

    def plot_MFE(self):
        
        val_ID = []
        val_MFE = []
        val_pnl = []
        
        for eTrade in self.listofClosedTrades:
            if eTrade.realizedprofitloss >= 0:
                val_ID.append(eTrade.ID)
                val_MFE.append(eTrade.maxFavorableExcursion)
                val_pnl.append(eTrade.realizedprofitloss)
        
        plt.scatter(val_MFE, val_pnl, color='g', marker='o', s = 8)
        plt.title("MFE vs PnL for winning trades")
        plt.xlabel("MFE")
        plt.ylabel("PnL")
        plt.show()
        plt.close()
           
        val_ID = []
        val_MFE = []
        val_pnl = []
    
        for eTrade in self.listofClosedTrades:
            if eTrade.realizedprofitloss < 0:
                val_ID.append(eTrade.ID)
                val_MFE.append(eTrade.maxFavorableExcursion)
                val_pnl.append(eTrade.realizedprofitloss)
    
        plt.scatter(val_MFE, val_pnl, color='r', marker='o', s = 8)
        plt.title("MFE vs PnL for losing trades")
        plt.xlabel("MFE")
        plt.ylabel("PnL")
        plt.show()
        plt.close()

    def plot_consecutive_win(self):

        lists = sorted(self.consecutive_win.items()) # sorted by key, return a list of tuples
        x, y = zip(*lists) # unpack a list of pairs into two tuples
        plt.bar(x, y)
        plt.title("Number of Consecutive Win")
        plt.show()

    def plot_consecutive_loss(self):

        lists = sorted(self.consecutive_loss.items()) # sorted by key, return a list of tuples
        x, y = zip(*lists) # unpack a list of pairs into two tuples
        plt.bar(x, y)
        plt.title("Number of Consecutive Loss")
        plt.show()

    def plot_equity(self):

        if len(self.data[self.data['free margin'] < 0 ]) > 0:                
        
            print('Margin requirement exceeded equity at least one point in time, need to change trade size')
            
        else:
            
            self.data[['required margin','free margin']].plot.area(title="Equity (required + free margin)")
            self.data['balance'].plot(title="Balance")
        
    def calculate_stats(self):
        
        self.calculate_PnL()
        self.calculate_sharpe_ratio()
        self.calculate_winning_losing_ratio()
        self.calculate_sortino_ratio(0)
        self.calculate_average_win()
        self.calculate_average_lose()
        self.calculate_expectancy()
        self.calculate_consecutive_win_loss()
        self.count_number_of_trading_days()
        
    def count_number_of_trading_days(self):
        
        msg = 'Number of trading days: {}'.format(len(set(self.data.index.date)))
        print(msg)
        
    def count_number_of_long_trades(self):
        
        self.numberofClosedLongTrades = len(set([x for x in self.listofClosedTrades if x.longshort == 'long']))
        
    def count_number_of_short_trades(self):

        self.numberofClosedShortTrades = len(set([x for x in self.listofClosedTrades if x.longshort == 'short']))
        
    def calculate_PnL(self):

        temp = []
        for etrade in self.listofClosedTrades:
            temp.append(etrade.realizedprofitloss)
        self.listofrealizedprofitloss = np.array(temp)
        
    def calculate_sharpe_ratio(self):

        pnl = self.listofrealizedprofitloss.mean()
        std = self.listofrealizedprofitloss.std()
        self.sharpe_ratio = pnl / std
        
        msg = 'Sharpe Ratio: {0:.2f}'.format(self.sharpe_ratio)
        print(msg)

    def calculate_sortino_ratio(self, threshold):

        pnl = self.listofrealizedprofitloss.mean()
        std = self.listofrealizedprofitloss[self.listofrealizedprofitloss<threshold].std()
        self.sortino_ratio = pnl / std
        msg = 'Sortino Ratio for threshold of {0:.2f}: {0:.2f}'.format(threshold, self.sortino_ratio)
        print(msg)

    def calculate_information_ratio(self):

        self.information_ratio = 0
        msg = 'Information Ratio: {0:.2f}'.format(self.information_ratio)
        print(msg)

    def calculate_average_win(self):

        self.average_win = self.listofrealizedprofitloss[self.listofrealizedprofitloss > 0].mean()

    def calculate_average_lose(self):

        self.average_lose = self.listofrealizedprofitloss[self.listofrealizedprofitloss < 0].mean()

    def calculate_winning_losing_ratio(self):
        
        self.winning_ratio = np.count_nonzero(self.listofrealizedprofitloss[self.listofrealizedprofitloss>=0]) / self.numberoftrades
        self.losing_ratio = 1 - self.winning_ratio
        
        msg = 'Winning Ratio: [%] {0:.2f} '.format(self.winning_ratio * 100)
        msg += '\nLosing Ratio: [%] {0:.2f}'.format(self.losing_ratio * 100)
        print(msg)

    def calculate_expectancy(self):
        
#        (AW × PW + AL × PL) ⁄ |AL|
#        AW = average winning trade (excluding maximum win) 
#        PW = probability of winning (PW = <wins> ⁄ NST where <wins> is total wins excluding maximum win) 
#        AL = average losing trade (negative, excluding scratch losses) 
#        |AL| = absolute value of AL 
#        PL = probability of losing (PL = <non-scratch losses> ⁄ NST)

        self.expectancy = ( self.winning_ratio * self.average_win + self.losing_ratio * self.average_lose ) / np.abs(self.average_lose)
        msg = 'Expectancy: {0:.2f} '.format(self.expectancy)
        print(msg)
        
    def calculate_consecutive_win_loss(self):

        # Compare consecutive trades to find out the cosecutive win/loss
            
        self.consecutive_win = {}
    
        self.consecutive_loss = {}
        
        same = 1
        
        prev_Trade = self.listofClosedTrades[0]
        
        for eTrade in self.listofClosedTrades[1:]:
                
            current_Trade = eTrade
            
            if current_Trade.realizedprofitloss * prev_Trade.realizedprofitloss >= 0:
    
                same = same + 1
                
            elif current_Trade.realizedprofitloss * prev_Trade.realizedprofitloss < 0:
    
                if prev_Trade.realizedprofitloss < 0:
    
#                    if not '{}'.format(same) in self.consecutive_loss.keys():
#                        
#                        self.consecutive_loss['{}'.format(same)] = 0
#                    
#                    self.consecutive_loss['{}'.format(same)] = self.consecutive_loss['{}'.format(same)]+1
                    if not same in self.consecutive_loss.keys():
                        
                        self.consecutive_loss[same] = 0
                    
                    self.consecutive_loss[same] = self.consecutive_loss[same]+1
                    
                if prev_Trade.realizedprofitloss > 0:
    
#                    if not '{}'.format(same) in self.consecutive_win.keys():
#                    
#                        self.consecutive_win['{}'.format(same)] = 0
#    
#                    self.consecutive_win['{}'.format(same)] = self.consecutive_win['{}'.format(same)]+1
                    if not same in self.consecutive_win.keys():
                    
                        self.consecutive_win[same] = 0
    
                    self.consecutive_win[same] = self.consecutive_win[same]+1
    
                same = 1
    
            if current_Trade == self.listofClosedTrades[-1]:
                                
                if current_Trade.realizedprofitloss * prev_Trade.realizedprofitloss >= 0:
                
                    same = same + 1
                    
                elif current_Trade.realizedprofitloss * prev_Trade.realizedprofitloss < 0:
                               
                    if current_Trade.realizedprofitloss < 0:
        
#                        if not '{}'.format(same) in self.consecutive_loss.keys():
#    
#                            self.consecutive_loss['{}'.format(same)] = 0
#                        
#                        self.consecutive_loss['{}'.format(same)] = self.consecutive_loss['{}'.format(same)]+1
                        if not same in self.consecutive_loss.keys():
    
                            self.consecutive_loss[same] = 0
                        
                        self.consecutive_loss[same] = self.consecutive_loss[same]+1
                        
                    if current_Trade.realizedprofitloss > 0:
        
                        if not same in self.consecutive_win.keys():
                        
                            self.consecutive_win[same] = 0
        
                        self.consecutive_win[same] = self.consecutive_win[same]+1
                                    
            prev_Trade = current_Trade

        msg = 'Consecutive Win: {} '.format(self.consecutive_win)
        msg += '\nConsecutive Loss: {} '.format(self.consecutive_loss)
        print(msg)
       

    def write_all_trades_to_excel(self):
        
        for eTrade in self.listofClosedTrades:
                
            self.df_trades.loc[eTrade.ID,'symbol'] = eTrade.symbol
            self.df_trades.loc[eTrade.ID,'units'] = eTrade.units
            self.df_trades.loc[eTrade.ID,'longshort'] = eTrade.longshort
            self.df_trades.loc[eTrade.ID,'entrydate'] = eTrade.entrydate
            self.df_trades.loc[eTrade.ID,'entryprice'] = eTrade.entryprice
            self.df_trades.loc[eTrade.ID,'realizedprofitloss'] = eTrade.realizedprofitloss
            self.df_trades.loc[eTrade.ID,'maxFavorableExcursion'] = eTrade.maxFavorableExcursion
            self.df_trades.loc[eTrade.ID,'maxAdverseExcursion'] = eTrade.maxAdverseExcursion
            self.df_trades.loc[eTrade.ID,'marginpercent'] = eTrade.marginpercent
                                        
            for idx, exTrade in enumerate(eTrade.exittransactions):
                
                self.df_trades.loc[eTrade.ID,'exit_{}_date'.format(idx)] = exTrade['date']
                self.df_trades.loc[eTrade.ID,'exit_{}_unit'.format(idx)] = exTrade['units']
                self.df_trades.loc[eTrade.ID,'exit_{}_price'.format(idx)] = exTrade['price']
                self.df_trades.loc[eTrade.ID,'exit_{}_realized P&L'.format(idx)] = exTrade['realized P&L']                
                
        now = datetime.datetime.now()
        filename = 'C:\\Users\\bora\\Documents\\GitHub\\visualizations\\trades_{}_{}.xlsx'.format(self.symbol, now.strftime("%Y-%m-%d-%H-%M"))

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        
        # Convert the dataframe to an XlsxWriter Excel object.
        self.df_trades.to_excel(writer, sheet_name='Sheet1')
        
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()
       
    def check_data_quality(self):
        
        '''
        Purpose is to check the returns from previous day based on high, low, close and find out if there are any that
        stands out 4 sigma. They should be extreme cases, o/w it is bad data.
        '''

        self.data['return_check_ask_h_over_c'] = self.data['ask_h'] / self.data['ask_c'].shift(1)
        self.data['return_check_ask_l_over_c'] = self.data['ask_l'] / self.data['ask_c'].shift(1)
        self.data['return_check_ask_c_over_c'] = self.data['ask_c'] / self.data['ask_c'].shift(1)

        self.data['return_check_bid_h_over_c'] = self.data['bid_h'] / self.data['bid_c'].shift(1)
        self.data['return_check_bid_l_over_c'] = self.data['bid_l'] / self.data['bid_c'].shift(1)
        self.data['return_check_bid_c_over_c'] = self.data['bid_c'] / self.data['bid_c'].shift(1)
        
        self.data['outlier_ask_h_over_c'] = np.abs( self.data['return_check_ask_h_over_c'] - self.data['return_check_ask_h_over_c'].mean() ) / self.data['return_check_ask_h_over_c'].std()
        self.data['outlier_ask_l_over_c'] = np.abs( self.data['return_check_ask_l_over_c'] - self.data['return_check_ask_l_over_c'].mean() ) / self.data['return_check_ask_l_over_c'].std()
        self.data['outlier_ask_c_over_c'] = np.abs( self.data['return_check_ask_c_over_c'] - self.data['return_check_ask_c_over_c'].mean() ) / self.data['return_check_ask_c_over_c'].std()

        self.data['outlier_bid_h_over_c'] = np.abs( self.data['return_check_bid_h_over_c'] - self.data['return_check_bid_h_over_c'].mean() ) / self.data['return_check_bid_h_over_c'].std()
        self.data['outlier_bid_l_over_c'] = np.abs( self.data['return_check_bid_l_over_c'] - self.data['return_check_bid_l_over_c'].mean() ) / self.data['return_check_bid_l_over_c'].std()
        self.data['outlier_bid_c_over_c'] = np.abs( self.data['return_check_bid_c_over_c'] - self.data['return_check_bid_c_over_c'].mean() ) / self.data['return_check_bid_c_over_c'].std()

        filename = 'C:\\Users\\bora\\Documents\\GitHub\\datastore\\outliers_{}.xlsx'.format(self.symbol)

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        
        # Convert the dataframe to an XlsxWriter Excel object.
        self.data.to_excel(writer, sheet_name='Sheet1')
        
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

        self.data.drop( ['return_check_ask_h_over_c', 'return_check_ask_l_over_c', 'return_check_ask_c_over_c', 'return_check_bid_h_over_c', 'return_check_bid_l_over_c', 'return_check_bid_c_over_c', 'outlier_ask_h_over_c', 'outlier_ask_l_over_c', 'outlier_ask_c_over_c', 'outlier_bid_h_over_c', 'outlier_bid_l_over_c', 'outlier_bid_c_over_c'], axis=1, inplace=True )

    def calculate_number_of_trades_to_simulate(self):
                
        frequency = (self.data.index[-1] - self.data.index[0]) / self.numberoftrades
        
        return int( pd.Timedelta(value='365D') / frequency )


    def durbin_watson_test(self, data):
        '''
        The null hypothesis of the test is that there is no serial correlation. The Durbin-Watson test statistics is defined as:
            ∑t=2T((et−et−1)2)/∑t=1Te2t

        The test statistic is approximately equal to 2*(1-r) where r is the sample autocorrelation of the residuals. Thus, for r == 0, 
        indicating no serial correlation, the test statistic equals 2. This statistic will always be between 0 and 4. The closer to 0 the 
        statistic, the more evidence for positive serial correlation. The closer to 4, the more evidence for negative serial correlation.
        '''
        from statsmodels.regression.linear_model import OLS
        from statsmodels.stats.stattools import durbin_watson

        ols_res = OLS(data, np.ones(len(data))).fit()

        print('=' * 55)
        msg = 'Durbin Watson Test:  '
        msg += '\nNo serial correlation, the test statistic equals 2.'
        msg += '\nThe closer to 0 the statistic, the more evidence for positive serial correlation.' 
        msg += '\nThe closer to 4, the more evidence for negative serial correlation.'
        msg += '\nDW Statistic: %.4f ' % durbin_watson(ols_res.resid)
        print(msg)
                
    def monte_carlo_simulator(self, cols=2500):
        '''
        Function to simulate trades for a given number of times.
    
        Parameters
        ==========
        rows: int
            number of trades to pick
        cols: int
            number of simulations
   
        Returns
        =======
        df: DataFrame object with simulated data
        '''

        '''
        It is a good practice to run Durbin-Watson test to check serial-correlation
        of trade returns. If there is no autocorrelation between trade results, then
        monte carlo can be used.        
        '''
        self.durbin_watson_test(self.listofrealizedprofitloss)
        
        no_of_rows = self.calculate_number_of_trades_to_simulate()
        no_of_cols = int(cols)
        
        # generate column names
        columns = ['Sim%d' % i for i in range(1, no_of_cols+1, 1)]
        rows = [i for i in range(1, no_of_rows+2, 1)]
        
        # generate sample paths for a selected set of trades
        self.simulations_df = pd.DataFrame( index=rows, columns=columns )
        
        self.simulations_maxdrawdown_pct = []
        self.simulations_profit_pct = []

        for eSim in columns:
        
            temp = [ self.initial_equity ]
                   
            total = self.initial_equity
            
            for eperiod in rows[:-1]:
        
                total = total + random.choice(self.listofrealizedprofitloss)
                temp.append( total )
                
            self.simulations_df[eSim] = temp
            
            self.simulations_df['cumret-strategy_{}'.format(eSim)] = ( self.simulations_df[eSim] / self.initial_equity - 1 )
            self.simulations_df['cumret-max_{}'.format(eSim)] = self.simulations_df['cumret-strategy_{}'.format(eSim)].cummax()
            self.simulations_df['cumret-min_{}'.format(eSim)] = self.simulations_df['cumret-strategy_{}'.format(eSim)].cummin()
            self.simulations_df['drawdown_pct_{}'.format(eSim)] = ( self.simulations_df['cumret-max_{}'.format(eSim)] - self.simulations_df['cumret-strategy_{}'.format(eSim)] ) / self.simulations_df['cumret-max_{}'.format(eSim)]
            #self.simulations_df['drawdown_pct_{}'.format(eSim)][self.simulations_df['drawdown_pct_{}'.format(eSim)] == np.inf] = 0
            self.simulations_df.loc[self.simulations_df['drawdown_pct_{}'.format(eSim)] == np.inf, 'drawdown_pct_{}'.format(eSim)] = 0
            
            self.simulations_maxdrawdown_pct.append( self.simulations_df['drawdown_pct_{}'.format(eSim)].max() )
            self.simulations_profit_pct.append( self.simulations_df['cumret-strategy_{}'.format(eSim)].iloc[-1] )

            del self.simulations_df['cumret-strategy_{}'.format(eSim)]
            del self.simulations_df['cumret-max_{}'.format(eSim)]
            del self.simulations_df['cumret-min_{}'.format(eSim)]
            del self.simulations_df['drawdown_pct_{}'.format(eSim)]
            
        self.simulations_df['mean'] = self.simulations_df.mean(axis=1)
        
        self.simulations_df['mean'].plot()
        
        self.simulations_mean_maxdrawdown_pct = np.mean( self.simulations_maxdrawdown_pct )
        self.simulations_median_maxdrawdown_pct = statistics.median( self.simulations_maxdrawdown_pct )
       
        self.simulations_mean_profit_pct = np.mean( self.simulations_profit_pct )
        self.simulations_median_profit_pct = statistics.median( self.simulations_profit_pct ) 

        self.calmar_ratio = self.simulations_median_profit_pct / self.simulations_median_maxdrawdown_pct

        print('=' * 55)
        msg = 'Monte Carlo Simulation Results:  '
        msg += '\nMean Max Drawdown Percent:   %.2f ' % self.simulations_mean_maxdrawdown_pct
        msg += '\nMedian Max Drawdown Percent: %.2f ' % self.simulations_median_maxdrawdown_pct
        msg += '\nCalmar Ratio                 %.4f ' % self.calmar_ratio
        print(msg)
    
    def analyze_trades(self):
        
        # Purpose is to collect stats from closed trades. This one collects all trades P/L for each
        # time period while they are open.
        self.trade_performance_over_time = pd.DataFrame()

        for eTrade in self.listofClosedTrades:
        
            for i in range( 1, len(eTrade.stat_unrealizedprofitloss)+1 ):
                
                self.trade_performance_over_time.loc[eTrade.ID, i] = eTrade.stat_unrealizedprofitloss[i-1]
        
        now = datetime.datetime.now()
        filename = 'C:\\Users\\bora\\Documents\\GitHub\\datastore\\trades_performance_over_time_{}_{}.xlsx'.format(self.symbol, now.strftime("%Y-%m-%d-%H-%M"))

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        
        # Convert the dataframe to an XlsxWriter Excel object.
        self.trade_performance_over_time.to_excel(writer, sheet_name='Sheet1')
        
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

    def calculate_average_number_of_bars_before_profitability(self):

        # Calculate how many time periods it typically takes to become profitable
        periods_before_profitable = {}
        periods_before_profitable_list = []

        for eTrade in self.listofClosedTrades:
        
            temp = self.trade_performance_over_time.loc[eTrade.ID, :]
            
            periods_before_profitable[eTrade.ID] = 0
                
            for i in range(1,len(temp)+1):
                
                if temp[i] > 0:
                    
                    periods_before_profitable[eTrade.ID] = i
                    break
                 
            if periods_before_profitable[eTrade.ID] == 0:
                
                periods_before_profitable[eTrade.ID] = len(temp)
                
            periods_before_profitable_list.append(periods_before_profitable[eTrade.ID])
                            
        periods_before_profitable_list_filtered = list(filter(lambda a: a < 24, periods_before_profitable_list))
        
        print('Mean number of periods (trade length < 24):', mean(periods_before_profitable_list_filtered))
        num_bins = 24 
        plt.hist(periods_before_profitable_list_filtered, num_bins)
        plt.show()

if __name__ == '__main__':

     symbol = 'EUR_USD'
     account_type = 'practice'
     granularity = 'S5'
     decision_frequency = '1H'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2017,8,1,0,0,0)
     marginpercent = 10
     verbose = False
       
     bb = backtest_base(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, 10000, marginpercent, verbose)
     bb.check_data_quality()

     viz.visualize(bb.symbol, bb.data, sorted(bb.listofClosedTrades, key=lambda k: k.ID), False)
     
    