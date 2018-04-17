from backtest_base import *

class backtest_strategy_SMA(backtest_base):

    def add_indicators(self, SMA1, SMA2):

        self.data, self.indicatorlist = AddSMA( self.data, self.indicatorlist, 'bid', 'c', SMA2)
        self.data, self.indicatorlist = AddSMA( self.data, self.indicatorlist, 'bid', 'c', SMA1)
        self.data = self.data.dropna()

    def go_long(self, date, units):
        self.close_short_trades(date=date)
        self.open_long_trade(units, date=date)
            
    def go_short(self, date, units):
        self.close_long_trades(date=date)
        self.open_short_trade(units, date=date)

    def run_strategy(self, SMA1, SMA2):

        self.add_indicators(SMA1, SMA2)

        msg = '\n\nRunning SMA strategy | SMA1 = %d & SMA2 = %d' % (SMA1, SMA2)
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        print('=' * 55)
                    
        for date, _ in self.data.iterrows():
    
            ''' Get signal
                Create buy/sell order
                -	Calculate PL
                -	Calculate required margin
                Check all open orders
                	Either add to the list
                	Eliminate some from list, move to ListofClosedOrders
            '''
            
            if self.units_net > 0:
                if self.data.loc[date,'SMA_14_bid_c'] < self.data.loc[date,'SMA_28_bid_c']:
                    self.go_short(date=date, units=-10000)
            
            elif self.units_net < 0:
                if self.data.loc[date,'SMA_14_bid_c'] > self.data.loc[date,'SMA_28_bid_c']:
                    self.go_long(date=date, units=10000)

            elif self.units_net == 0:
                if self.data.loc[date,'SMA_14_bid_c'] > self.data.loc[date,'SMA_28_bid_c']:
                    self.go_long(date=date, units=10000)
                elif self.data.loc[date,'SMA_14_bid_c'] < self.data.loc[date,'SMA_28_bid_c']:
                    self.go_short(date=date, units=-10000)

            self.update(date)
        
        self.close_all_trades(date)
        self.update(date)
        self.close_out()
            
if __name__ == '__main__':

     symbol = 'EUR_USD'
     account_type = 'practice'
     granularity = 'S5'
     decision_frequency = '1H'
#     decision_frequency = '1T'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2017,8,1,0,0,0)
     marginrate = 0.01
     
     # A standard lot = 100,000 units of base currency. 
     # A mini lot = 10,000 units of base currency.
     # A micro lot = 1,000 units of base currency.

     bb = backtest_strategy_SMA(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, 10000, marginrate)
     bb.verbose = True
     bb.run_strategy(14, 28)
     
     bb.calculate_stats()
     #bb.plot()

#     visualize(bb.symbol, bb.data, bb.listofClosedTrades)
     # write2excel( bb.data, 'output' )
    
    