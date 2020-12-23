import datetime
import pandas as pd
import os
import tables 
import tstables  
import configparser
import strategy
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.forexlabs as labs
from oandapyV20.exceptions import V20Error
from oandapyV20.exceptions import StreamTerminated
import utility_functions as uf

symbol = 'EUR_USD'
granularity = 'S5'
account_type = 'live'
askbidmid = 'AB'

def convert_raw_data_to_dataframe(raw):

    data = pd.DataFrame()
    
    if len(raw) > 0:
        

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
                
        data[['ask_c', 'ask_h', 'ask_l', 'ask_o','bid_c', 'bid_h', 'bid_l', 'bid_o']] = data[['ask_c', 'ask_h', 'ask_l', 'ask_o','bid_c', 'bid_h', 'bid_l', 'bid_o']].astype('float64')
 
        data = data[['ask_c', 'ask_h', 'ask_l', 'ask_o','bid_c', 'bid_h', 'bid_l', 'bid_o','volume']]
    
    return data


start_time = datetime.datetime(2020, 12, 22, 0, 0, 00)
end_time = datetime.datetime(2020, 12, 22, 4, 29, 00)
 
suffix = '.000000Z'     
start_datetime = start_time.isoformat('T') + suffix  
end_datetime = end_time.isoformat('T') + suffix  

params = {"from": start_datetime,
          "to": end_datetime,
          "granularity": granularity,
          "price": askbidmid }

config = configparser.ConfigParser()
config.read('..\..\configinfo.cfg')
accountID = config['oanda_v20']['account_number_{}'.format(account_type)]
access_token = config['oanda_v20']['access_token_{}'.format(account_type)]
api = oandapyV20.API(access_token=access_token, environment="{}".format(account_type))
           
print("requesting...")
r = instruments.InstrumentsCandles(instrument=symbol, params=params)
api.request(r)
print("received...")

raw = r.response.get('candles')
raw = [cs for cs in raw if cs['complete']]
                
data = convert_raw_data_to_dataframe(raw)

data = data.tz_localize(None)

#filename = "DownloadedHistorical.xlsx"
#folderpath = '..\\..\\datastore'           

#uf.write_df_to_excel(data, folderpath, filename)


                