
import datetime
import pandas as pd
import os
import tstables  
import tables 
import utility_functions as uf
import time

account_type = 'live'
symbol = 'EUR_USD'
granularity = 'S5'

uf.read_database(symbol, granularity, account_type)

symbol = 'USD_TRY'
account_type = 'practice'
granularity = 'S5'
        
uf.combine_databases(symbol, granularity, account_type)

