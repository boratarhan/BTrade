from backtest_base import *

class backtest_strategy_SMA(backtest_base):

    def add_indicators(self, SMA1, SMA2):

        self.data[self.decision_frequency], self.indicatorlist = AddSMA( self.data[self.decision_frequency], self.indicatorlist, 'bid', 'c', SMA2)
        self.data[self.decision_frequency], self.indicatorlist = AddSMA( self.data[self.decision_frequency], self.indicatorlist, 'bid', 'c', SMA1)
        self.data[self.decision_frequency] = self.data[self.decision_frequency].dropna()

    def go_long(self, date, units):
        self.open_long_trade(units, date=date)
            
    def go_short(self, date, units):
        self.open_short_trade(units, date=date)

    def run_strategy(self, SMA1, SMA2):
    
        self.add_indicators(SMA1, SMA2)

        self.data[self.decision_frequency] = self.data[self.decision_frequency].loc[(self.data[self.decision_frequency].index >= self.date_to_start_trading) & (self.data[self.decision_frequency].index <= self.end_date),:]

        print('-' * 55)
        msg = 'Running SMA strategy | SMA1 = %d & SMA2 = %d' % (SMA1, SMA2)
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        
        for date, _ in self.data[self.decision_frequency].iterrows():

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

            if self.data[self.decision_frequency].loc[date,'SMA_{}_bid_c'.format(SMA2)] > self.data[self.decision_frequency].loc[date,'SMA_{}_bid_c'.format(SMA1)]:
                self.go_short(date=date, units=10000)
            elif self.data[self.decision_frequency].loc[date,'SMA_{}_bid_c'.format(SMA2)] < self.data[self.decision_frequency].loc[date,'SMA_{}_bid_c'.format(SMA1)]:
                self.go_long(date=date, units=10000)
                                
            self.update(date)
            
        self.close_all_trades(date)
        self.update(date)
        self.close_out()

        self.calculate_stats()
                
if __name__ == '__main__':

     symbol = 'EUR_USD'
     account_type = 'backtest'
     granularity = ['1M']
     decision_frequency = '1M'
     granularity.append(decision_frequency)
     start_datetime = datetime.datetime(2020,12,24,4,35,0)
     end_datetime = datetime.datetime(2021,1,1,0,0,0)
     idle_duration_before_start_trading = datetime.timedelta(days=0, hours=0, minutes=5)
     initial_equity = 10000
     marginpercent = 100
     ftc=0.0
     ptc=0.0
     verbose=True
     create_data=False
     
     # A standard lot = 100,000 units of base currency. 
     # A mini lot = 10,000 units of base currency.
     # A micro lot = 1,000 units of base currency.

     bb = backtest_strategy_SMA(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)
     #bb.check_data_quality()

     bb.run_strategy(3, 5)
     
     #bb.plot()
     
     filename = '{}_data.xlsx'.format(bb.symbol)
     uf.write_df_to_excel(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
     
     filename = '{}_data.pkl'.format(bb.symbol)
     uf.pickle_df(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
             
     bb.write_all_trades_to_excel()
     
     bb.monte_carlo_simulator(250)
 
     viz.visualize(bb.symbol, bb.data[bb.decision_frequency], bb.listofClosedTrades)
     
     bb.analyze_trades()
     
     bb.calculate_average_number_of_bars_before_profitability()
     