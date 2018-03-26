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
import logging
import json

logging.basicConfig(
    filename="v20.log",
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s : %(message)s',
)

isAlive = True

# offset is used for testing during the weekend.
offset = datetime.timedelta(days=0)

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

class feeder(object):
    ''' Feeder receives data from broker and publishes messages for the rest of the objects in the system
        Ideally, feeder only deals with tick data and the rest of the objects handle resampling. However,
        OANDA streams only a portion of the entire tick data therefore feeder is designed to collect 5S data. 
        Tick data is collected only for future analysis or visual purposes.
    '''

    def __init__(self,config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency):

        self.config = config
        self.symbol = symbol
        self.granularity = granularity
        self.account_type = account_type
        self.socket_pub_socket_number = socket_number
        self.socket_sub_socket_number = socket_number + 3 
        self.download_frequency = download_frequency
        self.update_signal_frequency = update_signal_frequency

        self.askbidmid = 'AB'
        self.ticks = 0
        self.number_of_bars = 0
        self.heartbeat = 0
        self.current_heartbeat = datetime.datetime.utcnow()

        self.file_path_ohlc = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(self.account_type,self.symbol,self.granularity)
        self.folder_path = '..\\..\\datastore\\_{0}\\{1}'.format(self.account_type,self.symbol)
        
        self.in_memory_bar_ohlc_df = pd.DataFrame()
        
        self.context_pub = zmq.Context()
        self.socket_pub = self.context_pub.socket(zmq.PUB)
        self.socket_pub.set_hwm(0)
        self.socket_pub.connect("tcp://127.0.0.1:{}".format(self.socket_pub_socket_number))

        self.context_pub = zmq.Context()
        self.socket_pub = self.context_pub.socket(zmq.PUB)
        self.socket_pub.set_hwm(0)
        self.socket_pub.connect("tcp://127.0.0.1:{}".format(self.socket_pub_socket_number))

        self.context_sub = zmq.Context()
        self.socket_sub = self.context_sub.socket(zmq.SUB)
        self.socket_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket_sub.connect("tcp://127.0.0.1:{}".format(self.socket_sub_socket_number))

        time.sleep(5) # Since binding takes time, sleep for a few seconds before running

    def start(self):

        global isAlive
        isAlive = True
           
        if( self.account_type == 'live'):
            
            self.connect_broker_live()
            
        elif( self.account_type == 'practice'):

            self.connect_broker_practice()
            
        else:
            
            print('Error in account type, it should be either live, practice, or backtest') 
           
        self.open_database(self.file_path_ohlc)
           
        self.download_missing_data()

        print('Feeder Ready to go')

        # Run two threads for receiving real-time data and candle data                    
        t1 = threading.Thread( target=self.receive_realtime_tick_data )
        t2 = threading.Thread( target=self.receive_realtime_bar_data, args=(self.granularity, self.askbidmid, ) )

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    def connect_broker_live(self):

        self.accountID = self.config['oanda_v20']['account_number_live']
        self.access_token = self.config['oanda_v20']['access_token_live']
        self.api = oandapyV20.API(access_token=self.access_token)

    def connect_broker_practice(self):

        self.accountID = self.config['oanda_v20']['account_number_practice']
        self.access_token = self.config['oanda_v20']['access_token_practice']
        self.api = oandapyV20.API(access_token=self.access_token, environment="practice")

    def open_database(self, file_path):
        ''' Open an existing h5 file or create a new file and table 
        '''

        if( os.path.exists(file_path) ):
            ''' If a file exists, then start with current time and go back to find the
                last data point stored in the database.
                Otherwise create a new database.
            '''

            self.h5 = tables.open_file(file_path, 'a')
            self.ts = self.h5.root.data._f_get_timeseries()
            
            read_start_dt = datetime.datetime.utcnow() - offset - datetime.timedelta(days=1)
            read_end_dt = datetime.datetime.utcnow() - offset
            
            while True:
                
                rows = self.ts.read_range(read_start_dt,read_end_dt)
                if rows.shape[0] > 0:
                    self.current_timestamp = rows.index[-1]        
                    break
                else:
                    read_start_dt = read_start_dt - datetime.timedelta(days=1)
                                     
        else:

            if( not os.path.exists(self.folder_path)):
                
                os.mkdir(self.folder_path) 

            self.h5 = tables.open_file(file_path, 'w')
            self.ts = self.h5.create_ts('/', 'data', desc)
            self.current_timestamp = datetime.datetime(2010,1,1,0,0,0)

    def download_missing_data(self):

        if datetime.datetime.utcnow() - self.current_timestamp > datetime.timedelta(hours=1):
            
            print('More than 1 hour of data missing, need to download before starting')
            
            start_time = self.current_timestamp
            end_time = start_time + datetime.timedelta(hours=1)
            
            while end_time <= datetime.datetime.utcnow():
                    
                temp = self.download_ohlc_data(start_time, end_time, self.granularity, self.askbidmid)
                 
                self.ts.append(temp)
                
                start_time = end_time
                end_time = start_time + datetime.timedelta(hours=1)
                                
            self.h5.close()
            
            self.open_database(self.file_path_ohlc)
        
    def download_ohlc_data(self, start_datetime, end_datetime, granularity, askbidmid):
        
        start_datetime = start_datetime
        end_datetime = end_datetime
        
        start_datetime = start_datetime.replace(microsecond=0)
        end_datetime = end_datetime.replace(microsecond=0)
        slack = end_datetime - end_datetime.replace(second=0)
        slack = slack % datetime.timedelta(seconds=5)
        end_datetime = end_datetime - slack        
        
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
 
            data = data[data.index > self.current_timestamp]
    
        return data
                
    def receive_realtime_bar_data(self,granularity,askbidmid):
        ''' Constantly check the current time
            At evey 5 seconds, download 5S bar
        '''
        
        global isAlive
        
        previous_slack_download = datetime.timedelta(seconds=0)
        previous_slack_signal = datetime.timedelta(seconds=0)
       
        while isAlive:

            timestamp_bar_end = datetime.datetime.utcnow() - offset
            slack = timestamp_bar_end - timestamp_bar_end.replace(minute=0,second=0)
            
            current_slack_download = slack % self.download_frequency
            current_slack_signal = slack % self.update_signal_frequency
            
            if current_slack_download < previous_slack_download:
            
                fromTime = self.current_timestamp
                toTime = timestamp_bar_end
                
                try:

                    data = self.download_ohlc_data(fromTime, toTime, granularity, askbidmid)
                    self.append_bar_data_to_in_memory_bar_ohlc_df(data)

                    if current_slack_signal < previous_slack_signal:
                        self.append_in_memory_bar_ohlc_df_to_database()
                    
                    self.number_of_bars = self.number_of_bars + 1
        
                except Exception as e:
                    
                    print(e)

                    isAlive = False
                    self.h5.close()
                    print('Bar Data download failed at [UTC]', datetime.datetime.utcnow() )
                    
                    break
                                
            previous_slack_download = current_slack_download
            previous_slack_signal = current_slack_signal

            if isAlive == False:
                
                break

    def append_bar_data_to_in_memory_bar_ohlc_df(self,temp):
        ''' Take each received data signal as input and append to an in-memory dataframe
        '''
        
        if temp.index.size >= 1:
            
            self.in_memory_bar_ohlc_df = self.in_memory_bar_ohlc_df.append(temp)
            
            self.update_current_timestamp(self.in_memory_bar_ohlc_df)

    def update_current_timestamp(self,dataframe):

        year = dataframe.index[-1].year
        month = dataframe.index[-1].month
        day = dataframe.index[-1].day
        hour = dataframe.index[-1].hour
        minute = dataframe.index[-1].minute
        second = dataframe.index[-1].second
        self.current_timestamp = datetime.datetime(year,month,day,hour,minute,second)
        
    def append_in_memory_bar_ohlc_df_to_database(self):
        ''' Append dataframe which keeps in-memory data to h5 file on disk
            Remove the contents of in-memory dataframe
        '''

        if self.in_memory_bar_ohlc_df.index.size >= 1:

            self.ts.append(self.in_memory_bar_ohlc_df[:])
            self.in_memory_bar_ohlc_df = pd.DataFrame()  

        self.h5.close()
        
        msg = "Data Updated"
        print("Sending message: {0}".format(msg))                   
        self.socket_pub.send_string(msg)
        
        msg = self.socket_sub.recv_string()
        print("Received message: {0}".format(msg))
        
        self.h5 = tables.open_file(self.file_path_ohlc, 'a')
        self.ts = self.h5.root.data._f_get_timeseries()

    def receive_realtime_tick_data(self):

        global isAlive
        
        try:
         
            self.download_tick_data()
            
        except Exception as e:                    
            
            print(e)
            
            isAlive = False
            print('Tick data download failed at [UTC]', datetime.datetime.utcnow() )

    def download_tick_data(self):

        global isAlive
        params = { "instruments": self.symbol }
        s = pricing.PricingStream(accountID=self.accountID , params=params)

        while isAlive:

            try:

                for msg in self.api.request(s):
        
                    timestamp = msg['time']
                    timestamp = timestamp.replace('T',' ')
                    timestamp = timestamp.replace('Z','')
                    timestamp = uf.parse_date(timestamp)
        
                    if (msg['type'] == 'PRICE') and isAlive:
        
                        # compose the message
                        instrument = msg['instrument']
                        ask = msg['asks'][0]['price']
                        bid = msg['bids'][0]['price']
                        ask_volume = msg['asks'][0]['liquidity']
                        bid_volume = msg['bids'][0]['liquidity']
                                             
                        print(instrument, timestamp, ask, bid, ask_volume, bid_volume)                     
                        
                        self.ticks = self.ticks + 1
                         
                    elif (msg['type'] == 'HEARTBEAT') and isAlive:
                        ''' Heartbeat happens at approximately every 5 seconds. Even when the markets are closed.
                        '''
                
                        print("Receiving Heartbeat,{0}".format(timestamp))
                
                        current_heartbeat = timestamp
                        previous_heartbeat = timestamp
                        
                        if current_heartbeat - previous_heartbeat >= datetime.timedelta(seconds=9) and self.heartbeat > 1:
                            
                            print("Heartbeat not received for extended period")
                            isAlive = False
                                            
                        previous_heartbeat = current_heartbeat
                        
                        self.heartbeat = self.heartbeat + 1
        
                    else:
        
                        print("msg type not receognized by feeder")
                        isAlive = False
                        
                    if isAlive == False:
                    
                        break
                
            except V20Error as e:
                # catch API related errors that may occur
                print("Error: {}".format(e))
                isAlive = False
                break

            except ConnectionError as e:
                print("Error: {}".format(e))

            except StreamTerminated as e:
                print("Error: {}".format(e))
                isAlive = False                        
                break

            except Exception as e:
                print("Error: {}".format(e))
                isAlive = False
                break
                               
def ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,retries):
    
    while True:
            
        f1 = feeder(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency)

        try:

            f1.start()  
            print('Trying to restart feeder:', retries)
            
        except Exception as e:
            
            print(e)
        
            retries += 1        
            print('Trying to restart feeder:', retries)
            ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,retries)

if __name__ == '__main__':
        
    try:
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')
       
    except:
        print( 'Error in reading configuration file' )

    symbol = 'USD_TRY'
    symbol = 'AUD_USD'
    account_type = 'practice'
    socket_number = 5555    
    granularity = 'S5'
    download_frequency = datetime.timedelta(seconds=60)
    update_signal_frequency = datetime.timedelta(seconds=60)

    ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,retries=0)
    