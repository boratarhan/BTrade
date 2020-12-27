import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.forexlabs as labs
from oandapyV20.exceptions import V20Error
from oandapyV20.exceptions import StreamTerminated
from requests.exceptions import ConnectionError
import zmq
import pandas as pd
import tables 
import tstables 
import json
import configparser
import datetime
import time
import utility_functions as uf
import os
import sys

'''
The code should be updated based on deprecation warnings. However, it may require extensive work.
I will keep it in this version as long as it works.
Turn off warnings for keeping the screen cleaner.
'''
import warnings
warnings.filterwarnings("ignore", category=Warning) 

'''
import logging
logging.basicConfig(
    filename="v20.log",
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s : %(message)s',
)
'''

isAlive = True

class desc(tables.IsDescription):
    ''' 
    Description of TsTables table structure.
    '''
    timestamp = tables.Int64Col(pos=0)  
    ask_o = tables.Float64Col(pos=1)  
    ask_h = tables.Float64Col(pos=2)  
    ask_l = tables.Float64Col(pos=3)  
    ask_c = tables.Float64Col(pos=4)  

    bid_o = tables.Float64Col(pos=5)  
    bid_h = tables.Float64Col(pos=6)  
    bid_l = tables.Float64Col(pos=7)  
    bid_c = tables.Float64Col(pos=8)  

    volume = tables.Int64Col(pos=9)

class feeder(object):
    ''' 
    Feeder receives data from broker and publishes messages for the rest of the objects in the system
    Ideally, feeder only deals with tick data and the rest of the objects handle resampling. However,
    OANDA streams only a portion of the entire tick data therefore feeder is designed to collect 5S data. 
    Also, since my strategies are not suitable for tick data, so it does not lose any advantage by using S5 data.
    Tick data may be collected only for future analysis or visual purposes.
    '''

    def __init__(self,config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose):

        self.config = config
        self.symbol = symbol
        self.granularity = granularity
        self.account_type = account_type
        self.socket_pub_socket_number = socket_number
        self.socket_sub_socket_number = socket_number + 3 
        '''
        Defined two frequencies:
        - download_frequency is the frequency to download bar data and append to in-memory dataframe, e.g. 1 min
        - update_signal_frequency is the frequency to append in-memory dataframe to database, e.g. 1 hour
        - main idea is to make decisions every hour but get updates every minute for assessment.
        '''        
        self.download_frequency = download_frequency
        self.update_signal_frequency = update_signal_frequency
        self.download_data_start_date = download_data_start_date
        '''
        Following input is mostly take None value. It is useful only if user wants to download realtime data for a defined period.
        In that case, the feeder will start as usual but end after this date.
        It is used in source_system > workflow_compare_realtime_and_historical_data.py
        '''
        self.download_data_end_date = download_data_end_date
        
        self.askbidmid = 'AB'
        self.ticks = 0
        self.number_of_bars = 0
        self.heartbeat = 0
        self.current_heartbeat = datetime.datetime.utcnow()

        self.path_ohlc_data = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(self.account_type,self.symbol,self.granularity)
        self.path_folder = '..\\..\\datastore\\_{0}\\{1}'.format(self.account_type,self.symbol)
                
        self.in_memory_bar_ohlc_df = pd.DataFrame()

        '''
        Open two socket connections.
        Publisher is used for publishing messages to forwarder/strategy that the new data is ready to read.
        Subscriber receives messages from forwarder/strategy that the strategy has been executed. However, this is fairly obsolete message.
        I included this with anticipation of future developments.
        Feeder then continues waiting for receiving new data and saving it.
        '''        
        self.context_pub = zmq.Context()
        self.socket_pub = self.context_pub.socket(zmq.PUB)
        self.socket_pub.set_hwm(0)
        self.socket_pub.connect("tcp://127.0.0.1:{}".format(self.socket_pub_socket_number))
        
        self.context_sub = zmq.Context()
        self.socket_sub = self.context_sub.socket(zmq.SUB)
        self.socket_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket_sub.connect("tcp://127.0.0.1:{}".format(self.socket_sub_socket_number))
        
        self.verbose = verbose

        time.sleep(5) # Since binding takes time, sleep for a few seconds before running

    def start(self):

        global isAlive
        isAlive = True
                   
        self.connect_broker()

        self.open_database()

        self.download_missing_data()

        print('Feeder Ready to go')

        self.download_new_data()
         
    def connect_broker(self):
        ''' 
        Connect to OANDA through account ID and access token based on account type.
        '''    
        print("Connecting to broker...")
        try: 
   
            self.accountID = self.config['oanda_v20']['account_number_{}'.format(self.account_type)]
            self.access_token = self.config['oanda_v20']['access_token_{}'.format(self.account_type)]
            self.api = oandapyV20.API(access_token=self.access_token, environment="{}".format(self.account_type))
            print("Connection successful")
    
        except V20Error as err:
            print("V20Error occurred: {}".format(err))
             
    def open_database(self):
        ''' 
        Open an existing h5 file or create a new file and table 
        '''
        print("Opening database...")
        if( os.path.exists(self.path_ohlc_data) ):

            ''' 
            If a file exists, then start with current time and go back to find the
            last data point stored in the database.
            Otherwise create a new database.
            '''
                    
            self.h5 = tables.open_file(self.path_ohlc_data, 'a')
            self.ts = self.h5.root.data._f_get_timeseries()
                        
            read_start_dt = datetime.datetime.utcnow() - datetime.timedelta(days=1)     # datetime.datetime
            read_end_dt = datetime.datetime.utcnow()                                    # datetime.datetime
            
            '''
            tstables does not have a built-in function to return the last row. Therefore,
            I find the last entry in this loop.
            '''

            while True:
                
                rows = self.ts.read_range(read_start_dt,read_end_dt)
                
                if rows.shape[0] > 0:
                    # When data is read from TsTables, timezone info is lost. Need to set it back to UTC.
                    rows=rows.tz_localize('UTC')                                        #datetime64
                    self.current_timestamp = rows.index[-1]                             #pandas._libs.tslibs.timestamps.Timestamp      
                    self.current_timestamp = self.current_timestamp.to_pydatetime()     #datetime.datetime 
                    
                    break

                else:

                    read_start_dt = read_start_dt - datetime.timedelta(days=1)

            print("Database is opened successfully")
            
        else:
            
            self.create_database()
                
    def create_database(self):
        '''
        Create an empty database
        '''
        if( not os.path.exists(self.path_folder)):
            
            os.mkdir(self.path_folder) 

        self.h5 = tables.open_file(self.path_ohlc_data, 'w')
        self.ts = self.h5.create_ts('/', 'data', desc)
        
        self.current_timestamp = self.download_data_start_date  #datetime.datetime 
        
    def download_missing_data(self):
       
        print("download_missing_data")
        
        if ( datetime.datetime.now(datetime.timezone.utc) - self.current_timestamp > datetime.timedelta(hours=1) ):
                                   
            print('More than 1 hour of data missing, need to download before starting')
            print('Downloading chunks of data of 1 hour length of duration')            

            start_time = self.current_timestamp
            end_time = start_time + datetime.timedelta(hours=1)
            end_time = end_time.replace(second = 0, microsecond = 0)
            
            while end_time <= datetime.datetime.now(datetime.timezone.utc):
                    
                temp = self.download_ohlc_data(start_time, end_time)
                 
                self.ts.append(temp)
                
                start_time = end_time
                end_time = start_time + datetime.timedelta(hours=1)
                              
            end_time = datetime.datetime.now(datetime.timezone.utc)
            temp = self.download_ohlc_data(start_time, end_time)
            self.ts.append(temp)
            self.h5.close()
            self.open_database()

        else:
            
            start_time = self.current_timestamp
            end_time = pd.datetime.now(datetime.timezone.utc).replace(second = 0, microsecond = 0)
            temp = self.download_ohlc_data(start_time, end_time)
            self.ts.append(temp)
            self.h5.close()
            self.open_database()            
            
    def download_ohlc_data(self, start_datetime, end_datetime):
                
        start_datetime = start_datetime.replace(microsecond=0)
        end_datetime = end_datetime.replace(microsecond=0)
        slack = end_datetime - end_datetime.replace(second=0)
        slack = slack % datetime.timedelta(seconds=5)  # Download 5 second frequency data
        end_datetime = end_datetime - slack        
        
        print('Downloading', self.symbol, 'data from', start_datetime, 'to', end_datetime, 'requested at', datetime.datetime.utcnow())
        
        suffix = '.000000Z'  

        '''
        Start datetime comes from self.current_timestamp  
        Since self.current_timestamp has timezone information at the end
        tz information needs to be eliminated by using [0:-6] because API does not accept that format 
        '''
        
        start_datetime = start_datetime.isoformat('T')[0:-6] + suffix  
        end_datetime = end_datetime.isoformat('T')[0:-6] + suffix  

        params = {"from": start_datetime,
                  "to": end_datetime,
                  "granularity": self.granularity,
                  "price": self.askbidmid }
        
                            
        if self.verbose == True: 
            print("requesting data...")
        r = instruments.InstrumentsCandles(instrument=self.symbol, params=params)
        self.api.request(r)
        if self.verbose == True: 
            print("received data...")
        
        raw = r.response.get('candles')
        raw = [cs for cs in raw if cs['complete']]

        data = self.convert_raw_data_to_dataframe(raw)
        
        return data

    def convert_raw_data_to_dataframe(self, raw):

        data = pd.DataFrame()
        
        if len(raw) > 0:
            
            '''
            Convert raw data to time-open-high-low-close-volume format        
            '''
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
                    
            data[['ask_o', 'ask_h', 'ask_l', 'ask_c', 'bid_o', 'bid_h', 'bid_l', 'bid_c']] = data[['ask_o', 'ask_h', 'ask_l', 'ask_c', 'bid_o', 'bid_h', 'bid_l', 'bid_c']].astype('float64')
 
            '''
            Make sure that the sequence of columns are identical to the description of class desc(tables.IsDescription)
            '''
            data = data[['ask_o', 'ask_h', 'ask_l', 'ask_c', 'bid_o', 'bid_h', 'bid_l', 'bid_c','volume']]
        
            data = data[data.index > self.current_timestamp]
    
        return data
    
    def download_new_data(self):
        
        '''
        My initial plan was to run two threads running parallel to get both streaming data and bar data
        Running two threads for receiving real-time data and bar data causes problems, therefore I am running only bar data
        Since this is not a critical issue, I can hold this off for now.
        
        t1 = threading.Thread( target=self.receive_realtime_bar_data, args=() )
        t1.start()
        t1.join()
        '''
        self.receive_realtime_bar_data()
        
    def get_latest_candles(self, no_of_candles, granularity):
        
        try:
            
            params = {"count": no_of_candles, "granularity": "{}".format(granularity)}
            self.r = instruments.InstrumentsCandles(self.symbol, params)
            self.api.request(self.r)
                           
            return self.r.response.get('candles')
             
        except:
            
            print("Error in getting candle...")            
            
    def receive_realtime_bar_data(self):
        ''' 
        Constantly check the current time and download bar data with specified granularity
        '''
        global isAlive
        previous_slack_signal = datetime.timedelta(seconds=0)
        
        while isAlive:
            
            '''
            Feeder constantly requests minute bar data from broker. As soon as the minute
            bar is closed, it downloads 5S granularity data. This ensures any premature 
            data requests. Typically there is 1-5 seconds lag between theoretical bar close
            and receipt of actual bar close signal.
            '''
                    
            last_candle_time = self.current_timestamp
            if self.verbose == True: 
                print("Last candle: {}".format(last_candle_time))

            while True:  

                '''
                This section is useful when user wants feeder to download real-time data for
                a defined period. Once that date is reached, feeder stops, database is closed and 
                feeder ends. It is used in source_system > workflow_compare_realtime_and_historical_data.py
                '''
                if self.download_data_end_date != None:
                    
                    if datetime.datetime.utcnow() >= self.download_data_end_date:
                        
                        isAlive = False
                        self.h5.close()
                        break
                    
                '''
                Fetching latest 2 candles
                '''
                latest_candles = self.get_latest_candles(2, "M1")
                
                for e_candle in latest_candles:
    
                    latest_candle_time = (datetime.datetime.fromisoformat(e_candle['time'].replace('000Z', '+00:00')))
                                        
                    if (e_candle['complete'] == True) and (latest_candle_time > last_candle_time):
                    
                        if self.verbose == True: 
                            print("Latest candle: {0}, {1} ".format( latest_candle_time, last_candle_time) )

                        latest_candle_time = (datetime.datetime.fromisoformat(e_candle['time'].replace('000Z', '+00:00'))).replace(second=0)
                        
                        fromTime = self.current_timestamp
                        toTime = latest_candle_time + datetime.timedelta(minutes=1)
                        
                        if self.verbose == True: 
                            print('fromTime:', fromTime, ' toTime:', toTime)

                        try:
        
                            data = self.download_ohlc_data(fromTime, toTime)
                            
                            self.append_bar_data_to_in_memory_bar_ohlc_df(data)
        
                            slack = pd.datetime.now(datetime.timezone.utc) - pd.datetime.now(datetime.timezone.utc).replace(hour= 0, minute=0, second=0)
                            current_slack_signal = slack % self.update_signal_frequency

                            if self.download_frequency == self.update_signal_frequency:
                                
                                self.append_in_memory_bar_ohlc_df_to_database()
                                
                            elif self.download_frequency < self.update_signal_frequency:
                                
                                if current_slack_signal < previous_slack_signal:
                                    
                                    self.append_in_memory_bar_ohlc_df_to_database()
                            
                            else:
                                
                                print("Problem: download_frequency > update_signal_frequency, please check the feeder inputs")
                                exit()
                                
                            self.number_of_bars = self.number_of_bars + 1
                
                            previous_slack_signal = current_slack_signal
                
                        except Exception as e:
                            
                            print(e)
        
                            '''
                            In case download fails, global isAlive variable is set to false.
                            This triggers feeder object to restart and make connections with broker and other objects.
                            '''
                            
                            isAlive = False
                            self.h5.close()
                            print('Bar Data download failed at [UTC]', datetime.datetime.utcnow() )
                            
                            break
                        
                        last_candle_time = latest_candle_time
                
                
                
    def append_bar_data_to_in_memory_bar_ohlc_df(self,temp):
        ''' 
        Take each received data signal as input and append to an in-memory dataframe
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
        self.current_timestamp = pd.datetime(year,month,day,hour,minute,second, tzinfo=datetime.timezone.utc)
        
    def append_in_memory_bar_ohlc_df_to_database(self):
        ''' 
        Append dataframe which keeps in-memory data to h5 file on disk
        Then remove the contents of in-memory dataframe
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
        
        self.h5 = tables.open_file(self.path_ohlc_data, 'a')
        self.ts = self.h5.root.data._f_get_timeseries()
                               
    def add_calendar_data(self):
        
        params = {"instrument": list(self.symbol), "period": 217728000 } #period seems to capture the length of future in seconds, default was 86400
        r = labs.Calendar(params=params)
        self.df_calendar = pd.DataFrame(self.api.request(r))
        
        path = '..\\..\\datastore\\_{0}\\{1}\\calendar.pkl'.format(self.account_type,self.symbol)
        self.df_calendar.to_pickle(path)
       
    def add_orderbook_data(self):
        
        r = instruments.InstrumentsOrderBook(instrument=self.symbol)
        self.df_orderbook = pd.DataFrame(self.api.request(r))

        path = '..\\..\\datastore\\_{0}\\{1}\\orderbook.pkl'.format(self.account_type,self.symbol)
        self.df_orderbook.to_pickle(path)

    def add_positionbook_data(self):
        
        r = instruments.InstrumentsPositionBook(instrument=self.symbol)
        self.df_positionbook = pd.DataFrame(self.api.request(r))

        path = '..\\..\\datastore\\_{0}\\{1}\\positionbook.pkl'.format(self.account_type,self.symbol)
        self.df_positionbook.to_pickle(path)

def ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose,retries):
    
    while True:
            
        f1 = feeder(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose)
    
        try:

            f1.start()  
            print('Trying to restart feeder:', retries)
                
        except Exception as e:
            
            print(e)

            AppendLogFile(f1.symbol, e)
                
            retries += 1        
            print('Trying to restart feeder:', retries)
            ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose,retries)
            
        return f1

def AppendLogFile(symbol, error_message):
    
    path_logfile = '..\\..\\results_live\\log_feeder_{0}.log'.format(symbol)                
    f = open( path_logfile, 'a')
    f.write( '{}: Error: {} \n'.format(datetime.datetime.utcnow(), error_message) )
    f.close() 

if __name__ == '__main__':
   
    try:
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')
       
        symbol = sys.argv[1]
        granularity = sys.argv[2]
        account_type = sys.argv[3]
        socket_number = int(sys.argv[4])

        '''
       # For testing:
        symbol = 'EUR_USD'
        granularity = 'S5'
        account_type = 'live'
        socket_number = 5555
        ''' 
        
        daily_lookback = 10
        download_frequency = datetime.timedelta(seconds=60)
        update_signal_frequency = datetime.timedelta(seconds=60)
        download_data_start_date = datetime.datetime(2010,1,1,0,0,0,0,datetime.timezone.utc)
        download_data_end_date = None
        verbose = False
        
        print("--- FEEDER ---")
        print("symbol:", symbol)
        print("granularity:", granularity)
        print("account_type:", account_type)
        print("socket_number:", socket_number)
        print("--------------")
        
        if account_type not in ['live', 'practice', 'backtest']:
            print('Error in account type, it should be either live, practice, or backtest')
            time.sleep(30)
            exit()

        ContinueLooping(config,symbol,granularity,account_type,socket_number,download_frequency,update_signal_frequency,download_data_start_date,download_data_end_date,verbose,retries=0)
            
    except Exception as e:
        
        print( 'Error in starting the object' )
        print(e)
        AppendLogFile(symbol, e)
        
        
   
    