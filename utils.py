import pandas_datareader.data as web
import datetime as dt
import pandas as pd
import numpy as np

def get_data(ticker, start_date, end_date=dt.datetime.today(),
            colname='Adj Close'):
    '''

    '''
    
    try:
        #frame containing price data for given security in given date range
        df = web.DataReader(name=ticker,data_source='yahoo',start=start_date,
                            end=end_date)

        #convert index from string to datetime
        df.index = pd.to_datetime(df.index)

    except Exception as err:
        print(err)

    return df.rename(columns={colname:'price'}).reset_index()

def ewma_vectorized(ser, window):

    alpha = 2 / (window + 1.0)
    alpha_rev = 1 - alpha

    scale = 1 / alpha_rev
    n = len(ser)

    r = np.arange(n)
    scale_arr = scale ** r
    offset = ser[0] * alpha_rev ** (r + 1)
    pw0 = alpha * alpha_rev ** (n - 1)
    print(pw0)

    mult = ser * pw0 * scale_arr
    cumsums = mult.cumsum()
    return  offset + cumsums * scale_arr[::-1]
