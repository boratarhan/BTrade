from backtest_base import *

class backtest_strategy_SMA(backtest_base):

    def add_indicators(self):

        self.data, self.indicatorlist = AddSlowStochastic(self.data, self.indicatorlist, 'bid', fastk_period=14, slowk_period=3, slowd_period=3)
        self.data = self.data.dropna()
         
        self.data, self.indicatorlist = AddPivotPoints(self.data, self.indicatorlist, 'bid', rightstrength=1, leftstrength=5)
        self.data = self.data.dropna()
        
        #self.data, self.indicatorlist = AddDivergence( self.data, self.indicatorlist, 'bid', 24, 0.0020)

    def go_long(self, date, units):

        pass
            
    def go_short(self, date, units):

        pass
    
    def run_strategy(self):

        self.add_indicators()

        msg = '\n\nRunning Divergence strategy'
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
     marginpercent = 100
     
     bb = backtest_strategy_SMA(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, 10000, marginpercent)
     bb.verbose = True
     bb.run_strategy()
     
     write2excel( bb.data, 'output' )
         
    
