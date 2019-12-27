from backtest_base import *

class backtest_strategy_Divergence(backtest_base):

    def add_indicators(self):

        self.data, self.indicatorlist = AddSlowStochastic(self.data, self.indicatorlist, 'bid', fastk_period=14, slowk_period=3, slowd_period=3)
        self.data = self.data.dropna()
         
        self.data, self.indicatorlist = AddPivotPoints(self.data, self.indicatorlist, 'bid', rightstrength=1, leftstrength=10)
        self.data = self.data.dropna()
        
        self.data, self.indicatorlist = AddMinorHighLow(self.data, self.indicatorlist, 'bid')
        self.data = self.data.dropna()
            
        self.data, self.indicatorlist = AddDivergence(self.data, self.indicatorlist, 'bid', lookback=24, threshold=0.0010)

    def buy(self, date, units):

        self.open_long_trade(units=10000, date=date)
            
    def sell(self, date, units):

        self.open_short_trade(units=-10000, date=date)
    
    def run_strategy(self):

        self.add_indicators()

        print('=' * 55)
        msg = 'Running Divergence strategy'
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

            #self.close_short_trades(date=date)
            #self.close_long_trades(date=date)
        
            '''
            if self.data.loc[date,'divergenceregularbuy'] == 1:
                self.buy(date=date, units=10000)

            if self.data.loc[date,'divergencehiddenbuy'] == 1:
                self.sell(date=date, units=-10000)
            '''
            
            if self.data.loc[date,'divergenceregularbuy'] >= 1:
                self.buy(date=date, units=10000)

            if self.data.loc[date,'divergencehiddenbuy'] >= 1:
                self.buy(date=date, units=10000)

            if self.data.loc[date,'divergenceregularsell'] >= 1:
                self.sell(date=date, units=-10000)

            if self.data.loc[date,'divergencehiddensell'] >= 1:
                self.sell(date=date, units=-10000)
            
            '''
                Divergence signal
                divergenceregularbuy	divergencehiddenbuy	divergenceregularsell	divergencehiddensell
                Then add swing or pivot points
            
            '''            
            self.update(date)
        
        self.close_all_trades(date)
        self.update(date)
        self.close_out()
            
if __name__ == '__main__':

     symbol = 'EUR_USD'
     account_type = 'live'
     granularity = 'S5'
     decision_frequency = '1H'
#     decision_frequency = '1T'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2017,12,31,0,0,0)
     marginpercent = 100
     verbose = False
     
     bb = backtest_strategy_Divergence(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, 10000, marginpercent, verbose)

     bb.run_strategy()
     
     bb.analyze_trades()
     
     bb.calculate_average_number_of_bars_before_profitability()
     
     write2excel( bb.data, 'output' )
         
     viz.visualize(bb.symbol, bb.data, sorted(bb.listofClosedTrades, key=lambda k: k.ID), False)
     
     
     
     