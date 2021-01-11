from multiprocessing import Process
import os
import time

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

parameter_window_lenght = 60
list_parameter_reward_risk_ratio = [0.5,2]
parameter_xxx = 0.0010

report = {}
            
def print_func(continent='Asia'):
    time.sleep(5)
    print('The name of continent is : ', reward_risk_ratio)
    

def process_item(reward_risk_ratio):

    window_lenght = 60
    xxx = 0.0010
    
    bb = backtest_strategy(strategy_name, symbol, account_type, data_granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data, reward_risk_ratio, xxx)
    
    bb.run_strategy(window_lenght)
    
    filename = '{}_data.xlsx'.format(bb.symbol)
    uf.write_df_to_excel(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
    
    filename = '{}_data.pkl'.format(bb.symbol)
    uf.pickle_df(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
    
    bb.write_all_trades_to_excel()


if __name__ == "__main__":  # confirms that the code is under main function

    procs = []

    for reward_risk_ratio in list_parameter_reward_risk_ratio:
            
        proc = Process(target=print_func(), args=(reward_risk_ratio,))  # instantiating without any argument
        procs.append(proc)
        proc.start()
        proc.join()

    '''
    # complete the processes
    for proc in procs:
        proc.join()
    '''
    