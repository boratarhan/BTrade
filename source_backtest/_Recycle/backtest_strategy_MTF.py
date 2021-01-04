from backtest_base import *

sys.path.append('..\\source_system')
from visualize_strategy_MTF import *
sys.path.remove('..\\source_system')

ohlc_dict = { 'ask_o':'first', 'ask_h':'max', 'ask_l':'min', 'ask_c': 'last',                                                                                                    
              'bid_o':'first', 'bid_h':'max', 'bid_l':'min', 'bid_c': 'last',
              'volume': 'sum'                                                                                                        
            }

class backtest_strategy_MTF(backtest_base):

    def __init__(self, symbol, account_type, granularity, decision_frequency, start, end, amount, marginrate, ftc=0.0, ptc=0.0):
        super().__init__(symbol, account_type, granularity, decision_frequency, start, end, amount, marginrate, ftc=0.0, ptc=0.0)
        self.temp = 0

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

        read_data = False
        
        if read_data:

            self.data_1H = read_hdf_file('data_1H')
            self.data_4H = read_hdf_file('data_4H')

        else:
            
            self.define_multiple_timeframes()
            self.data_1H = self.add_indicators_1H(self.data_1H)
            self.data_4H = self.add_indicators_4H(self.data_4H)
            write_hdf_file(self.data_1H, 'data_1H')
            write_hdf_file(self.data_4H, 'data_4H')
        
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
            self.run_core_strategy(date)

        self.close_all_trades(date)
        self.update(date)
        self.close_out()

        self.merge_different_timeframes()

        

    def define_multiple_timeframes(self):

        print('Define multiple timeframes')
        self.data_1H = self.data.resample('1H', closed='left', label='left').apply(ohlc_dict).dropna()
        self.data_1H = self.data_1H[['bid_o','bid_h','bid_l','bid_c','volume']]
        self.data_1H = self.data_1H.reset_index()
        self.data_1H = self.data_1H.rename(columns={'index': 'date'})
        self.data_1H = self.data_1H.set_index('date')

        self.data_4H = self.data.resample('4H', closed='left', label='left').apply(ohlc_dict).dropna()
        self.data_4H = self.data_4H[['bid_o','bid_h','bid_l','bid_c','volume']]
        self.data_4H = self.data_4H.reset_index()
        self.data_4H = self.data_4H.rename(columns={'index': 'date'})
        self.data_4H = self.data_4H.set_index('date')
        
    def add_indicators_1H(self, df):

        print('Add indicators for 1H')

        df = df.reset_index()
        df = df.rename(columns={'index': 'date'})
        df, self.indicatorlist = AddWave( df, self.indicatorlist, 'bid', 23)
        df, self.indicatorlist = AddMACD( df, self.indicatorlist, 'bid', fastperiod=12, slowperiod=26, signalperiod=9)
        df, self.indicatorlist = AddSlowStochastic( df, self.indicatorlist, 'bid', fastk_period=14, slowk_period=3, slowd_period=3)
        df, self.indicatorlist = AddMACD( df, self.indicatorlist, 'bid', fastperiod=12, slowperiod=26, signalperiod=9)
        df, self.indicatorlist = AddDivergence( df, self.indicatorlist, 'bid', lookback=24, threshold=0.02)
        df, self.indicatorlist = VolumeWeightedPrice( df, self.indicatorlist, 'bid', lookback=12)
        df = df.dropna()
        df = df.set_index('date')
        return df

    def add_indicators_4H(self, df):

        print('Add indicators for 4H')
                     
        df = df.reset_index()
        df = df.rename(columns={'index': 'date'})
        df, self.indicatorlist = AddWave( df, self.indicatorlist, 'bid', 23)
        df, self.indicatorlist = AddMACD( df, self.indicatorlist, 'bid', fastperiod=12, slowperiod=26, signalperiod=9)
        df, self.indicatorlist = AddWaveAngle( df, self.indicatorlist, derivativelength=3)
        df, self.indicatorlist = AddATR( df, self.indicatorlist, 'bid', timeperiod=34)

        df['long_term_filter'] = 0
        df.loc[(df['macdhist'].shift(1) > df['macdhist'].shift(2)) & (df['waveangle'].shift(1)>0), 'long_term_filter'] = 1
        df.loc[(df['macdhist'].shift(1) < df['macdhist'].shift(2)) & (df['waveangle'].shift(1)<0), 'long_term_filter'] = -1

        df = df.dropna()
        df = df.set_index('date')
        return df
        
    def merge_different_timeframes(self):

        #This section merges two dataframes over dates and fills foward missing long_term_filter data in higher frequency data.     
        
        temp_1H = self.data_1H.reset_index()
        temp_1H = temp_1H.rename(columns={'index': 'date'})
        
        temp_4H = self.data_4H
        temp_4H = temp_4H['long_term_filter']
        temp_4H = temp_4H.reset_index()
        temp_4H = temp_4H.rename(columns={'index': 'date'})

        self.data_1H_final = pd.DataFrame()
        self.data_1H_final = pd.merge(left=temp_1H, right=temp_4H, how='left', on='date')
        self.data_1H_final = self.data_1H_final.fillna(method='ffill')
        self.data_1H_final = self.data_1H_final.set_index('date')
        
        write_hdf_file(self.data_1H_final, 'data_1H_final')


    def run_core_strategy(self,date):

        available_data_1H = len(self.data_1H[ self.data_1H.index <= date ].copy())
        available_data_4H = len(self.data_4H[ self.data_4H.index <= date ].copy())
        
#        print(available_data_1H)
#        print(available_data_4H)

        if available_data_1H >= 1 and available_data_4H >= 1:
        
            temp_1H = self.data_1H[ self.data_1H.index <= date ].copy()[-35:]
            temp_4H = self.data_4H[ self.data_4H.index <= date ].copy()[-35:]

#            print(temp_1H[-1:])
#            print(temp_4H[-1:])

#                if self.units_net > 0:
#                    #self.go_short(date=date, units=-10000)
#                    self.close_long_trades(date=date)                
#
#                elif self.units_net < 0:
#                    #self.go_long(date=date, units=10000)
#                    self.close_short_trades(date=date)                
#    
#                elif self.units_net == 0:
#                    if ( self.data_1H_final.loc[date,'slowk'] < 30 ) and ( self.data_4H.iloc[-2]['long_term_filter'] >=0 ) :
#                        #self.go_long(date=date, units=10000)
#                        self.open_long_trade(units=10000, date=date)
#
#                    elif ( self.data_1H_final.loc[date,'slowk'] > 70 ) and ( self.data_4H.iloc[-2]['long_term_filter'] <=0 ) :
#                        #self.go_short(date=date, units=-10000)
#                        self.open_short_trade(units=-10000, date=date)

    def go_long(self, date, units):
        self.close_short_trades(date=date)
        self.open_long_trade(units, date=date)
            
    def go_short(self, date, units):
        self.close_long_trades(date=date)
        self.open_short_trade(units, date=date)
                
if __name__ == '__main__':

     symbol = 'USD_TRY'
     account_type = 'practice'
     granularity = 'S5'
     decision_frequency = '1H'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2017,8,1,0,0,0)
     marginrate = 0.01
     
     # A standard lot = 100,000 units of base currency. 
     # A mini lot = 10,000 units of base currency.
     # A micro lot = 1,000 units of base currency.

     bb = backtest_strategy_MTF(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, 10000, marginrate)
     bb.verbose = True
     bb.run_strategy()


    
     visualize_1H(bb.symbol, bb.listofClosedTrades, bb.data_1H_final )
     visualize_4H(bb.symbol, bb.listofClosedTrades, bb.data_4H )

