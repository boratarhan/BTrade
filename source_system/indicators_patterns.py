import numpy as np
import talib
import pandas as pd

# integer = CDLDOJISTAR(open, high, low, close)
def Add_CDLDOJISTAR(df, indicator_list, askbidmid):
    
    df['CDLDOJISTAR'] = talib.CDLDOJISTAR(df['{}_o'.format(askbidmid)].values, df['{}_h'.format(askbidmid)].values, df['{}_l'.format(askbidmid)].values, df['{}_c'.format(askbidmid)].values )
    indicator_list.extend(['CDLDOJISTAR'])
    return df, indicator_list
