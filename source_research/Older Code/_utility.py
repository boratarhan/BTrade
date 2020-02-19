# -*- coding: utf-8 -*-

import datetime
import tables 
import tstables  
import os
import numpy as np
np.random.seed(42) # to make this notebook's output stable across runs
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rc('axes', labelsize=14)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)

from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedShuffleSplit # Example on p55 on Geron
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error, confusion_matrix, precision_score, recall_score, f1_score, precision_recall_curve, roc_curve, roc_auc_score
from sklearn.impute import SimpleImputer



def read_database(account_type, symbol, granularity, read_start_dt, read_end_dt):
    
    # Reading ts file
    file_path = '..\\..\\datastore\\_{0}\\{1}\\{2}.h5'.format(account_type,symbol,granularity)

    f = tables.open_file(file_path,'r')
    ts = f.root.data._f_get_timeseries()

    rows = ts.read_range(read_start_dt,read_end_dt)
    
    f.close()

    return rows

def read_hdf_file(filename):
    df_temp = pd.DataFrame()
    filepath = os.path.join('..', '..', 'backtests', filename)
    if os.path.exists( filepath ):
        df_temp = pd.read_hdf(filepath)
    return df_temp

def write_hdf_file(df, filename):
    filepath = os.path.join('..', '..', 'backtests', filename)
    df.to_hdf(filepath, 'time', mode='w')

def add_polynomial_features_model(X, degree=2):
    
    poly_features = PolynomialFeatures(degree=degree, include_bias=True)
    X_poly = poly_features.fit_transform(X)
    
    return X_poly

def split_train_test_data(X, y, based_on, dataindex=0, split_ratio=0):
    
    if based_on == 'random':
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, random_state=0)

    elif based_on == 'index':
        
        X_train, X_test, y_train, y_test = X[:dataindex], X[dataindex:], y[:dataindex], y[dataindex:]

    elif based_on == 'ratio':

        dataindex = X.shape()[0] * split_ratio
        X_train, X_test, y_train, y_test = X[:dataindex], X[dataindex:], y[:dataindex], y[dataindex:]
        
    print('Observations: %d' % (len(X)))
    print('Training Observations: %d' % (len(X_train)))
    print('Testing Observations: %d' % (len(X_test)))

    return X_train, X_test, y_train, y_test








def split_train_test_data_by_ratio(symbol, granularity, split_ratio):

    filename = '{}_{}.hdf'.format(symbol, granularity)
    rows = read_hdf_file(filename)
    
    train_size = int(len(rows.values) * split_ratio)
    
    rows_train, rows_test = rows[0:train_size], rows[train_size:len(rows)]
    
    print('Observations: %d' % (len(rows)))
    print('Training Observations: %d' % (len(rows_train)))
    print('Testing Observations: %d' % (len(rows_test)))
    
    return rows_train, rows_test

def split_train_test_validation_data_randomly(symbol, granularity, split_ratio):

    filename = '{}_{}.hdf'.format(symbol, granularity)
    rows = read_hdf_file(filename)

    train_set, test_valid_set = train_test_split(rows, test_size=0.2, random_State=42)
    test_set, valid_set = train_test_split(test_valid_set, test_size=0.2, random_State=42)
    
    return train_set, test_set, valid_set

def split_train_test_data_stratified(symbol, granularity, split_ratio):

    filename = '{}_{}.hdf'.format(symbol, granularity)
    rows = read_hdf_file(filename)

    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_State=42)
    split_index = list( range( sss.get_n_splits() ) )
    
    stratified_data = {}
    split_key = 0
    
    for train_index, test_index in sss.split(rows, rows['X']):
        stratified_data[split_key] = {}
        stratified_data['train_set'] = rows.loc[train_index]
        stratified_data['test_set'] = rows.loc[test_index]
        split_key = split_key + 1
            
    return stratified_data




