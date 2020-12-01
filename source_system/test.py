import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
from oandapyV20.exceptions import V20Error
import oandapyV20.endpoints.forexlabs as labs
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
    
    def __init__(self,config,account_type,socket_number):

        self.config = config
        self.account_type = account_type
        self.socket_number = socket_number
        
        self.context_sub = zmq.Context()
        self.socket_sub = self.context_sub.socket(zmq.SUB)
        self.socket_sub.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket_sub.connect("tcp://127.0.0.1:{}".format(self.socket_number))
        
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

    def get_instrument_list(self):

        r = accounts.AccountInstruments(accountID=self.accountID)
        self.api.request(r)
        self.instruments = pd.DataFrame(r.response['instruments'])['name'].values
                                      
    def get_positions_for_all_instruments(self):

        r = accounts.AccountDetails(accountID=self.accountID)
        df = pd.DataFrame(self.api.request(r))
            
        for symbol in self.instruments:
            
            self.position[symbol] = 0.0

        print('Positions:') 
        for e_position in df['account']['positions']:
            
            self.position[e_position['instrument']] = int(e_position['long']['units'])+int(e_position['short']['units'])

            if self.position[e_position['instrument']] != 0:
                print('{}: {}'.format(e_position['instrument'], self.position[e_position['instrument']]) ) 
        print("--------------------------------------")
        
    def get_account_value(self):

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
        print("NEED TO UNDERSTAND THESE...")
        '''
        marginCloseoutNAV
        marginCloseoutPositionValue
        marginCloseoutMarginUsed
        resettablePL
        '''      
        print("--------------------------------------")

if __name__ == '__main__':
        
    try:
        
        config = configparser.ConfigParser()
        config.read('..\..\configinfo.cfg')

    except:
        print( 'Error in reading configuration file' )
        exit()

    try:
        
        account_type = 'live'
        socket_number = 5554
    
        print("---- PORTFOLIO -----------------------")
        print("account_type:", account_type)
        print("socket_number:", socket_number)
        print("--------------------------------------")
            
        p1 = portfolio(config,account_type,socket_number)
        
        p1.connect_broker()
    
        #p1.get_instrument_list()
        #r = accounts.AccountInstruments(accountID=p1.accountID)
        #r = accounts.AccountDetails(accountID=p1.accountID)
        #df = pd.DataFrame(p1.api.request(r))
        p1.get_instrument_list()
        #p1.get_positions_for_all_instruments()
        #p1.get_account_value()


        params = {"instrument": "EUR_USD", "period": 217728000 }

        r = labs.Calendar(params=params)
        #r = labs.CommitmentOfTraders(params=params)
        #r = instruments.InstrumentsOrderBook(instrument="EUR_USD")
        df = pd.DataFrame(p1.api.request(r))
        
        #p1.api.request(r)
        #print(r.response)
       
    except:
        print( 'Error in starting portfolio object' )
        
        
        '''
        df = pd.DataFrame(r.response['instruments'])
    
        filepath = 'C:\\Users\\boratarhan\\Google Drive\\_Github\\datastore_results\\api1.xlsx'
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        df.to_excel(writer)
        writer.save()
        '''
                
        

