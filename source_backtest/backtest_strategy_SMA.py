from backtest_base import *

class backtest_strategy_SMA(backtest_base):

    def add_indicators(self, SMA1, SMA2):

        self.data, self.indicatorlist = AddSMA( self.data, self.indicatorlist, 'bid', 'c', SMA2)
        self.data, self.indicatorlist = AddSMA( self.data, self.indicatorlist, 'bid', 'c', SMA1)
        self.data = self.data.dropna()

    def go_long(self, date, units):
        self.open_long_trade(units, date=date)
            
    def go_short(self, date, units):
        self.open_short_trade(units, date=date)

    def run_strategy(self, SMA1, SMA2):
    
        self.add_indicators(SMA1, SMA2)

        self.data = self.data.loc[(self.data.index >= self.date_to_start_trading) & (self.data.index <= self.end),:]

        print('-' * 55)
        msg = '\n\nRunning SMA strategy | SMA1 = %d & SMA2 = %d' % (SMA1, SMA2)
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        print('-' * 55)
        
        for date, _ in self.data.iterrows():

            ''' 
            Get signal
            Create buy/sell order
            -	Calculate PL
            -	Calculate required margin
            Check all open orders
            - 	Either add to the list
            -	Or eliminate some from list, move to ListofClosedOrders
            '''
            #self.run_core_strategy()
        
            if self.units_net == 0:
                if self.data.loc[date,'SMA_14_bid_c'] > self.data.loc[date,'SMA_28_bid_c']:
                    self.go_long(date=date, units=1000)
                elif self.data.loc[date,'SMA_14_bid_c'] < self.data.loc[date,'SMA_28_bid_c']:
                    self.go_short(date=date, units=1000)

            elif self.units_net > 0:
                if self.data.loc[date,'SMA_14_bid_c'] < self.data.loc[date,'SMA_28_bid_c']:
                    self.go_short(date=date, units=2000)
            
            elif self.units_net < 0:
                if self.data.loc[date,'SMA_14_bid_c'] > self.data.loc[date,'SMA_28_bid_c']:
                    self.go_long(date=date, units=2000)
                                
            self.update(date)
                
        self.close_all_trades(date)
        self.update(date)
        self.close_out()
                
if __name__ == '__main__':

     symbol = 'EUR_USD'
     account_type = 'backtest'
     granularity = '1H'
     decision_frequency = '1H'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2018,1,1,0,0,0)
     idle_duration_before_start_trading = pd.Timedelta(value='30D')     
     initial_equity = 10000
     marginpercent = 100
     
     # A standard lot = 100,000 units of base currency. 
     # A mini lot = 10,000 units of base currency.
     # A micro lot = 1,000 units of base currency.

     bb = backtest_strategy_SMA(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, True)
     bb.verbose = True
     #bb.check_data_quality()

     bb.run_strategy(14, 28)
     
     bb.calculate_stats()
     
     bb.plot()
     
     bb.write_all_data()
     
     bb.write_all_trades_to_excel()

     bb.monte_carlo_simulator(250)
     
     bb.write_monte_carlo_simulation_results_to_excel()
 
     viz.visualize(bb.symbol, bb.data, bb.listofClosedTrades)