import sys
from sys import exit
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import datetime
import tables 
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
import operator

 # A standard lot = 100,000 units of base currency. 
 # A mini lot = 10,000 units of base currency.
 # A micro lot = 1,000 units of base currency.
 # A nano lot = 100 units of base currency.

# In order to calculate pips per one lot, multiply the rate with this factor based on quote currency
pip_factor = {}
pip_factor['USD'] = 10000
pip_factor['JPY'] = 100
pip_factor['CHF'] = 10000
pip_factor['CAD'] = 10000
pip_factor['GBP'] = 10000

class Trade(object):

    '''
    Trade class is for nodeling individual trades 
    '''
    
    trade_counter = 1
        
    def __init__(self, symbol, units, entrydate, entrypricebid, entrypriceask, marginpercent, verbose ):
        self.ID = Trade.trade_counter
        Trade.trade_counter += 1
        self.symbol = symbol # Symbol for currency, e.g. EUR_USD
        self.base_currency = self.symbol[:3]
        self.quote_currency = self.symbol[-3:]
        self.units = units #number of units of base currency
        self.entry_unit = units #number of units of base currency
        self.longshort = 'long' if self.units > 0 else 'short'
        self.entrydate = entrydate
        self.entryprice = entrypriceask if self.units > 0 else entrypricebid
        # Always remember: ask price > bid price
        # When entering a long trade we pay ask price
        # When entering a short trade we pay bid price
        self.marginpercent = marginpercent # Margin percent between 0-100
        self.exittransactions = [] 
        self.IsOpen = True # Trade is open or close; initially set to open
        self.unrealizedpips = 0.0
        self.realizedpips = 0.0
        self.unrealizedprofitloss = 0.0
        self.realizedprofitloss = 0.0
        self.maxFavorableExcursion = 0.0
        self.maxAdverseExcursion = 0.0
        self.stat_required_margin = []
        self.stat_unrealizedprofitloss = []                                   
        self.stat_unrealizedpips = []                                   
        self.maxFavorableExcursionList = []
        self.maxAdverseExcursionList = []
        self.bars = 0
        self.verbose = verbose # Set to True to get detailed output during execution for debugging
        self.trade_size = abs(self.units) * self.entryprice * self.marginpercent / 100
        self.share_within_equity = [] # In practice we do not want the trade size exceed 1-2% of the equity. We willkeep an eye on this.
            
    def update(self, price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l ):

        '''
        Update trade statistics based on new price data, close, high, low, bid/ask
        '''                     
        
        '''
        Since when we enter a long trade we pay ask price
        We use bid price for evaluating long trades, as if we are exiting the trade
        Similarly we use ask price for evaluating short trades, as if we are exiting the trade
        '''
        price_c = price_bid_c if self.units > 0 else price_ask_c      
        price_h = price_bid_h if self.units > 0 else price_ask_h      
        price_l = price_bid_l if self.units > 0 else price_ask_l      

        tempmaxFavorableExcursion = 0.0
        tempmaxAdverseExcursion = 0.0

        if self.units > 0:
            tempmaxFavorableExcursion = self.units * ( price_h - self.entryprice ) 
            tempmaxAdverseExcursion = self.units * ( price_l - self.entryprice )
        if self.units < 0:
            tempmaxFavorableExcursion = self.units * ( price_l - self.entryprice )
            tempmaxAdverseExcursion = self.units * ( price_h - self.entryprice )

        if self.quote_currency == 'USD':

            self.unrealizedprofitloss = self.units * ( price_c - self.entryprice )
            self.stat_unrealizedprofitloss.append(self.unrealizedprofitloss)

            self.unrealizedpips = np.sign(self.units) * ( price_c - self.entryprice ) * pip_factor[self.quote_currency]
            self.stat_unrealizedpips.append(self.unrealizedpips)

            self.required_margin = ( self.entryprice * abs(self.units) - self.unrealizedprofitloss ) * self.marginpercent / 100
            self.stat_required_margin.append(self.required_margin)                                   
    
            if tempmaxFavorableExcursion > self.maxFavorableExcursion:
                self.maxFavorableExcursion = tempmaxFavorableExcursion
            if tempmaxAdverseExcursion < self.maxAdverseExcursion:
                self.maxAdverseExcursion = tempmaxAdverseExcursion

        else:

            '''
            Note that if quote currency is different than USD, then we need to divide by the price_c 
            to get in units of base currency. For non-USD cross rates, the output is in base currency.
            Note that this should still be ok as long as we are evaluating everything in the same units.
            '''
            
            self.unrealizedprofitloss = self.units * ( price_c - self.entryprice ) / price_c
            self.stat_unrealizedprofitloss.append(self.unrealizedprofitloss)

            self.unrealizedpips = ( price_c - self.entryprice ) * pip_factor[self.quote_currency]
            self.stat_unrealizedpips.append(self.unrealizedpips)

            self.required_margin = ( self.entryprice * abs(self.units) - self.unrealizedprofitloss ) / price_c * self.marginpercent / 100
            self.stat_required_margin.append(self.required_margin)                                   

            if tempmaxFavorableExcursion > self.maxFavorableExcursion:
                self.maxFavorableExcursion = tempmaxFavorableExcursion / price_c 
            if tempmaxAdverseExcursion < self.maxAdverseExcursion:
                self.maxAdverseExcursion = tempmaxAdverseExcursion / price_c 

        self.maxFavorableExcursionList.append(self.maxFavorableExcursion)
        self.maxAdverseExcursionList.append(self.maxAdverseExcursion)

        self.bars = self.bars + 1

        if self.verbose == True:
            
            print('ID:', self.ID, 'units:', self.units, 'p/l:', self.unrealizedprofitloss, 'pips',  self.unrealizedpips, 'margin:', self.required_margin, 'maxFavorableExcursion:', self.maxFavorableExcursion, 'maxAdverseExcursion:', self.maxAdverseExcursion)
                                      
    def close(self, untransactedunits, exitdate, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l ):

        '''
        Since when we enter a long trade we pay ask price, we use bid price for closing long trade
        Since when we enter a short trade we pay bid price, we use ask price for closing short trade
        Remember that ask price > bid price
        '''
        exitprice = price_bid_c if self.units > 0 else price_ask_c
        
        transactedunits = 0
        
        '''
        Trade object may receive a close request with a certain units, i.e. untransactedunits.
        Depending on the units of the current trade and the units requested to close (i.e. untransactedunits), current trade may close partially or completely.
        If the current trade closes completely then self.IsOpen is set to False and otherwise set to True.
        Transacted units are the units that are allocated for closing the order .
        If the requested size of the trade is greater than the size of the current trade, any size of the untransactedunits is returned back.
        Returned amount will be served by another trade or opened a new trade.
        '''        
        
        if abs(self.units) > abs(untransactedunits):

            transactedunits = untransactedunits
            self.units = self.units + untransactedunits
            untransactedunits = 0
            self.IsOpen = True
            
        elif abs(self.units) == abs(untransactedunits):
            
            transactedunits = untransactedunits
            self.units = self.units + untransactedunits
            untransactedunits = 0
            self.IsOpen = False
        
        elif abs(self.units) < abs(untransactedunits):

            transactedunits = -self.units
            untransactedunits = self.units + untransactedunits 
            self.units = 0
            self.IsOpen = False


        '''
        Calculate realized profit&loss
        If trade is closed in several steps, keep track of exit transactions        
        '''                
        self.realizedpips = self.realizedpips - np.sign(transactedunits) * ( exitprice - self.entryprice ) * pip_factor[self.quote_currency]
        
        if self.quote_currency == 'USD':

            self.realizedprofitloss = self.realizedprofitloss - transactedunits * ( exitprice - self.entryprice )            
                    
        else:

            self.realizedprofitloss = self.realizedprofitloss - units * ( exitprice - self.entryprice ) / price_c            

        self.transaction = { 'date' : exitdate, 'units' : transactedunits, 'price' : exitprice, 'realized P&L': self.realizedprofitloss }
        self.exittransactions.append(self.transaction)

        '''
        Calculate trade statistics at the close
        '''
        
        self.update(price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l)
            
        return self.IsOpen, abs(untransactedunits)
        
class backtest_base(object):
    
    ''' 
    Base class for event-based backtesting of trading strategies.
    '''

    def __init__(self, symbol, account_type, granularity, decision_frequency, start_date, end_date, idle_duration_before_start_trading, initial_equity, marginpercent, ftc=0.0, ptc=0.0, verbose=False):
        self.symbol = symbol # Same as trade symbol
        self.account_type = account_type # should be set to backtest, eventually used for file/folder name specification
        self.granularity = granularity # Data granularity
        self.decision_frequency = decision_frequency # Decision frequency can be less granular (e.g. 1H) than data granularity (e.g. S5)
        self.start_date = start_date # Start date
        self.end_date = end_date # End date
        self.date_to_start_trading = self.start_date + idle_duration_before_start_trading
        self.indicatorlist = []
        self.listofOpenTrades = []
        self.listofClosedTrades = []
        self.stat_number_of_open_trades = []

        self.backtest_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
        self.backtest_folder = self.file_path_ohlc = '..\\..\\backtests\\{}'.format(self.backtest_name)
        if( not os.path.exists(self.backtest_folder)):
            os.mkdir(self.backtest_folder) 

        self.df_edge_ratio = pd.DataFrame()
        self.maxNumberBars = 0
        
        '''
        Notation:
        Equity = Balance + UnrealizedP&L
        Equity = Required margin + Free margin
        '''
        
        self.initial_equity = initial_equity
        self.equity = self.initial_equity

        self.marginpercent = marginpercent # Margin percent between 0-100
        
        '''
        leverage = 100 / marginpercent
        Leverage is conventionally displayed as a ratio, such as 20:1 or 50:1. However, here 
        we use only the number on the left since the number on the right is always 1.
        
        It is important to understand the relation between:
        - Leverage
        - Free Margin
        - Trade size
        - Risk
        Leverage -> Free Margin -> Trade Size -> Risk (Arrow shows what affects what)
        
        In the simplest case, our trade size is fixed so leverage only affects free margin.
        Unless the required margin exceed current equity (defined above), algorithm works.
        
        People associate leverage with risk because, typical investor uses high leverage
        which leads to high free margin (low required margin), which allows trader to take larger trade size.
        It is this large trade size that ruins the trader.
        As a rule of thumb, trade size should not exceed 1-2% of equity.
        '''
        
        self.required_margin = 0.0
        self.free_margin = self.equity
        self.balance = self.equity
        self.unrealizedprofitloss = 0.0
        self.realizedcumulativeprofitloss = 0.0
        self.unrealizedpips = 0.0
        self.realizedcumulativepips = 0.0
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
        self.data = pd.DataFrame()        

        self.data = read_hdf_file(self.account_type,self.symbol,self.granularity)
        self.data.loc[:,'units_to_buy'] = 0
        self.data.loc[:,'units_to_sell'] = 0
        self.data.loc[:,'units_net'] = 0
       
    '''                         
    def read_hdf_file(self):

        This input data file is generated offline by the file source_research > _create_research_data.py
        This is higher granularity data, i.e. at least as granular as the decision frequency. It can be identical to decision frequency.
        Advantage of using higher granularity data compared to decision frequency is to capture trade statisctics in a more refined way.

        filepath = '..\\..\\datastore\\_{0}\\{1}\\{2}.hdf'.format(self.account_type,self.symbol,self.granularity)
        if os.path.exists( filepath ):
            self.data = pd.read_hdf(filepath)
        self.data = self.data[['ask_o', 'ask_h', 'ask_l', 'ask_c', 'bid_o', 'bid_h', 'bid_l', 'bid_c', 'volume']]
    '''
    
    def add_indicators(self):
        '''
        This should be overwritten within derived classes from this base class.
        '''
        pass

    def run_strategy(self):

        self.add_indicators()

        self.data = self.data.iloc[(self.data.index.date >= self.date_to_start_trading) and (self.data.index.date <=self.end),:]
        
        print('-' * 55)
        msg = '\n\nRunning strategy '
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        print('-' * 55)
                
        for date, _ in self.data.iterrows():
            
            '''
            In case we need to update P/L using more refined data (e.g. hourly) and make decisions more 
            aggregate time period (e.g. daily), assume transaction is done at a certain hour of the day, 
            e.g. CST or UTC time. Below, I assume 9:00 PM UTC, 4 PM EST, 3 PM CST.
            '''
            if date.hour == 9:
                    
                ''' 
                Get signal
                Create buy/sell order

                Check all open orders
                - 	Either add to the list
                -	Or eliminate some from list, move to ListofClosedOrders
                '''

            '''
            At every time step
            -	Calculate PL
            -	Calculate required margin
            '''
            self.run_core_strategy()

        self.close_all_trades(date)
        self.update(date)
        self.close_out()
    
    def run_core_strategy(self):
        '''
        This should be overwritten within derived classes from this base class.
        '''
        pass
        
    def get_price(self, date):
        ''' 
        Return price for a given date.
        '''

        price_ask_c = self.data.loc[date,'ask_c']
        price_bid_c = self.data.loc[date,'bid_c']

        price_ask_h = self.data.loc[date,'ask_h']
        price_bid_h = self.data.loc[date,'bid_h']

        price_ask_l = self.data.loc[date,'ask_l']
        price_bid_l = self.data.loc[date,'bid_l']
            
        return price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l

    def open_long_trade(self, units_to_buy, date):
        ''' 
        Enter into long trade on a given date
        '''
        self.data.loc[date,'units_to_buy'] = self.data.loc[date,'units_to_buy'] + units_to_buy

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)

        self.units_net = self.units_net + units_to_buy
        
        if self.verbose:

            print('%s | buying  %4d units at ask %7.5f' %(date, units_to_buy, price_ask_c))

        while True:

            '''
            First check if there are existing short trades.            
            '''
            self.listofOpenShortTrades = [ etrade for etrade in self.listofOpenTrades if etrade.units < 0 ]
        
            if len(self.listofOpenShortTrades) == 0:
                
                '''
                If there is no short trade then open a long trade
                Note that units_to_buy > 0
                '''
                etrade = Trade(self.symbol, units_to_buy, date, price_bid_c, price_ask_c, self.marginpercent, self.verbose )
                #etrade.update(price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
                self.listofOpenTrades.append(etrade)
                self.longshort = 'long'                                
                break
            
            else:
               
                '''
                If there exists some short trades then we need to close those trades before opening a long trade.
                If there are multiple short trades, then close the last trade first.
                '''
                etrade = self.listofOpenShortTrades[-1]

                IsOpen, units_to_buy = etrade.close(units_to_buy, date, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
                '''
                If IsOpen is False that means that the existing short trade is closed.
                If units_to_buy (returned parameter) is zero that means that units_to_buy (input parameter) is greater than the size of the existing short trade. 
                If units_to_buy (returned parameter) is non-zero that means that the existing short trade size was not enough to cover the long trade.Therefore, we still have some more units to sell.
                If IsOpen is True that means that the existing short trade is not closed; units_to_buy (input parameter) is less than the size of the existing short trade.
                '''    
                if not IsOpen:
                    self.listofOpenTrades.remove(etrade)
                    self.listofClosedTrades.append(etrade)

                '''
                It there is still some non-zero units to buy, check if there is more short trades to close or open a new long trade.
                '''
                if units_to_buy > 0:
                                        
                    continue
                    
                else:
                
                    break
                
    def close_long_trades(self, date):
        '''
        Close all long trades.
        '''
        
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
    
    def open_short_trade(self, units_to_sell, date):
        ''' 
        Enter into short trade on a given date
        '''                
        self.data.loc[date,'units_to_sell'] = self.data.loc[date,'units_to_sell'] - units_to_sell

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)
    
        self.units_net = self.units_net - units_to_sell
        
        if self.verbose:

            print('%s | shorting %4d units at ask %7.5f' %(date, units_to_sell, price_bid_c))
        
        while True:

            '''
            First check if there are existing long trades.            
            '''
            self.listofOpenLongTrades = [ etrade for etrade in self.listofOpenTrades if etrade.units > 0 ]
        
            if len(self.listofOpenLongTrades) == 0:

                '''
                If there is no long trade then open a short trade
                Note that units_to_sell > 0
                '''                
                etrade = Trade(self.symbol, -units_to_sell, date, price_bid_c, price_ask_c, self.marginpercent, self.verbose )
                #etrade.update(price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l)
                self.listofOpenTrades.append(etrade)
                self.longshort = 'short'
                                
                break
            
            else:

                '''
                If there exists any long trade then we need to close those trades before opening a short trade.
                If there are multiple long trades, then close the last trade first.
                '''
                etrade = self.listofOpenLongTrades[-1]

                IsOpen, units_to_sell = etrade.close(-units_to_sell, date, price_bid_c, price_ask_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
                '''
                If IsOpen is False that means that the existing long trade is closed.
                If units_to_sell (returned parameter) is zero that means that units_to_sell (input parameter) is greater than the size of the existing long trade. 
                If units_to_sell (returned parameter) is non-zero that means that the existing long trade size was not enough to cover the short trade. Therefore, we still have some more units to sell.
                If IsOpen is True that means that the existing long trade is not closed; units_to_sell (input parameter) is less than the size of the existing long trade.
                '''    
                if not IsOpen:
                    self.listofOpenTrades.remove(etrade)
                    self.listofClosedTrades.append(etrade)

                '''
                It there is still some non-zero units to sell, check if there is more long trades to close or open a new short trade.
                '''
                if units_to_sell > 0:
                    
                    continue
                    
                else:
                
                    break
            
    def close_short_trades(self, date):
        '''
        Close all short trades.
        '''
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
        ''' 
        Closing out all long or short positions.
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
        '''
        Update each trade based on new data        
        '''

        price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l = self.get_price(date)

        for etrade in self.listofOpenTrades:
            etrade.update( price_ask_c, price_bid_c, price_ask_h, price_bid_h, price_ask_l, price_bid_l )
            
        self.realizedcumulativeprofitloss = sum( etrade.realizedprofitloss for etrade in self.listofClosedTrades )
        self.unrealizedprofitloss = sum( etrade.unrealizedprofitloss for etrade in self.listofOpenTrades )
        
        self.realizedcumulativepips = sum( etrade.realizedpips for etrade in self.listofClosedTrades )
        self.unrealizedpips = sum( etrade.unrealizedpips for etrade in self.listofOpenTrades )
        
        self.balance = self.initial_equity + self.realizedcumulativeprofitloss
        self.equity = self.balance + self.unrealizedprofitloss
        self.required_margin = sum( etrade.required_margin for etrade in self.listofOpenTrades )
        self.free_margin = self.equity - self.required_margin

        for etrade in self.listofOpenTrades:
            etrade.share_within_equity.append( etrade.trade_size / self.equity )

        self.stat_number_of_open_trades.append(len(self.listofOpenTrades))
        self.data.loc[date,'units_net'] = self.units_net
        self.data.loc[date,'equity'] = self.equity                    
        self.data.loc[date,'balance'] = self.balance                    
        self.data.loc[date,'realized cumulative P/L'] = self.realizedcumulativeprofitloss                   
        self.data.loc[date,'unrealized P/L'] = self.unrealizedprofitloss   
        self.data.loc[date,'realized cumulative pips'] = self.realizedcumulativepips                   
        self.data.loc[date,'unrealized pips'] = self.unrealizedpips   
        self.data.loc[date,'required margin'] = self.required_margin
        self.data.loc[date,'free margin'] = self.free_margin             
        
        print('Date: {0}, Equity: {1:.2f}, Realized Cumulative P/L: {2:.2f}, Unrealized P/L: {3:.2f}, Realized Cumulative pips: {4:.2f}, Unrealized pips: {5:.2f}'.format( date, self.equity, self.realizedcumulativeprofitloss, self.unrealizedprofitloss, self.realizedcumulativepips, self.unrealizedpips ) )
        
    def close_out(self):
        '''
        Calculate final statistics at closing
        '''
        
        self.numberoftrades = len(self.listofClosedTrades)
        self.data['return-asset'] = self.data['ask_c'] / self.data['ask_c'].iloc[0] - 1
        self.data['cumret-strategy'] = ( self.data['equity'] / self.initial_equity - 1 )
        self.data['cumret-max'] = self.data['cumret-strategy'].cummax()
        self.data['cumret-min'] = self.data['cumret-strategy'].cummin()
        self.data['drawdown'] = self.data['cumret-max'] - self.data['cumret-strategy']
    
        self.maxdrawdown = self.data['drawdown'].max()
        
        print('-' * 55)
        print('Performance:')
        print('Initial equity   [$] {0:.2f}'.format(self.initial_equity))
        print('Final equity   [$] {0:.2f}'.format(self.equity))
        print('Net Performance [%] {0:.2f}'.format(self.data['cumret-strategy'][-1] * 100) )
        print('Asset Performance [%] {0:.2f}'.format(self.data['return-asset'][-1] * 100) )
        print('Number of transactions: {}'.format(self.numberoftrades ))
        
        print('Maximum drawdown: [%] {0:.2f}'.format(self.maxdrawdown * 100) )

    def optimizer(self, args):
        pass

    def plot(self):

        self.plot_data()
        self.plot_returns()
        self.plot_PnL_vs_Trade_Number()
        self.plot_PnL_histogram()
        self.plot_drawdown()
        self.plot_MAE()
        self.plot_MFE()
        self.plot_consecutive_win()
        self.plot_consecutive_loss()
        self.plot_edge_ratio()
        
    def plot_data(self):
        ''' Plots the (adjusted) closing prices for symbol.
        '''
        fig1 = self.data['ask_c'].plot(figsize=(10, 6), title=self.symbol)
        fig2 = fig1.get_figure()
        fig2.savefig('{}\\data.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()
        
    def plot_returns(self):

        fig1 = self.data[['cumret-strategy','cumret-max', 'return-asset']].plot(figsize=(10,6), title='Returns')
        fig2 = fig1.get_figure()
        fig2.savefig('{}\\returns.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()

    def plot_PnL_vs_Trade_Number(self):

        #plt.autoscale(enable=True, axis='both', tight=None)
        plt.title('PnL vs. Trade Number')
        plt.plot(self.listofrealizedprofitloss, 'ro', markersize = 4)
        plt.savefig('{}\\PnL_vs_Trade_Number.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()
        
    def plot_PnL_histogram(self):
        
        binwidth = 1
        val_pnl = []
        
        for eTrade in self.listofClosedTrades:
            val_pnl.append(eTrade.realizedprofitloss)
        
        plt.title('PnL Histogram')
        plt.ylabel('Number of Trades')
        plt.xlabel('Profit/Loss')
        plt.hist(val_pnl, bins=range( np.int(np.floor(min(val_pnl))), np.int(np.ceil(max(val_pnl))) + binwidth, binwidth))
        plt.savefig('{}\\PnL_histogram.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()
        
    def plot_drawdown(self):

        fig1 = self.data[['drawdown']].plot(figsize=(10,6), title='Drawdown')
        fig2 = fig1.get_figure()
        fig2.savefig('{}\\drawdown.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()

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
        plt.savefig('{}\\MAE_vs_PnL_for_winning_trade.pdf'.format(self.backtest_folder))
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
        plt.savefig('{}\\MAE_vs_PnL_for_losing_trade.pdf'.format(self.backtest_folder))
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
        plt.savefig('{}\\MFE_vs_PnL_for_winning_trade.pdf'.format(self.backtest_folder))
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
        plt.savefig('{}\\MFE_vs_PnL_for_losing_trade.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()

    def plot_consecutive_win(self):

        lists = sorted(self.consecutive_win.items()) # sorted by key, return a list of tuples
        x, y = zip(*lists) # unpack a list of pairs into two tuples
        plt.figure().gca().xaxis.set_major_locator(MaxNLocator(integer=True))
        plt.bar(x, y)
        plt.title("Number of Consecutive Win")
        plt.show()
        plt.close()

    def plot_consecutive_loss(self):

        lists = sorted(self.consecutive_loss.items()) # sorted by key, return a list of tuples
        x, y = zip(*lists) # unpack a list of pairs into two tuples
        plt.figure().gca().xaxis.set_major_locator(MaxNLocator(integer=True))
        plt.bar(x, y)      
        plt.title("Number of Consecutive Loss")
        plt.show()
        plt.close()

    def plot_edge_ratio(self):
        
        ''' 
        Plots the edge-ratio over trades.
        '''
        fig1 = self.df_edge_ratio['mean'].plot(figsize=(10, 6), title='edge-ratio curve for {}'.format(self.symbol))
        fig2 = fig1.get_figure()
        fig2.savefig('{}\\edge_ratio.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()
        
    def plot_equity(self):

        if len(self.data[self.data['free margin'] < 0 ]) > 0:                
        
            print('Margin requirement exceeded equity at least one point in time, need to change trade size')
            
        else:
            
            self.data[['required margin','free margin']].plot.area(title="Equity (required + free margin)")
            self.data['balance'].plot(title="Balance")
        
    def calculate_stats(self):

        print('-' * 55)
        print('Statistics:')
        
        if self.numberoftrades == 0:
            
            print('No trading available')
    
        else:
            
            self.count_number_of_long_trades()
            self.count_number_of_short_trades()
            self.calculate_PnL()
            self.calculate_winning_losing_ratio()
            self.calculate_sharpe_ratio()
            self.calculate_sortino_ratio(0)
            self.calculate_average_win()
            self.calculate_average_loss()
            self.calculate_expectancy()
            self.calculate_consecutive_win_loss()
            self.count_number_of_trading_days()
            self.calculate_edge_ratio()
        
    def count_number_of_trading_days(self):
        
        msg = 'Number of trading days: {}'.format(len(set(self.data.index.date)))
        print(msg)
        
    def count_number_of_long_trades(self):
        
        self.numberofClosedLongTrades = len(set([x for x in self.listofClosedTrades if x.longshort == 'long']))
        msg = 'Number of long trades: {}'.format(self.numberofClosedLongTrades)
        print(msg)
        
    def count_number_of_short_trades(self):

        self.numberofClosedShortTrades = len(set([x for x in self.listofClosedTrades if x.longshort == 'short']))
        msg = 'Number of short trades: {}'.format(self.numberofClosedShortTrades)
        print(msg)
                        
    def calculate_PnL(self):

        temp = []
        for etrade in self.listofClosedTrades:
            temp.append(etrade.realizedprofitloss)
        self.listofrealizedprofitloss = np.array(temp)
        
    def calculate_sharpe_ratio(self):

        print('Note that the risk-free rate is assumed to be zero!')
        pnl = self.listofrealizedprofitloss.mean()
        std = self.listofrealizedprofitloss.std()
        self.sharpe_ratio = pnl / std
        
        msg = 'Sharpe Ratio: {0:.2f}'.format(self.sharpe_ratio)
        print(msg)

    def calculate_sortino_ratio(self, threshold):

        pnl = self.listofrealizedprofitloss.mean()
        std = self.listofrealizedprofitloss[self.listofrealizedprofitloss<threshold].std()
        self.sortino_ratio = pnl / std

        msg = 'Sortino Ratio for threshold of {0:.2f}: {1:.3f}'.format(threshold, round(self.sortino_ratio,3))
        print(msg)

    def calculate_average_win(self):

        self.average_win = self.listofrealizedprofitloss[self.listofrealizedprofitloss > 0].mean()

    def calculate_average_loss(self):

        self.average_loss = self.listofrealizedprofitloss[self.listofrealizedprofitloss < 0].mean()

    def calculate_winning_losing_ratio(self):
                
        self.winning_ratio = np.count_nonzero(self.listofrealizedprofitloss[self.listofrealizedprofitloss>=0]) / self.numberoftrades
        self.losing_ratio = 1 - self.winning_ratio
        
        msg = 'Winning Ratio: [%] {0:.2f} '.format(self.winning_ratio * 100)
        msg += '\nLosing Ratio: [%] {0:.2f}'.format(self.losing_ratio * 100)
        print(msg)

    def calculate_expectancy(self):
        
        '''
        (AW × PW + AL × PL) ⁄ |AL|
        AW = average winning trade (excluding maximum win) 
        PW = probability of winning (PW = <wins> ⁄ numberoftrades where <wins> is total wins) 
        AL = average losing trade (negative, excluding scratch losses) 
        |AL| = absolute value of AL 
        It is important to have the |AL| in the denominator of expectancy because this converts the expectancy to "risk units" — earnings per dollar risked.   
        PL = probability of losing (PL = <losses> ⁄ numberoftrades)
        '''
        
        self.expectancy = ( self.winning_ratio * self.average_win + self.losing_ratio * self.average_loss ) / np.abs(self.average_loss)
        msg = 'Expectancy (Earnings per dollar risked): {0:.2f} '.format(self.expectancy)
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

    def calculate_edge_ratio(self):
        
        '''
        Idea comes from buildalpha: https://www.buildalpha.com/e-ratio/
        It is called e-ratio or edge ratio
        Edge Ratio or E-Ratio measures how much a trade goes in your favor vs. how much a trade goes against you. 
        The x-axis is the number of bars since the trading signal. A higher y-value signifies more “edge” at that step in time.
        '''
        '''
        Add ATR as an indicator to normalize the MFE and MAE
        #self.data, self.indicatorlist = AddATR(self.data, self.indicatorlist, 'bid', timeperiod=14, std=0)
        For now, exclude normalizing using ATR
        '''
        #Find the max number of bars over all the trades        
        maxBars = max(self.listofClosedTrades, key=operator.attrgetter('bars')).bars
                
        bar_index = np.arange(1, maxBars+1)
        self.df_maxFavorableExcursion = pd.DataFrame(index=bar_index)
        self.df_maxAdverseExcursion = pd.DataFrame(index=bar_index)

        for eTrade in self.listofClosedTrades:

            temp = pd.DataFrame(eTrade.maxFavorableExcursionList, index=np.arange(1, eTrade.bars+1), columns=['Trade{}'.format(eTrade.ID)] )
            self.df_maxFavorableExcursion = pd.concat([self.df_maxFavorableExcursion, temp], axis=1, ignore_index=True)

            temp = -pd.DataFrame(eTrade.maxAdverseExcursionList, index=np.arange(1, eTrade.bars+1), columns=['Trade{}'.format(eTrade.ID)] )
            self.df_maxAdverseExcursion = pd.concat([self.df_maxAdverseExcursion, temp], axis=1, ignore_index=True)

        self.df_edge_ratio = self.df_maxFavorableExcursion.div(self.df_maxAdverseExcursion)
        
        filename = '{}\\{}_df_maxFavorableExcursion.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.df_maxFavorableExcursion)

        filename = '{}\\{}_df_maxAdverseExcursion.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.df_maxAdverseExcursion)
        
        self.df_edge_ratio['mean'] = self.df_edge_ratio.mean(axis=1)
        
        filename = '{}\\{}_df_edge_ratio.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.df_edge_ratio)
        
               
    def write_all_data(self):
        
        now = datetime.datetime.now()
        filename = '{}\\{}_data.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.data)
    
    def write_all_trades_to_excel(self):
        
        for eTrade in self.listofClosedTrades:
                
            self.df_trades.loc[eTrade.ID,'Symbol'] = eTrade.symbol
            self.df_trades.loc[eTrade.ID,'EntryUnit'] = eTrade.entry_unit
            self.df_trades.loc[eTrade.ID,'longShort'] = eTrade.longshort
            self.df_trades.loc[eTrade.ID,'EntryDate'] = eTrade.entrydate
            self.df_trades.loc[eTrade.ID,'EntryPrice'] = eTrade.entryprice
            self.df_trades.loc[eTrade.ID,'RealizedProfitloss'] = eTrade.realizedprofitloss
            self.df_trades.loc[eTrade.ID,'RealizedPips'] = eTrade.realizedpips
            self.df_trades.loc[eTrade.ID,'MaxFavorableExcursion'] = eTrade.maxFavorableExcursion
            self.df_trades.loc[eTrade.ID,'MaxAdverseExcursion'] = eTrade.maxAdverseExcursion
            self.df_trades.loc[eTrade.ID,'MarginPercent'] = eTrade.marginpercent
                                        
            for idx, exTrade in enumerate(eTrade.exittransactions):
                
                self.df_trades.loc[eTrade.ID,'exit_{}_date'.format(idx)] = exTrade['date']
                self.df_trades.loc[eTrade.ID,'exit_{}_unit'.format(idx)] = exTrade['units']
                self.df_trades.loc[eTrade.ID,'exit_{}_price'.format(idx)] = exTrade['price']
                self.df_trades.loc[eTrade.ID,'exit_{}_realized P&L'.format(idx)] = exTrade['realized P&L']                
                
        now = datetime.datetime.now()
        filename = '{}\\{}_trades.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.df_trades)
    
    def check_equity_curve_trading(self, WindowLenghtList):
        
        # This is for checking how the performance might change if trading stopped 
        # or continued based on equity curve
                
        self.df_temp = pd.DataFrame()
        self.df_temp = self.df_trades.copy()

        for WindowLenght in WindowLenghtList:

            self.df_temp['WindowLength_{}_Accept'.format(WindowLenght)] = 0

            self.df_temp.loc[:,'CumRealizedPips'] = self.df_temp['RealizedPips'].cumsum()
            self.df_temp.loc[:,'AvgCumRealizedPips'] = self.df_temp['CumRealizedPips'].rolling(WindowLenght).mean()
            self.df_temp = self.df_temp.dropna()

            for index, row in self.df_temp[:-1].iterrows():

                if self.df_temp.loc[index, 'CumRealizedPips'] >= self.df_temp.loc[index,'AvgCumRealizedPips']:
                    
                    self.df_temp.loc[index+1, 'WindowLength_{}_Accept'.format(WindowLenght)] = 1

            self.df_temp['FilteredRealizedPips_{}_Accept'.format(WindowLenght)] = self.df_temp['RealizedPips'] * self.df_temp['WindowLength_{}_Accept'.format(WindowLenght)]
            self.df_temp['FilteredCumRealizedPips_{}_Accept'.format(WindowLenght)] =self.df_temp['FilteredRealizedPips_{}_Accept'.format(WindowLenght)].cumsum()
            
            print('For window length of {}, cumulative pips based on filtered trades is {}'.format( WindowLenght, self.df_temp['FilteredCumRealizedPips_{}_Accept'.format(WindowLenght)].iloc[-1]) )
        
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
        
        self.data['normalized_return_ask_h_over_c'] = np.abs( self.data['return_check_ask_h_over_c'] - self.data['return_check_ask_h_over_c'].mean() ) / self.data['return_check_ask_h_over_c'].std()
        self.data['normalized_return_ask_l_over_c'] = np.abs( self.data['return_check_ask_l_over_c'] - self.data['return_check_ask_l_over_c'].mean() ) / self.data['return_check_ask_l_over_c'].std()
        self.data['normalized_return_ask_c_over_c'] = np.abs( self.data['return_check_ask_c_over_c'] - self.data['return_check_ask_c_over_c'].mean() ) / self.data['return_check_ask_c_over_c'].std()

        self.data['normalized_return_bid_h_over_c'] = np.abs( self.data['return_check_bid_h_over_c'] - self.data['return_check_bid_h_over_c'].mean() ) / self.data['return_check_bid_h_over_c'].std()
        self.data['normalized_return_bid_l_over_c'] = np.abs( self.data['return_check_bid_l_over_c'] - self.data['return_check_bid_l_over_c'].mean() ) / self.data['return_check_bid_l_over_c'].std()
        self.data['normalized_return_bid_c_over_c'] = np.abs( self.data['return_check_bid_c_over_c'] - self.data['return_check_bid_c_over_c'].mean() ) / self.data['return_check_bid_c_over_c'].std()

        self.data['outlier_ask_h_over_c'] = np.where( abs(self.data['normalized_return_ask_h_over_c']) > 3, 1, 0)
        self.data['outlier_ask_l_over_c'] = np.where( abs(self.data['normalized_return_ask_l_over_c']) > 3, 1, 0)
        self.data['outlier_ask_c_over_c'] = np.where( abs(self.data['normalized_return_ask_c_over_c']) > 3, 1, 0)

        self.data['outlier_bid_h_over_c'] = np.where( abs(self.data['normalized_return_bid_h_over_c']) > 3, 1, 0)
        self.data['outlier_bid_l_over_c'] = np.where( abs(self.data['normalized_return_bid_l_over_c']) > 3, 1, 0)
        self.data['outlier_bid_c_over_c'] = np.where( abs(self.data['normalized_return_bid_c_over_c']) > 3, 1, 0)
        
        self.data['outlier_any'] = self.data[['outlier_ask_h_over_c','outlier_ask_l_over_c','outlier_ask_c_over_c','outlier_bid_h_over_c','outlier_bid_l_over_c','outlier_bid_c_over_c']].any(axis='columns')

        print('Data Quality:')
        print('Total number of data set is {}'.format( len(self.data) ))
        print('Total number of outliers (exceed 3 std) is {}'.format( len(self.data[self.data['outlier_any'] == True]) )) 
        print('Percentage of outliers in the data set is {0:.2f}%'.format( len(self.data[self.data['outlier_any'] == True]) / len(self.data) * 100 ) ) 
        
        now = datetime.datetime.now()
        filename = '{}\\{}_outliers.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.data)
        
        self.data.drop( ['return_check_ask_h_over_c', 'return_check_ask_l_over_c', 'return_check_ask_c_over_c', 'return_check_bid_h_over_c', 'return_check_bid_l_over_c', 'return_check_bid_c_over_c',
                         #'outlier_ask_h_over_c', 'outlier_ask_l_over_c', 'outlier_ask_c_over_c', 'outlier_bid_h_over_c', 'outlier_bid_l_over_c', 'outlier_bid_c_over_c',
                         'normalized_return_ask_h_over_c', 'normalized_return_ask_l_over_c', 'normalized_return_ask_c_over_c', 'normalized_return_bid_h_over_c', 'normalized_return_bid_l_over_c', 'normalized_return_bid_c_over_c'], axis=1, inplace=True )

    def write_to_excel(self, filename, df):
        
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Sheet1')
        
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()    

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

        print('-' * 55)
        msg = 'Durbin Watson Test:  '
        msg += '\nStatistic: %.4f ' % durbin_watson(ols_res.resid)
        msg += '\nNote:'
        msg += '\nNo serial correlation, the test statistic equals 2.'
        msg += '\nThe closer to 0 the statistic, the more evidence for positive serial correlation.' 
        msg += '\nThe closer to 4, the more evidence for negative serial correlation.'
        print(msg)

    def calculate_number_of_trades_to_simulate(self):
                
        # Calculate the frequency of trades in the backtest
        frequency = (self.data.index[-1] - self.data.index[0]) / self.numberoftrades
        
        # Assume simulation duration for 1 year but given the frequency, it is more important to calculate how many trades to simulate
        return int( pd.Timedelta(value='252D') / frequency )

    def monte_carlo_simulator(self, no_of_simulations=250):
        '''
        Function to simulate trades for a given number of times.
    
        Parameters
        ==========
        rows: int
            number of trades to pick
        no_of_simulations: int
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
        no_of_cols = int(no_of_simulations)
        
        # generate column names
        columns = ['Sim%d' % i for i in range(1, no_of_cols+1, 1)]
        rows = [i for i in range(1, no_of_rows+1, 1)]
        
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
        
            '''
            Temporary calculations to find out max drawdown percent and profit percent
            '''
            self.simulations_df['cumret-strategy_{}'.format(eSim)] = ( self.simulations_df[eSim] / self.initial_equity - 1 )
            self.simulations_df['cumret-max_{}'.format(eSim)] = self.simulations_df['cumret-strategy_{}'.format(eSim)].cummax()
            self.simulations_df['cumret-min_{}'.format(eSim)] = self.simulations_df['cumret-strategy_{}'.format(eSim)].cummin()
            self.simulations_df['drawdown_pct_{}'.format(eSim)] = ( (1+self.simulations_df['cumret-max_{}'.format(eSim)]) - (1+self.simulations_df['cumret-strategy_{}'.format(eSim)]) ) / (1+self.simulations_df['cumret-max_{}'.format(eSim)])
            self.simulations_df.loc[self.simulations_df['drawdown_pct_{}'.format(eSim)] == np.inf, 'drawdown_pct_{}'.format(eSim)] = 0
            
            self.simulations_maxdrawdown_pct.append( self.simulations_df['drawdown_pct_{}'.format(eSim)].max() )
            self.simulations_profit_pct.append( self.simulations_df['cumret-strategy_{}'.format(eSim)].iloc[-1] )

        self.simulations_mean_maxdrawdown_pct = np.mean( self.simulations_maxdrawdown_pct )
        self.simulations_median_maxdrawdown_pct = statistics.median( self.simulations_maxdrawdown_pct )
       
        self.simulations_mean_profit_pct = np.mean( self.simulations_profit_pct )
        self.simulations_median_profit_pct = statistics.median( self.simulations_profit_pct ) 

        '''
        Ideally Calmar ratio should be above 2
        '''
        self.calmar_ratio = self.simulations_median_profit_pct / self.simulations_median_maxdrawdown_pct
        if self.calmar_ratio < 2:
            print("Ideally Calmar ratio should be above 2!")

        print('-' * 55)
        msg = 'Monte Carlo Simulation Results:  '
        msg += '\nMean Max Drawdown Percent:   %.2f ' % (self.simulations_mean_maxdrawdown_pct*100)
        msg += '\nMedian Max Drawdown Percent: %.2f ' % (self.simulations_median_maxdrawdown_pct*100)
        msg += '\nMean Profit Percent:         %.2f ' % (self.simulations_mean_profit_pct*100)
        msg += '\nMedian Profit Percent:       %.2f ' % (self.simulations_median_profit_pct*100)
        msg += '\nCalmar Ratio                %.4f  ' % self.calmar_ratio
        print(msg)

        self.calculate_quantiles_from_MonteCarlo(columns)
        self.plot_quantiles_from_MonteCarlo()

        for eSim in columns:
            '''
            Delete temporary calculations
            '''            
            del self.simulations_df['cumret-strategy_{}'.format(eSim)]
            del self.simulations_df['cumret-max_{}'.format(eSim)]
            del self.simulations_df['cumret-min_{}'.format(eSim)]
            del self.simulations_df['drawdown_pct_{}'.format(eSim)]

        self.calculate_risk_of_ruin(no_of_simulations)

        self.simulations_df['mean'] = self.simulations_df.mean(axis=1)
        self.simulations_df['mean'].plot(title='Mean Equity vs Trades')

    def calculate_quantiles_from_MonteCarlo(self, columns):
        '''
        Calculate quantiles for returns
        '''
        sim_column_names = ['cumret-strategy_{}'.format(eSim) for eSim in columns]
        quantiles = [5, 10, 25, 50, 75, 90, 95]
        self.quantile_columns = []
        self.simulations_df_quantiles = pd.DataFrame()
        for q in quantiles:
            self.quantile_columns.append('quantile_{}'.format(q))
            self.simulations_df_quantiles['quantile_{}'.format(q)]  = self.simulations_df[sim_column_names].quantile(q=q/100, axis=1)
    
    def plot_quantiles_from_MonteCarlo(self):

        plt.title('Quantiles Based on Monte Carlo Simulations')
        self.simulations_df_quantiles[self.quantile_columns].plot()
        plt.savefig('{}\\Quantiles_Based_on_Mone_Carlo_Simulations.pdf'.format(self.backtest_folder))
        plt.show()
        plt.close()
    
    def calculate_risk_of_ruin(self, no_of_simulations):

        columns = ['Sim%d' % i for i in range(1, no_of_simulations+1, 1)]

        self.dict_risk_of_ruin = {}
        
        print("Risk of Ruin:")
        
        for e_threshold in np.arange(0.05, 0.95, 0.05):
            threshold = self.initial_equity * e_threshold
            
            total_cases_of_ruin = 0.0
            for eSim in columns:
                if (self.simulations_df[eSim]<threshold).any() == True:
                    total_cases_of_ruin = total_cases_of_ruin + 1.0
        
            self.dict_risk_of_ruin[(1-e_threshold)] = (total_cases_of_ruin / no_of_simulations)
        
            print("Risk of losing {:0.0%} of initial equity within 1 year is {:0.2%}".format((1-e_threshold), (total_cases_of_ruin / no_of_simulations) ) )

        print('-' * 55)                        

        df_temp = pd.DataFrame(data=self.dict_risk_of_ruin, index=[0])
        filename = '{}\\{}_risk_of_ruin_results.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, df_temp)
        
    def write_monte_carlo_simulation_results_to_excel(self):

        now = datetime.datetime.now()
        filename = '{}\\{}_monte_carlo_simulation_results.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.simulations_df)
        
    def analyze_trades(self):
        
        '''
        Purpose is to collect stats from closed trades. This procedure collects P/L for each trade for each
        time period .
        '''
        self.trade_performance_over_time = pd.DataFrame()

        for eTrade in self.listofClosedTrades:
        
            for i in range( 1, len(eTrade.stat_unrealizedprofitloss)+1 ):
                
                self.trade_performance_over_time.loc[eTrade.ID, i] = eTrade.stat_unrealizedprofitloss[i-1]
        
        filename = '{}\\{}_trades_performance_over_time.xlsx'.format(self.backtest_folder,self.symbol)
        self.write_to_excel(filename, self.trade_performance_over_time)

    def calculate_average_number_of_bars_before_profitability(self):
        '''
        Calculate how many time periods it typically takes to become profitable
        '''
        self.periods_before_profitable = {}
        self.periods_before_profitable_list = []

        for eTrade in self.listofClosedTrades:
        
            temp = self.trade_performance_over_time.loc[eTrade.ID, :]
            
            self.periods_before_profitable[eTrade.ID] = 0
                
            for i in range(1,len(temp)+1):
                
                if temp[i] > 0:
                    
                    self.periods_before_profitable[eTrade.ID] = i
                    break
                 
            if self.periods_before_profitable[eTrade.ID] == 0:
                
                self.periods_before_profitable[eTrade.ID] = len(temp)
                
            self.periods_before_profitable_list.append(self.periods_before_profitable[eTrade.ID])
                            
        self.periods_before_profitable_list_filtered = list(filter(lambda a: a < 24, self.periods_before_profitable_list))
        
        print('Mean number of periods:', mean(self.periods_before_profitable_list))
        num_bins = 24 
        plt.hist(self.periods_before_profitable_list, num_bins)
        plt.title('Number of periods before trades turn profitable')
        plt.ylabel('Frequency')
        plt.xlabel('Number of periods')
        plt.savefig('{}\\Periods_before_profitable.pdf'.format(self.backtest_folder))
        plt.close()
        
        print('Mean number of periods (trade length < 24):', mean(self.periods_before_profitable_list_filtered))
        num_bins = 24 
        plt.hist(self.periods_before_profitable_list_filtered, num_bins)
        plt.title('Number of periods before trades turn profitable (trade length < 24)')
        plt.ylabel('Frequency')
        plt.xlabel('Number of periods')
        plt.savefig('{}\\Periods_before_profitable_short.pdf'.format(self.backtest_folder))
        plt.close()
        
if __name__ == '__main__':

     symbol = 'EUR_USD'
     account_type = 'backtest'
     granularity = '1H'
     decision_frequency = '1H'
     start_datetime = datetime.datetime(2019,1,1,0,0,0)
     end_datetime = datetime.datetime.now()
     idle_duration_before_start_trading = pd.Timedelta(value='0D')     
     initial_equity = 10000
     marginpercent = 100
     #WindowLenght = 12
    
     bb = backtest_base(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent)
     #bb.check_data_quality()

     #viz.visualize(bb.symbol, bb.data, sorted(bb.listofClosedTrades, key=lambda k: k.ID), False)
     
    