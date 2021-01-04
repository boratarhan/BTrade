
import sys
import os

from backtest_base import *

strategy_name = 'strategy v.2.3'
symbol = 'EUR_USD'
account_type = 'backtest'
data_granularity = ['1M']
decision_frequency = '1M'
data_granularity.append(decision_frequency)
data_granularity = list(np.unique(data_granularity))
start_datetime = datetime.datetime(2020,12,1,0,0,0)
end_datetime = datetime.datetime(2020,12,10,0,0,0)
idle_duration_before_start_trading = datetime.timedelta(days=0, hours=0, minutes=0)     
initial_equity = 10000
marginpercent = 100
ftc=0.0
ptc=0.0
verbose=True
create_data=False

WindowLenght = 1

# A standard lot = 100,000 units of base currency. 
# A mini lot = 10,000 units of base currency.
# A micro lot = 1,000 units of base currency.

#-----------------------------------------------------------------------------

bb = backtest_base(strategy_name, symbol, account_type, data_granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)

cwd = os.path.dirname(__file__)
os.chdir(cwd)

bb.data[bb.decision_frequency].loc[:,'H-L'] = bb.data[bb.decision_frequency]['bid_h'] - bb.data[bb.decision_frequency]['bid_l']

for i in [60]:#12, 720, 4320, 8640, 17280]:
    
    bb.data[bb.decision_frequency].loc[:,'cum-move-{}'.format(i)] = bb.data[bb.decision_frequency]['H-L'].rolling(i).sum()
    bb.data[bb.decision_frequency].loc[:,'net-move-{}'.format(i)] = np.abs( bb.data[bb.decision_frequency]['bid_c'] - bb.data[bb.decision_frequency]['bid_c'].shift(i) )
    bb.data[bb.decision_frequency].loc[:,'cum-vol-{}'.format(i)] = bb.data[bb.decision_frequency]['volume'].rolling(i).sum()

    fig1, ax1 = plt.subplots()
    ax1.set_title('Cumulative-Move vs Net-Move')
    ax1.set(xlabel='net-move', ylabel='cum-move')
    ax1.scatter(bb.data[bb.decision_frequency]['net-move-{}'.format(i)], bb.data[bb.decision_frequency]['cum-move-{}'.format(i)])
    fig1.savefig('Net-Move vs Cumulative-Move.format-{}.png'.format(i))

    fig1, ax1 = plt.subplots()
    ax1.set_title('Cumulative-Move vs Cum-Vol')
    ax1.set(xlabel='cum-vol', ylabel='cum-move')
    ax1.scatter(bb.data[bb.decision_frequency]['cum-vol-{}'.format(i)], bb.data[bb.decision_frequency]['cum-move-{}'.format(i)])
    fig1.savefig('Cum-volume vs Cumulative-Move.format-{}.png'.format(i))

    fig1, ax1 = plt.subplots()
    ax1.set_title('Cum-Vol vs Net-Move')
    ax1.set(xlabel='net-move', ylabel='cum-vol')
    ax1.scatter(bb.data[bb.decision_frequency]['net-move-{}'.format(i)], bb.data[bb.decision_frequency]['cum-vol-{}'.format(i)])
    fig1.savefig('Net-Move vs Cumulative-Vol.format-{}.png'.format(i))

    bb.data[bb.decision_frequency][:1000000].to_excel('data_for_cum_nove_vol.xlsx')

