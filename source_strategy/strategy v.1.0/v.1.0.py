# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 23:23:13 2020

@author: boratarhan
"""

import sys
sys.path.append('..\\source_backtest')
from backtest_base import *
sys.path.remove('..\\source_backtest')

symbol = 'EUR_USD'
account_type = 'backtest'
granularity = '1M'
decision_frequency = '1M'
start_datetime = datetime.datetime(2020,12,1,0,0,0)
end_datetime = datetime.datetime(2021,1,1,0,0,0)
idle_duration_before_start_trading = pd.Timedelta(value='1M')     
initial_equity = 10000
marginpercent = 100
ftc=0.0
ptc=0.0
verbose=True
create_data=False

# A standard lot = 100,000 units of base currency. 
# A mini lot = 10,000 units of base currency.
# A micro lot = 1,000 units of base currency.

bb = backtest_base(symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)

bb.data['bid_spread'] = bb.data['bid_h'] - bb.data['bid_l']
bb.data['ask_spread'] = bb.data['ask_h'] - bb.data['ask_l']

bb.data['HOD'] = bb.data.index.hour
bb.data['DOW'] = bb.data.index.day_name()
bb.data['MOY'] = bb.data.index.month_name()

bb_MOY = bb.data.reset_index().groupby(['MOY']).agg({'bid_spread': ['mean', 'min', 'max']})
bb_DOW = bb.data.reset_index().groupby(['DOW']).agg({'bid_spread': ['mean', 'min', 'max']})
bb_DOW.sort_values(by=[('bid_spread', 'mean')],axis=0)
