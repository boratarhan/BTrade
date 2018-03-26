import datetime
import pandas as pd
import tstables  
import tables 

class desc(tables.IsDescription):
    ''' Description of TsTables table structure.
    '''
    timestamp = tables.Int64Col(pos=0)  
    ask = tables.Float64Col(pos=1)  
    bid = tables.Float64Col(pos=2)
    ask_volume = tables.Int64Col(pos=3)
    bid_volume = tables.Int64Col(pos=4)

def read_hdf_file(filename):
    df_temp = pd.DataFrame()
    filepath = os.path.join('..', '..', 'datastore', filename)
    if os.path.exists( filepath ):
        df_temp = pd.read_hdf(filepath)
    return df_temp


def create_train_test_data(symbol, account_type, read_start_dt, read_end_dt, split_ratio):

    # Reading ts file
    file_path_h5 = '..\\..\\datastore\\_{}\\{}\\S5.h5'.format(account_type, symbol)
    f = tables.open_file(file_path_h5,'r')
    ts = f.root.data._f_get_timeseries()
    read_start_dt = datetime.datetime(2017,1,1,00,00)
    read_end_dt = datetime.datetime.now()
    rows = ts.read_range(read_start_dt,read_end_dt)
    
    train_size = int(len(rows.values) * split_ratio)
    rows_train, rows_test = rows[0:train_size], rows[train_size:len(rows)]
    print('Observations: %d' % (len(rows)))
    print('Training Observations: %d' % (len(rows_train)))
    print('Testing Observations: %d' % (len(rows_test)))
    
    f.close()
    
    return rows_train, rows_test

symbol = 'EUR_USD'
account_type = 'practice'
read_start_dt = datetime.datetime(2017,1,1,00,00)
read_end_dt = datetime.datetime.now()
split_ratio = 0.66

rows_train, rows_test = create_train_test_data(symbol, account_type, read_start_dt, read_end_dt, split_ratio)
