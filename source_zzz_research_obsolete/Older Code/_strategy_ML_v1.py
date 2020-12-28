# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rc('axes', labelsize=14)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)

import numpy as np
np.random.seed(42) # to make this notebook's output stable across runs

from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedShuffleSplit # Example on p55 on Geron
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, precision_recall_curve, roc_curve, roc_auc_score
from sklearn.model_selection import GridSearchCV

from sklearn.impute import SimpleImputer



'''

def get_correlation_matrix(df, columns):
    
    return df[columns].corr()


def impute_missing_data(df, strategy="median"):
    
    imputer = SimpleImputer(strategy)
    
    imputer.fit(df)
    
    df = imputer.transform(df, columns=df.columns, index=df.index)


parameter_grid = [{'parameter1:': [1,2,3], 'parameter2:': [1,2,3]}, 
                  {'parameter3:': [1,2,3], 'parameter4:': [1,2,3]}] # Example p76 on Geron
 
def grid_Search(estimator, parameter_grid, df, y, cv=10, scoring='neg_mean_squared_error'):
    
    grid_search = GridSearchCV(estimator, param_grid, cv, scoring, return_train_score=True)
    
    grid_search.fit(df, y)
    
'''

def get_mnist_data():

    from sklearn.datasets import fetch_openml
    
    mnist = fetch_openml('mnist_784', version=1)
    print(mnist.keys())
    
    X = mnist['data']
    y = mnist['target']
        
    y = y.astype(np.uint8)
    
    return X, y

def add_polynomial_features_model(X, degree=2):
    
    from sklearn.preprocessing import PolynomialFeatures
    poly_features = PolynomialFeatures(degree=degree, include_bias=True)
    X_poly = poly_features.fit_transform(X)
    
    return X_poly


def train_test_model():
    
    X, y = get_mnist_data()
    
    print( X.shape, y.shape )
    
    plot_mnist_data(X[0])

    X_train, X_test, y_train, y_test = split_train_test_data(X, y, 'random')#, dataindex=60000)

    y_train = ( y_train == 5 )
    y_test = ( y_test == 5 )

    list_models = ['SGDClassifier']
        
    cross_validation(list_models, scoring='accuracy', cv=3)
    
def split_train_test_data(X, y, based_on, dataindex=0):
    
    if based_on == 'random':
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, random_state=0)

    elif based_on == 'index':
        
        X_train, X_test, y_train, y_test = X[:dataindex], X[dataindex:], y[:dataindex], y[dataindex:]
        
    return X_train, X_test, y_train, y_test
    
    
def plot_mnist_data(digit):

    digit_image = digit.reshape(28,28)
    plt.imshow(digit_image, cmap='binary')
    plt.axis("off")
    plt.show()

def modeling(list_models, X_train, y_train):

    fitted_models = {}
        
    for eModel in list_models:
        
        if eModel == 'SGDClassifier':
            
            from sklearn.linear_model import SGDClassifier
            clf_sgd = SGDClassifier(random_state=42)
            clf_sgd.fit(X_train, y_train)
            fitted_models[eModel] = clf_sgd
            print('SGDClassifier fitted')

        else:
            
            print('Model {} is missing'.format(eModel))

    return fitted_models

def plot_precision_recall_vs_threshold(precisions, recalls, thresholds):
    
    plt.plot(thresholds, precisions[:-1], "b--", label="Precision")
    plt.plot(thresholds, recalls[:-1], "g-", label="Recall")
    plt.legend(loc="center right", fontsize=16)
    plt.xlabel("Threshold", fontsize=16)
    plt.grid(True)
    #plt.axis([-50000, 50000, 0, 1])
    plt.legend()
    plt.show()    

def calculate_threshold_given_desired_precision(precisions, thresholds, desired_precision):
    
    return thresholds[np.argmax(precisions >= desired_precision)]

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
    
def cross_validation(list_models, fitted_models, scoring, cv):
        
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
            
          
def cross_val_score_alternative(model, X_train, y_train, ):

    from sklearn.model_selection import StratifiedKFold
    from sklearn.base import clone
    
    skfolds = StratifiedKFold(n_splits=3, random_state=42)
    
    for train_index, test_index in skfolds.split(X_train, y_train):
        clone_clf = clone(model)
        X_train_folds = X_train[train_index]
        y_train_folds = y_train[train_index]
        X_test_fold = X_train[test_index]
        y_test_fold = y_train[test_index]
    
        clone_clf.fit(X_train_folds, y_train_folds)
        y_pred = clone_clf.predict(X_test_fold)
        n_correct = sum(y_pred == y_test_fold)
        print(n_correct / len(y_pred))
            
if __name__ == '__main__':
        
    #run_classification_example('mnist')

    X, y = get_mnist_data()
     
    print( X.shape, y.shape )
    
    plot_mnist_data(X[0])

    X_train, X_test, y_train, y_test = split_train_test_data(X, y, 'random')
    #X_train, X_test, y_train, y_test = split_train_test_data(X, y, 'index', dataindex=60000)
    
    y_train = ( y_train == 5 )
    y_test = ( y_test == 5 )
    
    list_models = ['SGDClassifier', 'RandomForestClassifier', 'LogisticRegression']
    
    fitted_models = {}
    
    cross_validation(list_models, fitted_models, scoring='accuracy', cv=3)
    
    
    

    
    