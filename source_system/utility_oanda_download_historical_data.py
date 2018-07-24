import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
from oandapyV20.exceptions import V20Error
from requests.exceptions import ConnectionError
import zmq
import pandas as pd
import tables 
import tstables  
import datetime
import configparser
import time
import utility_functions as uf
import threading
import os

class desc(tables.IsDescription):
    ''' Description of TsTables table structure.
    '''
    timestamp = tables.Int64Col(pos=0)  
    ask_c = tables.Float64Col(pos=1)  
    ask_h = tables.Float64Col(pos=2)  
    ask_l = tables.Float64Col(pos=3)  
    ask_o = tables.Float64Col(pos=4)  

    bid_c = tables.Float64Col(pos=5)  
    bid_h = tables.Float64Col(pos=6)  
    bid_l = tables.Float64Col(pos=7)  
    bid_o = tables.Float64Col(pos=8)  

    volume = tables.Int64Col(pos=9)
    
class downloader_historical_data(object):
    
    def __init__(self,config,account_type,symbol,start_datetime,end_datetime,granularity,askbidmid,step):    

        self.config = config
        self.account_type = account_type
        self.symbol = symbol
        self.granularity = granularity
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.askbidmid = askbidmid
        self.step = step
        self.file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(self.account_type,self.symbol,self.granularity)

        if not os.path.exists('\\'.join(self.file_path.split('\\')[0:-1])):
            os.mkdir('\\'.join(self.file_path.split('\\')[0:-1]))
            
        if account_type == 'practice':
            
            self.connect_broker_practice()
            
        else:
            
            self.connect_broker_live()
            
        self.download_data()
        
    def connect_broker_live(self):

        self.accountID = self.config['oanda_v20']['account_number_live']
        self.access_token = self.config['oanda_v20']['access_token_live']
        self.api = oandapyV20.API(access_token=self.access_token, environment="live")

    def connect_broker_practice(self):

        self.accountID = self.config['oanda_v20']['account_number_practice']
        self.access_token = self.config['oanda_v20']['access_token_practice']
        self.api = oandapyV20.API(access_token=self.access_token, environment="practice")

    def download_data(self):

        self.h5 = tables.open_file(self.file_path, 'a')
        self.ts = self.h5.create_ts('/', 'data', desc)
        
        day_begin = self.start_datetime
        day_end = day_begin + step
        
        while day_end <= self.end_datetime:
            
            print( day_begin, day_end )

            temp = self.download_ohlc_data(day_begin, day_end, self.granularity, self.askbidmid)
             
            self.ts.append(temp)
            
            day_begin = day_end
            day_end = day_begin + step
            
        self.h5.close()

    def download_ohlc_data(self, start_datetime, end_datetime, granularity, askbidmid):
        
        start_datetime = start_datetime
        end_datetime = end_datetime

        print('Downloading data from', start_datetime, 'to', end_datetime, 'requested at', datetime.datetime.utcnow())
        
        suffix = '.000000000Z'  
        start_datetime = start_datetime.isoformat('T') + suffix  
        end_datetime = end_datetime.isoformat('T') + suffix  

        params = {"from": start_datetime,
                  "to": end_datetime,
                  "granularity": granularity,
                  "price": askbidmid }
        
        r = instruments.InstrumentsCandles(instrument=self.symbol, params=params)
        self.api.request(r)
        
        raw = r.response.get('candles')
        raw = [cs for cs in raw if cs['complete']]

        data = pd.DataFrame()
        
        if len(raw) > 0:
            
            # Convert raw data to time-open-high-low-close-volume format        
            for cs in raw:
                cs['ask_o'] = cs['ask']['o']
                cs['ask_h'] = cs['ask']['h']
                cs['ask_l'] = cs['ask']['l']
                cs['ask_c'] = cs['ask']['c']
                cs['bid_o'] = cs['bid']['o']
                cs['bid_h'] = cs['bid']['h']
                cs['bid_l'] = cs['bid']['l']
                cs['bid_c'] = cs['bid']['c']
                del cs['ask']
                del cs['bid']
                del cs['complete']

            data = pd.DataFrame(raw)
                       
            data = data.set_index('time')  
            data.index = pd.DatetimeIndex(data.index)  
                    
            data[['ask_c', 'ask_l', 'ask_h', 'ask_o','bid_c', 'bid_l', 'bid_h', 'bid_o']] = data[['ask_c', 'ask_l', 'ask_h', 'ask_o','bid_c', 'bid_l', 'bid_h', 'bid_o']].astype('float64')
 
        return data

if __name__ == '__main__':
    
    config = configparser.ConfigParser()
    config.read('..\..\configinfo.cfg')
    
#    account_type = 'practice'
#    symbol_list = ['EUR_USD', 'AUD_USD', 'USD_CAD', 'USD_JPY', 'USD_TRY']

    account_type = 'live'
    symbol_list = ['EUR_USD']
    
    start_datetime = datetime.datetime(2005,1,1,0,0,0)
    end_datetime = datetime.datetime(2018,7,20,0,0,0)
#    end_datetime = datetime.datetime.utcnow()
    
    granularity = 'S5'
    askbidmid = 'AB'
    
    step = datetime.timedelta(hours=1)

    for symbol in symbol_list:
    
        d1 = downloader_historical_data(config,account_type,symbol,start_datetime,end_datetime,granularity,askbidmid,step)
