
import os

cwd = os.path.dirname(__file__)
os.chdir(cwd)

from backtest_base import *
from backtest_strategy_v_4_0 import backtest_strategy

cwd = os.path.dirname(__file__)
os.chdir(cwd)

strategy_name = 'strategy v.4.0'
symbol = 'EUR_USD'
account_type = 'backtest'
data_granularity = ['1M']
decision_frequency = '1M'
data_granularity.append(decision_frequency)
data_granularity = list(np.unique(data_granularity))
start_datetime = datetime.datetime(2020,1,1,0,0,0)
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

list_parameter_window_lenght = [60]
list_parameter_reward_risk_ratio = [0.5,2]
list_parameter_xxx = [0.0010]

report = {}

for window_lenght in list_parameter_window_lenght:
    
    for reward_risk_ratio in list_parameter_reward_risk_ratio:

        for xxx in list_parameter_xxx:
        
            run_ID = '{}-{}-{}'.format(window_lenght, reward_risk_ratio, xxx)
            report[run_ID]= {}
            
            bb = backtest_strategy(strategy_name, symbol, account_type, data_granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data, reward_risk_ratio, xxx)
            
            bb.run_strategy(window_lenght)
                    
            filename = '{}_data.xlsx'.format(bb.symbol)
            uf.write_df_to_excel(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
            
            filename = '{}_data.pkl'.format(bb.symbol)
            uf.pickle_df(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
                    
            bb.write_all_trades_to_excel()
    
            report[run_ID]['numberofClosedLongTrades'] = bb.numberofClosedLongTrades
            report[run_ID]['numberofClosedShortTrades'] = bb.numberofClosedShortTrades
            report[run_ID]['sharpe_ratio'] = bb.sharpe_ratio
            report[run_ID]['sortino_ratio'] = bb.sortino_ratio
            report[run_ID]['average_win'] = bb.average_win
            report[run_ID]['average_loss'] = bb.average_loss
            report[run_ID]['winning_ratio'] = bb.winning_ratio
            report[run_ID]['losing_ratio'] = bb.losing_ratio
            report[run_ID]['expectancy'] = bb.expectancy
            report[run_ID]['net performance'] = bb.data[bb.decision_frequency]['cumret-strategy'][-1] * 100
            report[run_ID]['max drawdown'] = bb.maxdrawdown * 100
        

cwd = os.path.dirname(__file__)
time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
result_file = '..\\..\\results_backtest\\results-{}.xlsx'.format(time)

df = pd.DataFrame(report)
df.to_excel(result_file)
