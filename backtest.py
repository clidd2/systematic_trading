import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
from utils import get_data
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def breakout(df, st=50, lt=200):
    df['{}_dma'.format(st)] = df[r'price'].rolling(st).mean()
    df['{}_dma'.format(lt)] = df[r'price'].rolling(lt).mean()

    #eventually this could be better with using position size. 1 = 100% long, -1 = 100% short.
    #L/S parameters are vague right now, will use a position optimization function apply for time series levels
    df['signal_long'] = np.where(df['{}_dma'.format(st)] > df['{}_dma'.format(lt)], 1, 0)
    df['signal_short'] = np.where(df['{}_dma'.format(st)] < df['{}_dma'.format(lt)], -1, 0)
    conditions = [(df['signal_long'] == 1), (df['signal_short'] == -1), (df['signal_long'] == 0) & (df['signal_short'] == 0)]
    values = [1, -1, 0]
    df['signal'] = np.select(conditions, values)

    return df.dropna()


def macd(df, a=12, b=26, c=9):
    df[f'ewm_{a}'] = df['price'].ewm(span=a).mean()
    df[f'ewm_{b}'] = df['price'].ewm(span=b).mean()
    df['macd_line'] = df[f'ewm_{a}'] - df[f'ewm_{b}']
    print(df['macd_line'])
    return df['macd_line'].ewm(span=c).mean()


def macd_strat(df):
    print(df.columns)
    df['macd'] = macd(df)
    df['signal'] = np.where(df['macd'] > 0, 1, -1)

    return df.dropna()


def dollar_value(df, initial_amount=100):
    return (df['signal'].shift(1) * df['daily_returns']).cumsum().apply(np.exp)

def plot_macd(df):
    buy_and_hold = df['price'].apply(np.log).diff(1).cumsum().apply(np.exp)

    fig, ax = plt.subplots(3,1)
    df['cumulative_value'].plot(ax=ax[0], title='Strategy Returns')
    buy_and_hold.plot(ax=ax[1], title='Buy and Hold')
    df['signal'].plot(ax=ax[2], title='Long/Short')
    plt.show()


def plot_breakout(df, st, lt):
    magnitude = df['{}_dma'.format(st)] - df['{}_dma'.format(lt)]
    buy_and_hold = df['price'].apply(np.log).diff(1).cumsum().apply(np.exp)

    fig, ax = plt.subplots(4,1)
    df['cumulative_value'].plot(ax=ax[0], title='Strategy Returns')
    buy_and_hold.plot(ax=ax[1], title='Buy and Hold')
    magnitude.plot(ax=ax[2], title='Breakout Magnitude')
    df['signal'].plot(ax=ax[3], title='Long/Short')
    plt.show()

def implement_macd(df, func):

    strategy = func(df=df)

    # strategy['daily_returns'] = strategy['Close/Last'].pct_change()
    strategy['daily_returns'] = strategy['price'].apply(np.log).diff(1)
    dollar_total = dollar_value(strategy)
    full_frame = pd.concat([strategy, dollar_total.rename('cumulative_value')], axis=1)
    plot_macd(full_frame)
    return full_frame

def implement_breakout(df, func, params=[]):
    short_window = 10
    long_window = 30
    strategy = func(df=df, st=short_window, lt=long_window)

    # strategy['daily_returns'] = strategy['Close/Last'].pct_change()
    strategy['daily_returns'] = strategy['price'].apply(np.log).diff(1)
    dollar_total = dollar_value(strategy)
    full_frame = pd.concat([strategy, dollar_total.rename('cumulative_value')], axis=1)
    plot_breakout(full_frame, st=short_window, lt=long_window)
    return full_frame


def main():

    end_date = dt.date.today()
    start_date = end_date - relativedelta(years=20)
    df = get_data('SPY', start_date, end_date, 'Adj Close')
    df.set_index('Date', inplace=True)

    #TODO: need to find a way to implement these out of current year, may be able to parse years and just pass these as parameters
    rebals = [dt.date(year=dt.date.today().year,month=3,day=31),dt.date(year=dt.date.today().year, month=6, day=30),
              dt.date(year=dt.date.today().year, month=9, day=30), dt.date(year=dt.date.today().year, month=12, day=31)]

    macd_df = macd_strat(df)
    macd_stats = implement_macd(macd_df, macd_strat)
    print(macd_stats)


if __name__ == '__main__':
    main()
