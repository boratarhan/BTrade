import numpy as np
import talib
import pandas as pd

def AddSMA(df, indicator_list, askbidmid, ohlc, length):
    column_name = 'SMA_{}_{}_{}'.format(length, askbidmid, ohlc)
    df[column_name] = talib.SMA(np.asarray(df['{}_{}'.format(askbidmid, ohlc)]), length)
    indicator_list.extend([column_name])
    return df, indicator_list

def AddWave(df, indicator_list, askbidmid, length):
    df['waveclose'] = talib.EMA(df['{}_c'.format(askbidmid)].values, length)
    df['wavehigh'] = talib.EMA(df['{}_h'.format(askbidmid)].values, length)
    df['wavelow'] = talib.EMA(df['{}_l'.format(askbidmid)].values, length)
    indicator_list.extend(['waveclose','wavehigh','wavelow'])
    return df, indicator_list

def AddWaveAngle(df, indicator_list, derivativelength=3):
    df_temp = pd.DataFrame()
    df_temp['Avg1'] = (df['wavehigh'] + df['wavelow'] + df['waveclose'])/3
    df_temp['Avg2'] = (df['wavehigh'].shift(derivativelength) + df['wavelow'].shift(derivativelength) + df['waveclose'].shift(derivativelength))/3
    df_temp['AvgDiff'] = df_temp['Avg1'] - df_temp['Avg2']
    df['waveangle'] = 1000 * df_temp['AvgDiff'] / df_temp['Avg1']
    indicator_list.extend(['waveangle'])
    return df, indicator_list

def AddMACD(df, indicator_list, askbidmid, fastperiod=12, slowperiod=26, signalperiod=9):
    df['macd'], df['macdsignal'], df['macdhist'] = talib.MACD(df['{}_c'.format(askbidmid)].values, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    indicator_list.extend(['macd','macdsignal','macdhist'])
    return df, indicator_list

def AddDMI(df, indicator_list, askbidmid, timeperiod=14):
    df['dmi_minus'] = talib.MINUS_DI( df['{}_h'.format(askbidmid)].values, df['{}_l'.format(askbidmid)].values, df['{}_c'.format(askbidmid)].values, timeperiod=timeperiod)
    df['dmi_plus'] =  talib.PLUS_DI(  df['{}_h'.format(askbidmid)].values, df['{}_l'.format(askbidmid)].values, df['{}_c'.format(askbidmid)].values, timeperiod=timeperiod)
    df['dmi_diff'] = df['dmi_plus'] - df['dmi_minus']
    indicator_list.extend(['dmi_minus','dmi_plus','dmi_diff'])
    return df, indicator_list

def AddRSI(df, indicator_list, askbidmid, timeperiod=14):
    df['rsi'] = talib.RSI(df['{}_c'.format(askbidmid)].values, timeperiod=timeperiod)
    indicator_list.extend(['rsi'])
    return df, indicator_list
        
def AddSlowStochastic(df, indicator_list, askbidmid, fastk_period=14, slowk_period=3, slowd_period=3):
    df['slowk'], df['slowd'] = talib.STOCH(df['{}_h'.format(askbidmid)].values, df['{}_l'.format(askbidmid)].values, df['{}_c'.format(askbidmid)].values, fastk_period=fastk_period, slowk_period=slowk_period, slowk_matype=1, slowd_period=slowd_period, slowd_matype=1)
    indicator_list.extend(['slowk', 'slowd'])
    return df, indicator_list

def AddATR(df, indicator_list, askbidmid, timeperiod=14):
    df['atr'] = talib.ATR(df['{}_h'.format(askbidmid)].values, df['{}_l'.format(askbidmid)].values, df['{}_c'.format(askbidmid)].values, timeperiod=timeperiod)
    df['atr+1'] = df['waveclose'] + 1 * df['atr']
    df['atr+2'] = df['waveclose'] + 2 * df['atr']
    df['atr+3'] = df['waveclose'] + 3 * df['atr']
    df['atr-1'] = df['waveclose'] - 1 * df['atr']
    df['atr-2'] = df['waveclose'] - 2 * df['atr']
    df['atr-3'] = df['waveclose'] - 3 * df['atr']
    indicator_list.extend(['atr+1','atr+2','atr+3','atr-1','atr-2','atr-3'])
    return df, indicator_list

def AddMinorHighLow(df, indicator_list, askbidmid):
    df['minorhigh'] = np.where(( df['{}_h'.format(askbidmid)] > df['{}_h'.format(askbidmid)].shift(1) )     \
                             & ( df['{}_h'.format(askbidmid)] > df['{}_h'.format(askbidmid)].shift(-1) )    \
                             & ( df['{}_l'.format(askbidmid)] > df['{}_l'.format(askbidmid)].shift(1) )     \
                             & ( df['{}_l'.format(askbidmid)] > df['{}_l'.format(askbidmid)].shift(-1) ), 1, 0)
    df['minorlow'] = np.where(( df['{}_h'.format(askbidmid)] < df['{}_h'.format(askbidmid)].shift(1) )      \
                             & ( df['{}_h'.format(askbidmid)] < df['{}_h'.format(askbidmid)].shift(-1) )    \
                             & ( df['{}_l'.format(askbidmid)] < df['{}_l'.format(askbidmid)].shift(1) )     \
                             & ( df['{}_l'.format(askbidmid)] < df['{}_l'.format(askbidmid)].shift(-1) ), 1, 0)
    indicator_list.extend(['minorhigh','minorlow'])
    return df, indicator_list

def AddDivergence(df, indicator_list, askbidmid, lookback, threshold):
    df['divergenceregularbuy'] = 0
    df['divergencehiddenbuy'] = 0
    df['divergenceregularsell'] = 0
    df['divergencehiddensell'] = 0
    
    for index, row in df.iterrows():
            
        if df.index.get_loc(index) >= lookback:
            
            loc = df.index.get_loc(index)
            print(loc)
            
            stopdivergenceregularbuy = False
            stopdivergencehiddenbuy = False
            stopdivergenceregularsell = False
            stopdivergencehiddensell = False
        
            temp = df[loc-lookback:loc]
            for index2, row2 in temp[::-1].iterrows():

                if( ( row2['{}_l'.format(askbidmid)] < df.ix[index]['{}_l'.format(askbidmid)] ) &
                    ( row2['slowk'] > df.ix[index]['slowk'] ) &
                    ( row2['slowk'] < 50 ) &
                    ( df.ix[index]['slowk'] < 50 ) &
                    ( np.abs( row2['{}_l'.format(askbidmid)] - df.ix[index]['{}_l'.format(askbidmid)] ) < threshold ) &
                    ( not stopdivergenceregularbuy ) ):

                    loc2 = df.index.get_loc(index2)
                    df['divergenceregularbuy'].ix[index] = loc-loc2
                    stopdivergenceregularbuy = True

                if( ( row2['{}_l'.format(askbidmid)] > df.ix[index]['{}_l'.format(askbidmid)] ) &
                    ( row2['slowk'] < df.ix[index]['slowk'] ) &
                    ( row2['slowk'] < 50 ) &
                    ( df.ix[index]['slowk'] < 50 ) &
                    ( np.abs( row['{}_l'.format(askbidmid)] - df.ix[index]['{}_l'.format(askbidmid)] ) < threshold ) &
                    ( not stopdivergencehiddenbuy ) ):

                    loc2 = df.index.get_loc(index2)
                    df['divergencehiddenbuy'].ix[index] = loc-loc2
                    stopdivergencehiddenbuy = True
                
                if( ( row2['{}_h'.format(askbidmid)] > df.ix[index]['{}_h'.format(askbidmid)] ) &
                    ( row2['slowk'] < df.ix[index]['slowk'] ) &
                    #( row['slowk'] > 50 ) &
                    #( df.ix[index]['slowk'] > 50 ) &
                    ( np.abs( row['{}_h'.format(askbidmid)] - df.ix[index]['{}_h'.format(askbidmid)] ) < threshold ) &
                    ( not stopdivergenceregularsell ) ):
                    
                    loc2 = df.index.get_loc(index2)
                    df['divergenceregularsell'].ix[index] = loc-loc2
                    stopdivergenceregularsell = True

                if( ( row2['{}_h'.format(askbidmid)] < df.ix[index]['{}_h'.format(askbidmid)] ) &
                    ( row2['slowk'] > df.ix[index]['slowk'] ) &
                    #( row['slowk'] > 50 ) &
                    #( df.ix[index]['slowk'] > 50 ) &
                    ( np.abs( row['{}_h'.format(askbidmid)] - df.ix[index]['{}_h'.format(askbidmid)] ) < threshold ) &
                    ( not stopdivergencehiddensell ) ):
                    
                    loc2 = df.index.get_loc(index2)
                    df['divergencehiddensell'].ix[index] = loc-loc2
                    stopdivergencehiddensell = True
                                
    indicator_list.extend(['divergenceregularbuy','divergencehiddenbuy','divergenceregularsell','divergencehiddensell'])
    return df, indicator_list

def AddDivergenceRegularBuyLast(df, indicator_list, askbidmid, lookback, threshold):
    df['divergenceregularbuy'] = 0
    
    for index, row in df[lookback:].iterrows():
            
        for index_lookback in range(0,lookback):
    
            if( ( row['{}_l'.format(askbidmid)] < df.ix[index-index_lookback-1]['{}_l'.format(askbidmid)] ) &
                ( row['slowk'] > df.ix[index-index_lookback-1]['slowk'] ) &
                ( row['slowk'] < 50 ) &
                ( df.ix[index-index_lookback-1]['slowk'] < 50 ) &
                ( np.abs( row['{}_l'.format(askbidmid)] - df.ix[index-index_lookback-1]['{}_l'.format(askbidmid)] ) < threshold ) ):
                
                df['divergenceregularbuy'].ix[index] = index_lookback+1
                break

    indicator_list.extend(['divergenceregularbuy'])
    return df, indicator_list

def AddDivergenceHiddenBuyLast(df, indicator_list, askbidmid, lookback, threshold):
    df['divergencehiddenbuy'] = 0
    
    for index, row in df[lookback:].iterrows():
            
        for index_lookback in range(0,lookback):
    
            if( ( row['{}_l'.format(askbidmid)] > df.ix[index-index_lookback-1]['{}_l'.format(askbidmid)] ) &
                ( row['slowk'] < df.ix[index-index_lookback-1]['slowk'] ) &
                ( row['slowk'] < 50 ) &
                ( df.ix[index-index_lookback-1]['slowk'] < 50 ) &
                ( np.abs( row['{}_l'.format(askbidmid)] - df.ix[index-index_lookback-1]['{}_l'.format(askbidmid)] ) < threshold ) ):
                
                df['divergencehiddenbuy'].ix[index] = index_lookback+1
                break
             
    indicator_list.extend(['divergencehiddenbuy'])
    return df, indicator_list

def AddDivergenceRegularSellLast(df, indicator_list, askbidmid, lookback, threshold):
    df['divergenceregularsell'] = 0
    
    for index, row in df[lookback:].iterrows():
            
        for index_lookback in range(0,lookback):
    
            if( ( row['{}_h'.format(askbidmid)] > df.ix[index-index_lookback-1]['{}_h'.format(askbidmid)] ) &
                ( row['slowk'] < df.ix[index-index_lookback-1]['slowk'] ) &
                #( row['slowk'] > 50 ) &
                #( df.ix[index-index_lookback-1]['slowk'] > 50 ) &
                ( np.abs( row['{}_h'.format(askbidmid)] - df.ix[index-index_lookback-1]['{}_h'.format(askbidmid)] ) < threshold ) ):
                
                df['divergenceregularsell'].ix[index] = index_lookback+1
                break
             
    indicator_list.extend(['divergenceregularsell'])
    return df, indicator_list

def AddDivergenceHiddenSellLast(df, indicator_list, askbidmid, lookback, threshold):
    df['divergencehiddensell'] = 0
    
    for index, row in df[lookback:].iterrows():
            
        for index_lookback in range(0,lookback):
    
            if( ( row['{}_h'.format(askbidmid)] < df.ix[index-index_lookback-1]['{}_h'.format(askbidmid)] ) &
                ( row['slowk'] > df.ix[index-index_lookback-1]['slowk'] ) &
                #( row['slowk'] > 50 ) &
                #( df.ix[index-index_lookback-1]['slowk'] > 50 ) &
                ( np.abs( row['{}_h'.format(askbidmid)] - df.ix[index-index_lookback-1]['{}_h'.format(askbidmid)] ) < threshold ) ):
                
                df['divergencehiddensell'].ix[index] = index_lookback+1
                break
             
    indicator_list.extend(['divergencehiddensell'])
    return df, indicator_list


#def AddDivergenceMACDDMI(df):
#    
#    df['DivergenceMACDDMI'] = 0
#    
#    for index, row in df[1:].iterrows():
#      
#        if( ( row['macd'] > df.ix[index-1]['macd'] ) &
#            ( row['dmi_plus'] < df.ix[index-1]['dmi_plus'] ) ):
#            
#            df['DivergenceMACDDMI'].ix[index] = -1
#
#        if( ( row['macd'] < df.ix[index-1]['macd'] ) &
#            ( row['dmi_minus'] < df.ix[index-1]['dmi_minus'] ) ):
#
#            df['DivergenceMACDDMI'].ix[index] = 1
#             
#    return df
#
#def AddLT_Long_Short_Sideways(df):
#    
#    df['LT_Long_Short_Sideways'] = 0
#    
#    for index, row in df[1:].iterrows():
#      
#        if( ( row['WaveAngle'] > 0 ) &
#            ( row['macdhist'] > df.ix[index-1]['macdhist'] ) ):
#            
#            df['LT_Long_Short_Sideways'].ix[index] = 1
#
#        elif( ( row['WaveAngle'] < 0 ) &
#                 ( row['macdhist'] < df.ix[index-1]['macdhist'] ) ):
#            
#            df['LT_Long_Short_Sideways'].ix[index] = -1
#
#        else:
#
#            df['LT_Long_Short_Sideways'].ix[index] = 0
#            
#    return df
#
#def AddHodrickPrescott(df, smoothingparameter=50000):
#
#    df['HP-Cycle'], df['HP-Trend'] = sm.tsa.filters.hpfilter(df['Close'], smoothingparameter)
#
#    return df

#def HeikinAshi(df):
#    df_temp = pd.DataFrame()
#    df_temp['HA_Close'] = (df['closeAskhigh'] + df['closeAsklow'] + df['closeAskopen'] + df['closeAskclose'])/4
#    df_temp['HA_Open'] = (df['closeAskopen'].shift() + df['closeAskclose'].shift())/2
#    df_temp['HA_High'] = df[['closeAskhigh','closeAskopen','closeAskclose']].max(axis=1)
#    df_temp['HA_Low'] = df[['closeAsklow','closeAskopen','closeAskclose']].min(axis=1)
#    df = df.join(df_temp)
#    return df

