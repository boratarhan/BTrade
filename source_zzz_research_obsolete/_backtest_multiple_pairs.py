# -*- coding: utf-8 -*-
from backtest_base import *
from backtest_strategy_SMA_14_28 import *

#list_pairs = ['AUD_USD', 'EUR_USD', 'GBP_USD', 'NZD_USD', 'USD_CAD', 'USD_CHF', 'USD_JPY', 'USD_TRY', 'AUD_NZD', 'EUR_CHF', 'AUD_JPY' ]
list_pairs = ['EUR_USD', 'GBP_USD', 'NZD_USD', 'USD_CAD']

for e_symbol in list_pairs:
    
     symbol = e_symbol
     account_type = 'backtest'
     granularity = '1H'
     decision_frequency = '1H'
     start_datetime = datetime.datetime(2017,1,1,0,0,0)
     end_datetime = datetime.datetime(2021,1,1,0,0,0)
     idle_duration_before_start_trading = datetime.timedelta(days=30, hours=0, minutes=0)
     initial_equity = 10000
     marginpercent = 10
     ftc=0.0
     ptc=0.0
     verbose=False
     create_data=False
     
     bb = backtest_strategy_SMA(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)
     #bb.check_data_quality()

     bb.run_strategy(14, 28)
          
     #bb.plot()

     filename = '{}_data.xlsx'.format(bb.symbol)
     uf.write_df_to_excel(bb.data, bb.backtest_folder, filename)
     
     filename = '{}_data.pkl'.format(bb.symbol)
     uf.pickle_df(bb.data, bb.backtest_folder, filename)
             
     bb.write_all_trades_to_excel()
               
     bb.monte_carlo_simulator(250)
 
     #viz.visualize(bb.symbol, bb.data, bb.listofClosedTrades)
     
     #bb.analyze_trades()
     
     #bb.calculate_average_number_of_bars_before_profitability()
              