# -*- coding: utf-8 -*-

import datetime
import tables 
import tstables  
import os
import pandas as pd
from _utility_v2 import *
 
if __name__ == '__main__':

    account_type = 'live'
    symbol = 'EUR_USD'
    granularity = '1H'
    filename = '{}_{}.hdf'.format(symbol, granularity)
    df = read_hdf_file(filename)

    # Filter only bid prices  
    df = df[['bid_o', 'bid_h', 'bid_l', 'bid_c', 'volume']]

    # Change column names for better readibility
    df.columns = ['open', 'high', 'low', 'close', 'volume']

    # Create columns for model    
    df_reg = pd.DataFrame()
    df_reg['returns'] = np.log(df['close'] / df['close'].shift(1))
    df_reg.dropna(inplace=True)

    # Add lagged returns as predictors
    lags = 5
    
    cols = []
    for lag in range(1, lags + 1):
        col = 'lag_{}'.format(lag)
        df_reg[col] = df_reg['returns'].shift(lag)
        cols.append(col)
    
    df_reg.dropna(inplace=True)
    
    # Assign data to X and y from dataframe
    X = df_reg[cols].values
    y = df_reg['returns'].values

    X_train, X_test, y_train, y_test = split_train_test_data(X, y, 'ratio', split_ratio=0.80)

    list_models = ['LogisticRegression']
    
    fitted_models = {}
    
    cross_validation(list_models, fitted_models, X_train, y_train, scoring='accuracy', cv=3)


