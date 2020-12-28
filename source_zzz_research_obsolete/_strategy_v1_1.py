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
    lags = 15
    
    cols = []
    for lag in range(1, lags + 1):
        col = 'lag_{}'.format(lag)
        df_reg[col] = df_reg['returns'].shift(lag)
        cols.append(col)
    
    df_reg.dropna(inplace=True)

    df_reg.describe()
    
    #plot_pairwise_distributions(df_reg)
    #plot_pairwise_correlation(df_reg)
    
    # Assign data to X and y from dataframe
    X = df_reg[cols].values
    y = df_reg['returns'].values
    
    split_ratio = 0.80
    dataindex = np.int( X.shape[0] * split_ratio )
    X_train, X_test, y_train, y_test = X[:dataindex], X[dataindex:], y[:dataindex], y[dataindex:]
        
    print('Observations: %d' % (len(X)))
    print('Training Observations: %d' % (len(X_train)))
    print('Testing Observations: %d' % (len(X_test)))
                
    # Ordinary Linear Regression
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(X_train, y_train)
    print( 'Intercept: {}    Coefficients: {}'.format(model.intercept_, model.coef_) )
    
    y_train_pred = model.predict(X_train)

    # Accuracy test:
    y_train_sign = np.sign(y_train)
    y_train_pred_sign = np.sign(y_train_pred)
    y_train_hit = y_train_sign == y_train_pred_sign
    unique, counts = np.unique(y_train_hit, return_counts=True)

    hit_matrix_train = np.asarray((unique, counts)).T
    hit_train_negative_rate = hit_matrix_train[0][1] / sum(hit_matrix_train[:,1])
    hit_train_positive_rate = hit_matrix_train[1][1] / sum(hit_matrix_train[:,1])
    print( 'Training Sample')
    print( 'Positive Rate: {} '.format(hit_train_positive_rate) )
    print( 'Negative Rate: {} '.format(hit_train_negative_rate) )    

    # Get predictions based on testing sample
    y_test_pred = model.predict(X_test)

    # Accuracy test:
    y_test_sign = np.sign(y_test)
    y_test_pred_sign = np.sign(y_test_pred)
    y_test_hit = y_test_sign == y_test_pred_sign
    unique, counts = np.unique(y_test_hit, return_counts=True)
    
    hit_matrix_test = np.asarray((unique, counts)).T
    hit_test_negative_rate = hit_matrix_test[0][1] / sum(hit_matrix_test[:,1])
    hit_test_positive_rate = hit_matrix_test[1][1] / sum(hit_matrix_test[:,1])
    print( 'Testing Sample')
    print( 'Positive Rate: {} '.format(hit_test_positive_rate) )
    print( 'Negative Rate: {} '.format(hit_test_negative_rate) )    
    
    
    # Plot actual and fitted values but in this case they do not match.    
    ax1 = sns.distplot(y_train, hist=False, color="r", label="Actual Value")
    sns.distplot(y_train_pred, hist=False, color="b", label="Fitted Values" , ax=ax1)
    plt.show()
    
    pd.DataFrame(np.c_[y_train, y_train_pred], columns=['train data', 'pred']).plot()
    
    pd.DataFrame(np.c_[y_test, y_test_pred], columns=['test data', 'pred']).plot()
