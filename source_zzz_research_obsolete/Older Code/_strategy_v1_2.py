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

    df_reg.describe()
    
    #plot_pairwise_distributions(df_reg)
    #plot_pairwise_correlation(df_reg)
    
    # Assign data to X and y from dataframe
    X = df_reg[cols]
    y = df_reg['returns']
    
    # Ordinary Linear Regression with polynomial terms added
    poly_reg = PolynomialFeatures(degree=5)
    X_poly = poly_reg.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)
    print( 'Intercept: {}    Coefficients: {}'.format(model.intercept_, model.coef_) )
    df_reg['returns_pred'] = model.predict(X_poly)
    
    # Joint plot
    sns.jointplot(x=X['lag_1'], y=y, kind='reg', height=10)
    plt.show()
    
    ax1 = sns.distplot(y, hist=False, color="r", label="Actual Value")
    sns.distplot(df_reg['returns_pred'], hist=False, color="b", label="Fitted Values" , ax=ax1)
    plt.show()
    
    df_reg[['returns','returns_pred']].plot()
    
    # Accuracy test:
    df_reg['sign_returns'] = np.sign(df_reg['returns'])
    df_reg['sign_returns_pred'] = np.sign(df_reg['returns_pred'])
    df_reg['hit'] = df_reg['sign_returns'] == df_reg['sign_returns_pred']
    print( df_reg['hit'].value_counts(normalize=True) )
    






    

    


