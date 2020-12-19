# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 22:52:43 2020

@author: boratarhan
"""

import time
import datetime
import pandas as pd

current_time = datetime.datetime.now()
print(current_time)
past_minute = current_time.minute

while True:

    current_minute = datetime.datetime.now().minute

    if current_minute > past_minute:
        print("new minute")
        print(datetime.datetime.now())
        past_minute = datetime.datetime.now().minute
        
        time.sleep(5)
        print("Request now: {}".format(datetime.datetime.now()))
        
        
    
    