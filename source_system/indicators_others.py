try:
    
    import numpy as np
    import talib
    import pandas as pd

except Exception as e:
    
    print(e) 
    
# integer = CDLDOJISTAR(open, high, low, close)
def Add_CDLDOJISTAR(df, indicator_list, askbidmid):
    
    df['CDLDOJISTAR'] = talib.CDLDOJISTAR(df['{}_o'.format(askbidmid)].values, df['{}_h'.format(askbidmid)].values, df['{}_l'.format(askbidmid)].values, df['{}_c'.format(askbidmid)].values )
    indicator_list.extend(['CDLDOJISTAR'])
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


