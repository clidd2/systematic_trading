import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import pandas_datareader.data as web


def get_data(ticker, start_date, end_date=dt.datetime.today(), colname='Adj Close'):
    try:
        df = web.DataReader(name=ticker,data_source='yahoo',start=start_date,
                            end=end_date)
        df.set_index('Date', inplace=True)
        df.index = pd.to_datetime(df.index)

    except Exception as err:
        print(err)

    return df.rename(columns={colname:'price'}).reset_index()


def returnize(df, colname = 'price'):
    df['return'] = np.log(df[colname] / df[colname].shift(1))
    return df.dropna()


def strategy_return(df, initial_investment=100000):
    df['strategy'] = df['position'].shift(1) * df['return']
    df.dropna(inplace=True)
    df['strategy_nominal'] = df['strategy'].cumsum().apply(np.exp) * initial_investment
    return df


def strategy(df, fma, sma):
    df[fma] = df['price'].rolling(fma).mean()
    df[sma] = df['price'].rolling(sma).mean()
    df['dist'] = df[fma] - df[sma]
    df['position'] = np.where((df[fma] > df[sma]) & (df['dist'] > df['dist'].rolling(sma).mean()), 1, -1)
    return df

def main():
    #crude futures
    ticker = 'CL=F'
    end = dt.date.today()
    start = end - dt.timedelta(5000) #lookback period - could be changed for more robust data
    df = returnize(get_data(ticker, start, end))

    fma = 5
    sma = 30
    df = strategy_return(strategy(df, fma, sma))

    sns.set()
    df[['return','strategy']].cumsum().apply(np.exp).plot()
    plt.show()
    print(df)





if __name__ == '__main__':
    main()
