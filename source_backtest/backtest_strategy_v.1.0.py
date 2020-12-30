from backtest_base import *

class backtest_strategy_v_1_0(backtest_base):

    def go_long(self, date, units):
        self.open_long_trade(units, date=date)
            
    def go_short(self, date, units):
        self.open_short_trade(units, date=date)

    def calculate_price_distribution(self, date):
        
        data = self.data[self.data_granularity[0]]
        data_filtered = data.loc[(data.index <= date) & (data.index >= date-datetime.timedelta(days=0, hours=1, minutes=0)), :]
                
        self.data[self.decision_frequency].loc[date, 'mean_bid_c'] = data_filtered['bid_c'].mean()
        self.data[self.decision_frequency].loc[date, 'std_bid_c'] = data_filtered['bid_c'].std()
        self.data[self.decision_frequency].loc[date, 'bid_ask_spread'] = data_filtered.iloc[-1:, data_filtered.columns.get_loc('bid_c')].values[0] - data_filtered.iloc[-1:, data_filtered.columns.get_loc('ask_c')].values[0]
        self.data[self.decision_frequency].loc[date, 'std / bid_ask_spread'] = np.abs( self.data[self.decision_frequency].loc[date, 'std_bid_c'] / self.data[self.decision_frequency].loc[date, 'bid_ask_spread'] )
                                
    def run_strategy(self):

#       try: 
            
        for e_granularity in self.data_granularity:
            self.data[e_granularity] = self.data[e_granularity].loc[(self.data[e_granularity].index >= self.start_date) & (self.data[e_granularity].index <= self.end_date),:]
                
        print('-' * 55)
        msg = 'Running strategy v.1.0'
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        
        for date, _ in self.data[self.decision_frequency].iterrows():
            
            if date >=self.date_to_start_trading:

                print('Date: ', date)
                self.calculate_price_distribution(date)
    
                ''' 
                Get signal
                Create buy/sell order
                -	Calculate PL
                -	Calculate required margin
                Check all open orders
                - 	Either add to the list
                -	Or eliminate some from list, move to ListofClosedOrders
                '''
                                                            
                self.update(date)
            
        filename = os.path.join( self.backtest_folder, 'data.xlsx')
        self.data[self.decision_frequency].to_excel(filename)
            
        '''                
        self.close_all_trades(date)
        self.update(date)
        self.close_out()

        self.calculate_stats()
        '''

#        except:
            
#            print("error!!!!!!")
            
if __name__ == '__main__':
    
     cwd = os.path.dirname(__file__)
     os.chdir(cwd)

     symbol = 'EUR_USD'
     account_type = 'backtest'
     granularity = ['1M']
     decision_frequency = '1H'
     granularity.append(decision_frequency)
     start_datetime = datetime.datetime(2020,12,1,0,0,0)
     end_datetime = datetime.datetime(2021,1,1,0,0,0)
     idle_duration_before_start_trading = datetime.timedelta(days=0, hours=1, minutes=0)
     initial_equity = 10000
     marginpercent = 100
     ftc=0.0
     ptc=0.0
     verbose=True
     create_data=False
     
     # A standard lot = 100,000 units of base currency. 
     # A mini lot = 10,000 units of base currency.
     # A micro lot = 1,000 units of base currency.

     bb = backtest_strategy_v_1_0(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)
     #bb.check_data_quality()

     bb.run_strategy()
     
     #bb.plot()
     '''
     filename = '{}_data.xlsx'.format(bb.symbol)
     uf.write_df_to_excel(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
     
     filename = '{}_data.pkl'.format(bb.symbol)
     uf.pickle_df(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
             
     bb.write_all_trades_to_excel()
     
     bb.monte_carlo_simulator(250)
 
     viz.visualize(bb.symbol, bb.data[bb.decision_frequency], bb.listofClosedTrades)
     
     bb.analyze_trades()
     
     bb.calculate_average_number_of_bars_before_profitability()
     '''
     