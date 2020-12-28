# -*- coding: utf-8 -*-

import datetime
import tables 
import tstables  
import os
import numpy as np
np.random.seed(42) # to make this notebook's output stable across runs
import pandas as pd
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rc('axes', labelsize=14)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
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

        dataindex = np.int(X.shape[0] * split_ratio)
        X_train, X_test, y_train, y_test = X[:dataindex], X[dataindex:], y[:dataindex], y[dataindex:]
        
    print('Observations: %d' % (len(X)))
    print('Training Observations: %d' % (len(X_train)))
    print('Testing Observations: %d' % (len(X_test)))

    return X_train, X_test, y_train, y_test


def plot_pairwise_distributions(df):
    
    sns.pairplot(df, height=1.5);
    plt.show()
    
def plot_pairwise_correlation(df):
    pd.options.display.float_format = '{:,.2f}'.format
    df.corr()
    
    plt.figure(figsize=(16,10))
    sns.heatmap(df.corr(), annot=True)
    plt.show()


def cross_validation(list_models, fitted_models, X_train, y_train, scoring, cv):
        
    for eModel in list_models:
        
        if eModel == 'SGDClassifier':

            from sklearn.linear_model import SGDClassifier
            clf_sgd = SGDClassifier(max_iter=1000, tol=1e-3, random_state=42)
            scores = cross_val_score(clf_sgd, X_train, y_train, scoring=scoring, cv=cv)

            fitted_models[eModel] = {}
            fitted_models[eModel]['model'] = clf_sgd
            fitted_models[eModel]['Scores'] = scores
            fitted_models[eModel]['Mean'] = scores.mean()
            fitted_models[eModel]['Standard deviation'] = scores.std()
    
            y_scores = cross_val_predict(clf_sgd, X_train, y_train, cv=cv, method='decision_function')

            classification_performance_measure(fitted_models, eModel, clf_sgd, X_train, y_train, cv, y_scores)
            
        if eModel == 'RandomForestClassifier':
            
            from sklearn.ensemble import RandomForestClassifier
            clf_forest = RandomForestClassifier(n_estimators=100, random_state=42)

            y_probas_forest = cross_val_predict(clf_forest, X_train, y_train, cv=3, method="predict_proba")
            y_scores = y_probas_forest[:, 1] # Positive class probabilities
                        
            fitted_models[eModel] = {}
            fitted_models[eModel]['model'] = clf_forest

            classification_performance_measure(fitted_models, eModel, clf_forest, X_train, y_train, cv, y_scores)
  
        if eModel == 'LogisticRegression':
            
            from sklearn.linear_model import LogisticRegression
            train_samples = X_train.shape[0]
            #reg_log = LogisticRegression()
            reg_log = LogisticRegression(C=50. / train_samples, penalty='l1', solver='saga', tol=0.1)
            
            y_probas_log = cross_val_predict(reg_log, X_train, y_train, cv=3, method="predict_proba")
            y_scores = y_probas_log[:, 1] # Positive class probabilities
            
            fitted_models[eModel] = {}
            fitted_models[eModel]['model'] = reg_log
            
            classification_performance_measure(fitted_models, eModel, reg_log, X_train, y_train, cv, y_scores)

        if eModel == 'SGDRegressor':
            
            from sklearn.linear_model import SGSRegressor
            reg_sgd = SGSRegressor(max_iter=1000, tol=1e-3, penalty=None, eta0=0.1)

            print('MISSING FITTING')

            fitted_models[eModel] = {}
            fitted_models[eModel]['model'] = reg_sgd
            
def classification_performance_measure(fitted_models, eModel, clf, X_train, y_train, cv, y_scores):

    y_train_pred = cross_val_predict(clf, X_train, y_train, cv=cv)
    precisions, recalls, thresholds = precision_recall_curve(y_train, y_scores)

    fitted_models[eModel]['confusion_matrix'] = confusion_matrix(y_train, y_train_pred)
    fitted_models[eModel]['precision'] = precisions
    fitted_models[eModel]['recall'] = recalls
    fitted_models[eModel]['f1_score'] = f1_score(y_train, y_train_pred)
    plot_precision_recall_vs_threshold(precisions, recalls, thresholds)
    
    plot_precision_vs_recall(precisions, recalls)
    
    fpr, tpr, thresholds = roc_curve(y_train, y_scores)
    fitted_models[eModel]['roc_auc'] = roc_auc_score(y_train, y_scores)
    plot_roc_curve(fpr, tpr)            
            
def plot_precision_recall_vs_threshold(precisions, recalls, thresholds):
    
    plt.plot(thresholds, precisions[:-1], "b--", label="Precision")
    plt.plot(thresholds, recalls[:-1], "g-", label="Recall")
    plt.legend(loc="center right", fontsize=16)
    plt.xlabel("Threshold", fontsize=16)
    plt.grid(True)
    #plt.axis([-50000, 50000, 0, 1])
    plt.legend()
    plt.show()              
            
def plot_precision_vs_recall(precisions, recalls):
    plt.plot(recalls, precisions, "b-", linewidth=2)
    plt.xlabel("Recall", fontsize=16)
    plt.ylabel("Precision", fontsize=16)
    plt.axis([0, 1, 0, 1])
    plt.grid(True)
    plt.show()
    
def plot_roc_curve(fpr, tpr, label=None):
    
    plt.plot(fpr, tpr, linewidth=2, label=label)
    plt.plot([0,1], [0,1], 'k--')
    plt.axis([0, 1, 0, 1])                                    # Not shown in the book
    plt.xlabel('False Positive Rate (Fall-Out)', fontsize=16) # Not shown
    plt.ylabel('True Positive Rate (Recall)', fontsize=16)    # Not shown
    plt.title('Receiver Operating Characteristic (ROC)')
    plt.grid(True)   
    plt.show()            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            















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




