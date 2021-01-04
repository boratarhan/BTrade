
import sys
import os

from backtest_base import *

strategy_name = 'strategy v.1.0'
symbol = 'EUR_USD'
account_type = 'backtest'
data_granularity = ['1M']
decision_frequency = '1M'
data_granularity.append(decision_frequency)
data_granularity = list(np.unique(data_granularity))
start_datetime = datetime.datetime(2020,12,1,0,0,0)
end_datetime = datetime.datetime(2021,1,1,0,0,0)
idle_duration_before_start_trading = datetime.timedelta(days=0, hours=0, minutes=1)     
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
'''
granularity = '1H'
bb = backtest_base(strategy_name, symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)

bb.data['HOD'] = bb.data.index.hour
bb.data.loc[:,'bid_h-l'] = bb.data.loc[:,'bid_h'] - bb.data.loc[:,'bid_l']

cwd = os.path.dirname(__file__)
os.chdir(cwd)

data = bb.data.reset_index().groupby(['HOD'])['bid_h-l'].apply(np.array)
fig1, ax1 = plt.subplots()
ax1.set_title('Bid High-Low {} vs. Hour of Day'.format(granularity))
ax1.boxplot(data)
fig1.savefig('Bid High-Low vs. Hour of Day.pdf')

fig1, ax1 = plt.subplots()
ax1.set_title('Bid High-Low {} vs. Hour of Day'.format(granularity))
ax1.boxplot(data, showfliers=False)
fig1.savefig('Bid High-Low vs. Hour of Day (No outlier).pdf')
'''
#-----------------------------------------------------------------------------
'''   
granularity = '1H'
bb = backtest_base(strategy_name, symbol, account_type, granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)

bb.data['HOD'] = bb.data.index.hour
bb.data.loc[:,'net_move'] = np.abs(bb.data['bid_c'] - bb.data['bid_c'].shift(WindowLenght))

cwd = os.path.dirname(__file__)
os.chdir(cwd)

data = bb.data.reset_index().groupby(['HOD'])['net_move'].apply(np.array)
data = data.apply(lambda x: x[~np.isnan(x)] )

fig1, ax1 = plt.subplots()
ax1.set_title('Net move {} vs. Hour of Day'.format(granularity))
ax1.boxplot(data)
fig1.savefig('Net move {} vs. Hour of Day.pdf'.format(granularity))

fig1, ax1 = plt.subplots()
ax1.set_title('Net move {} vs. Hour of Day'.format(granularity))
ax1.boxplot(data, showfliers=False)
fig1.savefig('Net move {} vs. Hour of Day (No outlier).pdf'.format(granularity))
'''
#-----------------------------------------------------------------------------

bb = backtest_base(strategy_name, symbol, account_type, data_granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data)

cwd = os.path.dirname(__file__)
os.chdir(cwd)

bb.data[decision_frequency]['HOD'] = bb.data[decision_frequency].index.hour
bb.data[decision_frequency].loc[:,'bid_ask_spread'] = bb.data[decision_frequency].loc[:,'bid_c'] - bb.data[decision_frequency].loc[:,'ask_c']

data = bb.data[decision_frequency].reset_index().groupby(['HOD'])['bid_ask_spread'].apply(np.array)
data = data.apply(lambda x: x[~np.isnan(x)] )

fig1, ax1 = plt.subplots()
ax1.set_title('Bid Ask Spread {} vs. Hour of Day'.format(decision_frequency))
ax1.boxplot(data)
fig1.savefig('Bid Ask Spread {} vs. Hour of Day.pdf'.format(decision_frequency))

fig1, ax1 = plt.subplots()
ax1.set_title('Bid Ask Spread {} vs. Hour of Day'.format(decision_frequency))
ax1.boxplot(data, showfliers=False)
fig1.savefig('Bid Ask Spread {} vs. Hour of Day (No outlier).pdf'.format(decision_frequency))

#-----------------------------------------------------------------------------

'''
# Other analysis, not used
bb.data['HOD'] = bb.data.index.hour
bb.data['DOW'] = bb.data.index.day_name()
bb.data['MOY'] = bb.data.index.month_name()

bb.data.loc[:,'bid_cum_move'] = bb.data['bid_h-l'].rolling(WindowLenght+1).sum()


bb_HOD = bb.data.reset_index().groupby(['HOD']).agg({'bid_h-l': ['mean', 'min', 'max'], 'net_move': ['mean'] })
bb_MOY = bb.data.reset_index().groupby(['MOY']).agg({'bid_h-l': ['mean', 'min', 'max'], 'net_move': ['mean'] })
bb_DOW = bb.data.reset_index().groupby(['DOW']).agg({'bid_h-l': ['mean', 'min', 'max'], 'net_move': ['mean'] })

X= np.transpose( [bb_HOD['bid_h-l']['mean'].values, bb_HOD['net_move']['mean'].values ] )
df = pd.DataFrame(X, columns=['mean_bid_h-l', 'mean_net_move'])
df.plot.scatter(x='mean_bid_h-l',y='mean_net_move')

df['mean_net_move / mean_bid_h-l'] = df['mean_net_move'] / df['mean_bid_h-l']
df.reset_index(inplace=True)
df.plot.scatter(x='index', y='mean_net_move / mean_bid_h-l')
'''

'''
bb_HOD.sort_values(by=[('bid_spread', 'mean')],axis=0)
'''

# Other code, not used

'''
cwd = os.path.dirname(__file__)
print(cwd)
os.chdir(cwd)

filedir = os.path.join('..\\')
os.chdir(filedir)
cwd2 = os.path.abspath(os.getcwd())
sys.path.append(cwd2)
print(cwd2)

filedir = os.path.join('..\\')
os.chdir(filedir)
cwd3 = os.path.abspath(os.getcwd())
sys.path.append(cwd3)
print(cwd3)

filedir = os.path.join('.\\source_backtest')
os.chdir(filedir)
cwd4 = os.path.abspath(os.getcwd())
sys.path.append(cwd4)
print(cwd4)

filedir = os.path.join('..\\source_system')
os.chdir(filedir)
cwd5 = os.path.abspath(os.getcwd())
sys.path.append(cwd5)
print(cwd5)

print(sys.path)
'''
