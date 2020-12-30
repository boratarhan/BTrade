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
import sys
import configparser
    
class portfolio(object):

    '''
    Portfolio object receives signals from multiple strategy objects and sends buy/sell/close signals to broker.
        
    '''    
    def __init__(self,config,account_type,socket_number):

        self.config = config
        self.account_type = account_type
        self.socket_number = socket_number
        
        '''
        Subscribe to the feeds coming from strategy objects
        '''
        self.context_sub = zmq.Context()
        self.socket_sub = self.context_sub.socket(zmq.SUB)
        self.socket_sub.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket_sub.set_hwm(0)
        self.socket_sub.bind("tcp://127.0.0.1:{}".format(self.socket_number))
        
        self.position = {}

        self.NAV = 0.0
        self.unrealizedPL = 0.0
        self.positionValue = 0.0
        self.marginUsed = 0.0
        self.marginAvailable = 0.0
       
    def connect_broker(self):

        ''' 
        Connect to OANDA through account ID and access token based on account type.
        '''    
        
        try: 
   
            self.accountID = self.config['oanda_v20']['account_number_{}'.format(self.account_type)]
            self.access_token = self.config['oanda_v20']['access_token_{}'.format(self.account_type)]
            self.api = oandapyV20.API(access_token=self.access_token, environment="{}".format(self.account_type))
    
        except V20Error as err:
            print("V20Error occurred: {}".format(err))
        
    def create_order(self, order_type, symbol, units, priceBound, limit_price, takeProfitOnFill, stopLossOnFill):
        ''' 
        Places orders with Oanda. 
        if units < 0 means short
        if units > 0 means long
        '''
        
        orderinfo = {}
        
        if order_type == "MARKET":

            orderinfo = { "order": {"type": "MARKET",
                                    "instrument": symbol,
                                    "units": units,
                                    "timeInForce": "FOK",
                                    "positionFill": "DEFAULT" }
                                }
            
            if priceBound != 0.0:
                orderinfo = { "order": {"priceBound": priceBound} }
            if takeProfitOnFill != 0.0:
                orderinfo = { "order": {"takeProfitOnFill": takeProfitOnFill} }                
            if stopLossOnFill != 0.0:
                orderinfo = { "order": {"stopLossOnFill": stopLossOnFill} }
                
        if order_type == "LIMIT":
            
            orderinfo = { "order": {"type": "LIMIT",
                                    "instrument": symbol,
                                    "units": units,
                                    "price": limit_price,
                                    "timeInForce": "GTC",
                                    "positionFill": "DEFAULT" }
                               }
    
            if takeProfitOnFill != 0.0:
                orderinfo = { "order": {"takeProfitOnFill": takeProfitOnFill} }                
            if stopLossOnFill != 0.0:
                orderinfo = { "order": {"stopLossOnFill": stopLossOnFill} }            
                     
        r = orders.OrderCreate(self.accountID, data=orderinfo)
        self.api.request(r)
        
        if units < 0:
            
            print('{} Sell {} order is sent'.format(order_type, units) )

        elif units > 0:
            
            print('{} Buy {} order is sent'.format(order_type, units) )
        
        else:
            
            print('Error in create order function - units is zero')

        print(r.response['orderCreateTransaction'])
        
    def wait_order_signals(self):

        while True:

            msg = self.socket_sub.recv_string()
            print("Received message: {0}".format(msg))
            order_type, longshort, symbol, units, priceBound, limit_price, takeProfitOnFill, stopLossOnFill = msg.split()
                        
            units = int(units)
            priceBound = float(priceBound)
            limit_price = float(limit_price)
            takeProfitOnFill = float(takeProfitOnFill)
            stopLossOnFill = float(stopLossOnFill)
            
            print(order_type, longshort, symbol, units, priceBound, limit_price, takeProfitOnFill, stopLossOnFill)

            if longshort == 'Short':
                
                self.create_order(order_type, symbol, -units, priceBound, limit_price, takeProfitOnFill, stopLossOnFill)
    
            if longshort == 'Long':
                
                self.create_order(order_type, symbol, units, priceBound, limit_price, takeProfitOnFill, stopLossOnFill)

            self.get_positions_for_all_instruments()
                                     
    def get_instrument_list(self):

        '''
        Request all eligible assets to trade
        '''
        r = accounts.AccountInstruments(accountID=self.accountID)
        self.api.request(r)
        self.instruments = pd.DataFrame(r.response['instruments'])['name'].values
                                                          
    def get_positions_for_all_instruments(self):

        '''
        Get current positions for all assets
        Long positions are positive 
        Short positions are negative
        '''
        for symbol in self.instruments:
            
            self.position[symbol] = 0.0

        r = accounts.AccountDetails(accountID=self.accountID)
        df = pd.DataFrame(self.api.request(r))
                
        print('Net Positions:') 

        for e_position in df['account']['positions']:
                        
            self.position[e_position['instrument']] = int(e_position['long']['units'])+int(e_position['short']['units'])

            if self.position[e_position['instrument']] != 0:
                print('{}: {}'.format(e_position['instrument'], self.position[e_position['instrument']]) ) 

        print("--------------------------------------")
        
    def get_account_value(self):

        '''
        Get current account value, P&L, and margin information
        '''
        r = accounts.AccountDetails(accountID=self.accountID)
        self.NAV = pd.DataFrame(self.api.request(r))['account']['NAV']
        self.unrealizedPL = pd.DataFrame(self.api.request(r))['account']['unrealizedPL']
        self.positionValue = pd.DataFrame(self.api.request(r))['account']['positionValue']
        self.marginUsed = pd.DataFrame(self.api.request(r))['account']['marginUsed']
        self.marginAvailable = pd.DataFrame(self.api.request(r))['account']['marginAvailable']

        print('Account Values:')
        print('NAV:             ', self.NAV)
        print('Unrealized P&L:  ', self.unrealizedPL)
        print('Position Value:  ', self.positionValue)
        print('Margin Used:     ', self.marginUsed)
        print('Marging Available', self.marginAvailable)
        print("--------------------------------------")

        '''
        NEED TO UNDERSTAND THESE...
        marginCloseoutNAV
        marginCloseoutPositionValue
        marginCloseoutMarginUsed
        resettablePL
        '''      
            
    def start(self):
        
        self.connect_broker()

        self.get_instrument_list()

        self.get_positions_for_all_instruments()
        
        self.get_account_value()

        print('Portfolio Ready to go')
           
        self.wait_order_signals()
        
def AppendLogFile(error_message):
    
    path_logfile = '..\\..\\results_live\\log_portfolio.log'
    f = open( path_logfile, 'a')
    f.write( '{}: Error: {} \n'.format(datetime.datetime.utcnow(), error_message) )
    f.close() 
        
if __name__ == '__main__':
        
    try:
        
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')

    except:
                
        print( 'Error in reading configuration file' )

    try:

        account_type = sys.argv[1]
        socket_number = int(sys.argv[2])

        '''
        # For testing:
        account_type = 'practice'
        socket_number = 5554
        '''
        
        print("---- PORTFOLIO -----------------------")
        print("account_type:", account_type)
        print("socket_number:", socket_number)
        print("--------------------------------------")
            
        p1 = portfolio(config,account_type,socket_number)
        p1.start()

    except Exception as e:

        print( 'Error in starting portfolio object' )

        AppendLogFile(e)
        
        time.sleep(30)
        
