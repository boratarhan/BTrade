from backtest_base import *

ohlc_dict = { 'ask_o':'first', 'ask_h':'max', 'ask_l':'min', 'ask_c': 'last',                                                                                                    
              'bid_o':'first', 'bid_h':'max', 'bid_l':'min', 'bid_c': 'last',
              'volume': 'sum'                                                                                                        
            }

class backtest_ML_prep(backtest_base):

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

            file_path_h5 = '_{}\\{}\\H1.h5'.format(account_type, symbol)
            self.data_1H = read_hdf_file(file_path_h5)
            file_path_h5 = '_{}\\{}\\H4.h5'.format(account_type, symbol)
            self.data_4H = read_hdf_file(file_path_h5)

        else:
            
            self.define_multiple_timeframes()
#            self.data_1H = self.add_indicators_1H(self.data_1H)
            self.data_4H = self.add_indicators_4H(self.data_4H)

#            file_path_h5 = '_backtest\\{}\\H1.h5'.format(symbol)
#            write_hdf_file(self.data_1H, file_path_h5)
            file_path_h5 = '_backtest\\{}\\H4.h5'.format(symbol)
            write_hdf_file(self.data_4H, file_path_h5)

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
                        
if __name__ == '__main__':

     symbol = 'USD_TRY'
     account_type = 'practice'
     granularity = 'S5'
     decision_frequency = '4H'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2017,8,1,0,0,0)
     marginrate = 0.01
     
     # A standard lot = 100,000 units of base currency. 
     # A mini lot = 10,000 units of base currency.
     # A micro lot = 1,000 units of base currency.

     bb = backtest_ML_prep(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, 10000, marginrate)
     bb.run_strategy()
