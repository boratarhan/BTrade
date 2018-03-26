import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
from oandapyV20.exceptions import V20Error
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

class portfolio(object):
    
    def __init__(self,config,account_type,socket_number):

        self.config = config
        self.account_type = account_type
        self.socket_number = socket_number
        
        self.context_sub = zmq.Context()
        self.socket_sub = self.context_sub.socket(zmq.SUB)
        self.socket_sub.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket_sub.connect("tcp://127.0.0.1:{}".format(self.socket_number))
        
        self.position = {}

        self.start()

    def connect_broker_live(self):

        self.accountID = self.config['oanda_v20']['account_number_live']
        self.access_token = self.config['oanda_v20']['access_token_live']
        self.api = oandapyV20.API(access_token=self.access_token)

    def connect_broker_practice(self):

        self.accountID = self.config['oanda_v20']['account_number_practice']
        self.access_token = self.config['oanda_v20']['access_token_practice']
        self.api = oandapyV20.API(access_token=self.access_token, environment="practice")

    def create_order(self, symbol, units):
        ''' Places orders with Oanda. 
            if units < 0 means short
            if units > 0 means long
        '''
        
        orderinfo = { "order": {"type": "MARKET",
                                "instrument": symbol,
                                "units": units,
                                "timeInForce": "FOK",
                                "positionFill": "DEFAULT" }
                    }
                    
        r = orders.OrderCreate(self.accountID, data=orderinfo)
        self.api.request(r)
        
        if units < 0:
            
            print('{} Sell Orders Sent'.format(units) )

        elif units < 0:
            
            print('{} Buy Orders Sent'.format(units) )
        
        else:
            
            print('Error in create order function - units is zero')

        print(r.response['orderCreateTransaction'])
        
    def wait_order_signals(self):

        while True:
       
            msg = self.socket_sub.recv_string()
            print("Received message: {0}".format(msg))
            longshort, symbol = msg.split()

            self.get_positions_for_instruments()
            
            if self.position[symbol] > 0:

                if longshort == 'Short':

                    units = 2
                    self.create_order(symbol,-units)
                
            if self.position[symbol] < 0:

                if longshort == 'Long':
                
                    units = 2
                    self.create_order(symbol,units)

            if self.position[symbol] == 0:
                
                if longshort == 'Short':

                    units = 1
                    self.create_order(symbol,-units)
                    
                elif longshort == 'Long':

                    units = 1
                    self.create_order(symbol,units)

            self.get_positions_for_instruments()
                                     
    def get_instrument_list(self):

        r = accounts.AccountInstruments(accountID=self.accountID)
        self.api.request(r)
        self.instruments = pd.DataFrame(r.response['instruments'])['name'].values
                                      
    def get_positions_for_instruments(self):

        r = accounts.AccountDetails(accountID=self.accountID)
        df = pd.DataFrame(self.api.request(r))

        for symbol in self.instruments:
            
            self.position[symbol] = 0

            for e_position in df['account']['positions']:
                
                if symbol == e_position['instrument']:
                
                    self.position[symbol] = int(e_position['long']['units'])+int(e_position['short']['units'])
            
    def start(self):

        print('Portfolio Ready to go')
        
        if( self.account_type == 'live'):
            
            self.connect_broker_live()
            
        elif( self.account_type == 'practice'):

            self.connect_broker_practice()

        self.get_instrument_list()
        self.get_positions_for_instruments()
           
        self.wait_order_signals()

if __name__ == '__main__':
        
    try:
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')
       
    except:
        print( 'Error in reading configuration file' )

    account_type = 'practice'
    socket_number = 5554
       
    p1 = portfolio(config,account_type,socket_number)


#            params = { "instruments": "EUR_USD,EUR_JPY" }
#            r = pricing.PricingInfo(accountID=self.accountID,params=params)
#            self.api.request(r)
#            print(r.response)
#            

#            
#            r = accounts.AccountList()
#            self.api.request(r)
#            print(r.response)
#
#            r = accounts.AccountSummary(accountID=self.accountID)
#            self.api.request(r)
#            print(r.response)
#
