
import configparser
import feeder
import resampler
import multiprocessing
import datetime

try:
    config = configparser.ConfigParser()
    config.read('..\..\configinfo.cfg')
   
except:
    print( 'Error in reading configuration file' )

#symbol_list = ['EUR_USD','USD_JPY','GBP_USD','USD_MXN','USD_TRY','EUR_TRY','TRY_JPY','EUR_CAD']
symbol_list = ['USD_JPY']
account_type = 'live' # live / practice / backtest
granularity = 'S5'
download_frequency = datetime.timedelta(seconds=60)
update_signal_frequency = datetime.timedelta(seconds=3600)
freq_input = 'S5'
freq_aggregate = 'M1'
retries = 0

if __name__ == '__main__':


    p_resampler = {}
    p_feeder = {}

    for symbol in symbol_list:
        
        print('1')
        socket_number = 5556
        p_resampler[symbol] = multiprocessing.Process( target = resampler.resampler, args=(config,symbol,account_type,socket_number,freq_input,freq_aggregate,) )
        p_resampler[symbol].start()

        print('2')
        socket_number = 5555    
        p_feeder[symbol] = multiprocessing.Process( target = feeder.feeder, args=(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,retries,) )
        p_feeder[symbol].start()
      


                               


