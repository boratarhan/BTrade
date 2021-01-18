
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
from sklearn.metrics import mean_squared_error, confusion_matrix, precision_score, recall_score, f1_score, precision_recall_curve, roc_curve, roc_auc_score
from sklearn.model_selection import GridSearchCV

from sklearn.impute import SimpleImputer

def write2excel( df, filename ):
    filepath = os.path.join('..', '..',  '..', 'datastore', filename) + '.xlsx'
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    df.to_excel(writer )
    writer.save()
    
def add_polynomial_features_model(X, degree=2):
    
    from sklearn.preprocessing import PolynomialFeatures
    poly_features = PolynomialFeatures(degree=degree, include_bias=True)
    X_poly = poly_features.fit_transform(X)
    
    return X_poly

def train_test_model(model, X, y):

    X_train, X_test, y_train, y_test = split_train_test_data(X, y, 'random')

    train_errors, test_errors = [], []
    for m in range(1, len(X_train)):

        model.fit(X_train[:m], y_train[:m])

        y_train_predict = model.predict(X_train[:m])
        y_test_predict = model.predict(X_test)

        train_errors.append(mean_squared_error(y_train[:m], y_train_predict))
        test_errors.append(mean_squared_error(y_test, y_test_predict))

    plt.plot(np.sqrt(train_errors), "r-+", linewidth=2, label="train")
    plt.plot(np.sqrt(test_errors), "b-", linewidth=3, label="val")
    plt.legend(loc="upper right", fontsize=14)   # not shown in the book
    plt.xlabel("Training set size", fontsize=14) # not shown
    plt.ylabel("RMSE", fontsize=14)              # not shown

def split_train_test_data(X, y, based_on, dataindex=0):
    
    if based_on == 'random':
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, random_state=0)
        print( 'Random {} points are allocated for training'.format(X_train.shape[0]))
        print( 'Random {} points are allocated for training'.format(X_test.shape[0]))
        
    elif based_on == 'index_number':
        
        X_train, X_test, y_train, y_test = X[:dataindex], X[dataindex:], y[:dataindex], y[dataindex:]
        print( 'First {} points are allocated for training'.format(X_train.shape[0]))
        print( 'Following {} points are allocated for training'.format(X_test.shape[0]))
        
    elif based_on == 'index_percent':
        
        dataindex = int(X.shape[0] * dataindex)
        X_train, X_test, y_train, y_test = X[:dataindex], X[dataindex:], y[:dataindex], y[dataindex:]
        print( 'First {} points are allocated for training'.format(X_train.shape[0]))
        print( 'Following {} points are allocated for training'.format(X_test.shape[0]))
               
    return X_train, X_test, y_train, y_test
    
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
    
def cross_validation(list_models, X_train, y_train, scoring, cv):
    
    fitted_models = {key: None for key in list_models} 
    
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

            y_probas_forest = cross_val_predict(clf_forest, X_train, y_train, cv=cv, method="predict_proba")
            y_scores = y_probas_forest[:, 1] # Positive class probabilities
                        
            fitted_models[eModel] = {}
            fitted_models[eModel]['model'] = clf_forest

            classification_performance_measure(fitted_models, eModel, clf_forest, X_train, y_train, cv, y_scores)
  
        if eModel == 'LogisticRegression':
            
            from sklearn.linear_model import LogisticRegression
            train_samples = X_train.shape[0]
            #reg_log = LogisticRegression()
            #reg_log = LogisticRegression(C=50. / train_samples, penalty='l1', solver='saga', tol=0.1)
            reg_log = LogisticRegression(solver='newton-cg')
            
            y_probas_log = cross_val_predict(reg_log, X_train, y_train, cv=cv, method="predict_proba")
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
            
          

    
    