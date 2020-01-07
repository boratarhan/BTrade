from backtest_base import *

class backtest_strategy_volatility(backtest_base):

    def add_indicators(self, WindowLenght):
    
        self.data.loc[:,'H-L'] = self.data.loc[:,'bid_h']-self.data.loc[:,'bid_l']
        self.data.loc[:,'cum-move'] = self.data['H-L'].rolling(WindowLenght+1).sum()
        self.data.loc[:,'net-move'] = np.abs(self.data['bid_c'] - self.data['bid_c'].shift(WindowLenght))
        self.data.loc[:,'ratio-move'] = self.data.loc[:,'net-move'] / self.data.loc[:,'cum-move']

        self.data.loc[:,'max-range'] = self.data['bid_c'].rolling(WindowLenght+1).max()
        self.data.loc[:,'min-range'] = self.data['bid_c'].rolling(WindowLenght+1).min()
        self.data.loc[:,'mid-range'] = ( self.data.loc[:,'max-range'] + self.data.loc[:,'min-range'] ) / 2
        
        self.data, self.indicatorlist = AddWave( self.data, self.indicatorlist, 'bid', 34)
        self.data, self.indicatorlist = AddATR( self.data, self.indicatorlist, 'bid', 14, 3)
        self.data, self.indicatorlist = AddADX( self.data, self.indicatorlist, 'bid', 14 )
        self.data, self.indicatorlist = AddROC( self.data, self.indicatorlist, 'bid', 14)
        self.data, self.indicatorlist = AddNormalizedROC( self.data, self.indicatorlist, 'bid', 14, 25)
        
        self.data, self.indicatorlist = Add_CDLDOJISTAR( self.data, self.indicatorlist, 'bid')
        
        self.data = self.data.dropna()

    def run_strategy(self, WindowLenght):

        self.add_indicators(WindowLenght)

        print('=' * 55)
        msg = 'Running volatility strategy | WindowLength = %d' % (WindowLenght)
        msg += '\nFixed costs %.2f | ' % self.ftc
        msg += 'proportional costs %.4f' % self.ptc
        print(msg)
        print('=' * 55)
        
        for date, _ in self.data.iterrows():

            if(date >= self.date_to_start_trading):
                        
                #print(date, self.data.loc[date,'net-move'], self.data.loc[date,'cum-move'])
                ''' Get signal
                    Create buy/sell order
                    -	Calculate PL
                    -	Calculate required margin
                    Check all open orders
                    	Either add to the list
                    	Eliminate some from list, move to ListofClosedOrders
                '''
                
                if self.units_net != 0:

                    '''
                    if self.data.loc[date,'bid_c'] < self.data.loc[date,'atr-2']:
                        
                        self.close_all_trades(date)

                    elif self.data.loc[date,'bid_c'] > self.data.loc[date,'atr+2']:
                        
                        self.close_all_trades(date)
                    '''
                    
                    for etrade in self.listofOpenTrades:
                        
                        if(etrade.unrealizedprofitloss) > .5:
                            
                            self.close_all_trades(date)

                        if(etrade.unrealizedprofitloss) <= -10:

                            self.close_all_trades(date)
                    '''
                    for etrade in self.listofOpenTrades:
                    
                        if etrade.units > 0:
                            
                            if self.data.loc[date,'bid_c'] > self.data.loc[date,'atr+3']:
                                
                                self.close_all_trades(date)
                    
                            elif self.data.loc[date,'bid_c'] < self.data.loc[date,'atr-3']:
                                
                                self.close_all_trades(date)
                                
                        elif etrade.units < 0:

                            if self.data.loc[date,'bid_c'] > self.data.loc[date,'atr+3']:

                                self.close_all_trades(date)

                            elif self.data.loc[date,'bid_c'] < self.data.loc[date,'atr-3']:

                                self.close_all_trades(date)
                        
                        else:
                            
                            pass
                    '''
                    
                elif self.units_net == 0:
                     
                    if self.data.loc[date,'adx'] <= 25:
                    #if self.data.loc[date,'net-move'] < 0.001 and self.data.loc[date,'cum-move'] > 0.02:
                    #if self.data.loc[date,'ratio-move'] < 0.11:
   
                        if self.data.loc[date,'bid_c'] < self.data.loc[date,'mid-range']:
                            self.open_long_trade(1000, date)
                        else:
                            self.open_short_trade(-1000, date)

                        '''
                        if np.random.random() >= 0.5:  
                            self.open_long_trade(1000, date)
                        else:
                            self.open_short_trade(-1000, date)
                        '''
                        
            self.update(date)

        self.close_all_trades(date)
        self.update(date)
        self.close_out()

if __name__ == '__main__':

     symbol = 'EUR_USD'
     account_type = 'practice'
     granularity = '1M'
     decision_frequency = '1H' # For 1 minute use '1T'
     start_datetime = datetime.datetime(2010,1,1,0,0,0)
     end_datetime = datetime.datetime.now()
     margin_duration_before_start_trading = pd.Timedelta(value='0D')     
     marginpercent = 100
     WindowLenght = 12
     
     bb = backtest_strategy_volatility(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, margin_duration_before_start_trading, 10000, marginpercent)
    
     bb.verbose = True
     #bb.check_data_quality()
     #bb.data = bb.data[:10000]
     
     bb.run_strategy(WindowLenght)
      
     bb.calculate_stats()
     
     '''    
     bb.plot()
     '''

     bb.write_all_data()
     
     bb.write_all_trades_to_excel()

     '''
     bb.monte_carlo_simulator(250)
     
     bb.write_all_simulation_data_to_excel()
 
     viz.visualize(bb.symbol, bb.data, bb.listofClosedTrades)
     '''
     