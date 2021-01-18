from multiprocessing import Pool
import os
import time

cwd = os.path.dirname(__file__)
os.chdir(cwd)

from backtest_base import *
from backtest_strategy_v_4_0 import backtest_strategy

cwd = os.path.dirname(__file__)
os.chdir(cwd)

# A standard lot = 100,000 units of base currency. 
# A mini lot = 10,000 units of base currency.
# A micro lot = 1,000 units of base currency.

def process_item(input_arg):
    
    window_lenght = int(input_arg[0])
    reward_risk_ratio = float(input_arg[1])
    risked_amount = float(input_arg[2])

    report = {}
    run_ID = '{}-{}-{}'.format(window_lenght, reward_risk_ratio, risked_amount)
    report[run_ID]= {}
 
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
        
    bb = backtest_strategy(strategy_name, symbol, account_type, data_granularity, decision_frequency, start_datetime, end_datetime, idle_duration_before_start_trading, initial_equity, marginpercent, ftc, ptc, verbose, create_data, reward_risk_ratio, risked_amount)
    
    bb.run_strategy(window_lenght)
         
    filename = '{}_data.xlsx'.format(bb.symbol)
    uf.write_df_to_excel(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
    
    filename = '{}_data.pkl'.format(bb.symbol)
    uf.pickle_df(bb.data[bb.decision_frequency], bb.backtest_folder, filename)
    
    bb.write_all_trades_to_excel()
    
    report[run_ID]['numberofClosedLongTrades'] = bb.numberofClosedLongTrades
    report[run_ID]['numberofClosedShortTrades'] = bb.numberofClosedShortTrades
    report[run_ID]['numberofTrades'] = bb.numberofClosedShortTrades + bb.numberofClosedShortTrades
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
    result_file = os.path.join(bb.backtest_folder, 'summary-{}.xlsx'.format(time) )
    
    df = pd.DataFrame(report)
    df.to_excel(result_file)
        
    result_file = 'summary-{}.pkl'.format(time)
    uf.pickle_df(df, bb.backtest_folder, result_file)

    return df

if __name__ == '__main__':

    input_arg = []

    list_parameter_window_lenght = [60, 120, 240, 480, 720, 1440]
    list_parameter_reward_risk_ratio = [0.5, 1.0, 2.0]
    list_parameter_risked_amount = [0.020, 0.0040, 0.0060, 0.0080]
    
    for window_lenght in list_parameter_window_lenght:
    
        for reward_risk_ratio in list_parameter_reward_risk_ratio:

            for risked_amount in list_parameter_risked_amount:

                input_arg.append( (window_lenght, reward_risk_ratio, risked_amount) )
                
    p = Pool(10)
    results = p.map(process_item, input_arg)

    df = pd.DataFrame()
    i = 0
    for window_lenght in list_parameter_window_lenght:
    
        for reward_risk_ratio in list_parameter_reward_risk_ratio:

            for risked_amount in list_parameter_risked_amount:
            
                run_ID = '{}-{}-{}'.format(window_lenght, reward_risk_ratio, risked_amount)
                
                df[run_ID] = results[i][run_ID].values
                df.index = results[i][run_ID].index
                
                i = i + 1
        
    df.to_excel('..\\..\\results_backtest\\summary.xlsx')