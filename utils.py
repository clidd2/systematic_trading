import pandas_datareader.data as web
import datetime as dt

def get_data(ticker, start_date, end_date=dt.datetime.today(), colname='Adj Close'):
    try:
        #frame containing price data for given security in given date range
        df = web.DataReader(name=ticker,data_source='yahoo',start=start_date,
                            end=end_date)

        #convert index from string to datetime
        df.index = pd.to_datetime(df.index)

    except Exception as err:
        print(err)

    return df.rename(columns={colname:'price'}).reset_index()
