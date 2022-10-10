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

    #eventually this could be better with using position size. 1 = 100% long,
    #-1 = 100% short. L/S parameters are vague right now, will use a position
    #optimization function apply for time series levels
    df['signal_long'] = np.where(df['{}_dma'.format(st)] > \
                                df['{}_dma'.format(lt)], 1, 0)
    df['signal_short'] = np.where(df['{}_dma'.format(st)] < \
                                df['{}_dma'.format(lt)], -1, 0)

    conditions = [(df['signal_long'] == 1), (df['signal_short'] == -1), \
                    (df['signal_long'] == 0) & (df['signal_short'] == 0)]

    values = [1, -1, 0]
    df['signal'] = np.select(conditions, values)

    return df.dropna()


def macd(df, a=12, b=26, c=9):
    df[f'ewm_{a}'] = df['price'].ewm(span=a).mean()
    df[f'ewm_{b}'] = df['price'].ewm(span=b).mean()
    df['macd_line'] = df[f'ewm_{a}'] - df[f'ewm_{b}']
    return df['macd_line'].ewm(span=c).mean()


def macd_strat(df):
    '''
    macd strategy in which acceleration/deceleration of divergence is captured
    in trades

    params
    ======
    df (pd.Dataframe): time-series price data for individual security

    return
    ======
    pandas dataframe containing all incoming price data as well as signals
    generated from macd implementation
    '''

    df['macd'] = macd(df)

    ###########################################
    # looking for rate of change of macd here #
    ###########################################

    # 1) positive acceleration of macd while above zero macd ==> buy
    # 2) negative acceleration of macd while negative ==> short
    # 3) average negative acceleration of macd for 5 trading days while positive ==> flat
    # 2) average positive acceleration of macd for 5 trading days while negative ==> flat
    #TODO: scaling into and out of positions is important. relative strength of signal?

    df['macd_roll'] = df['macd'].pct_change(periods=5, axis=0)
    #print(df['macd_roll'].dropna())
    df['signal_long'] = np.where(((df['macd_roll'] >= 0) & \
                                (df['macd'] >= 0)), 1, 0)
    print(df['signal_long'])
    df['signal_short'] = np.where((df['macd_roll'] < 0) & (df['macd'] < 0), 1, 0)
    df['signal_flat'] = np.where(((df['macd_roll'] >= 0) & (df['macd'] < 0)) | \
                            ((df['macd_roll'] < 0) & (df['macd'] >= 0)), 1, 0)

    conditions = [(df['signal_long'] == 1), (df['signal_short'] == 1), \
                    (df['signal_flat'] == 1)]
    values = [1, -1, 0]

    df['signal'] = np.select(conditions, values)

    return df.dropna()


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


def generate_awesome_oscillator(df, window):
    '''
    Implementation of awesome oscillator for trend breakout/reversal

    params
    ======
    df (pd.DataFrame): pandas dataframe with pricing data for security
    window (int): lookback window to create

    returns
    =======
    pandas dataframe containing dataframe with oscillator values
    '''
    df['med'] = (df['High'] + df['Low']) / 2
    df[f'awesome_oscillator_{window}_window'] = df['med'].rolling(5).mean() - \
                                                df['med'].rolling(window).mean()
    return df

def awesome_oscillator_strategy(df, windows=[]):
    '''
    interpret and generate signals based on awesome oscillator

    Economic rationale is below:
    1) if awesome oscillator is positive and gradient is positive, buy.
    2) if oscillator negative  and gradient negative, sell.
    3) if oscillator positive but gradient negative, scale out.
    4) if oscillator is negative but gradient is positive, scale in.

    need to think more about 3) and 4). will likely think about this a bit more
    and implement later down the line.

    params
    ======
    df (pd.DataFrame): pandas dataframe with pricing data for security
    window (int): list of lookback windows from which to generate signals

    returns
    =======
    buy/sell signal expressed as a decimal
    '''

    #generate awesome oscillator series' based on windows
    for window in windows:
        df = generate_awesome_oscillator(df, window)

    #find columns independent of the windows used
    oscillator_cols = [col for col in df.columns if 'awesome_oscillator' in col]

    #find if oscillator value is higher or lower than previous
    for col in oscillator_cols:
        df[f'gradient_{col}'] = df[col] - df[col].shift(1)

    #find gradient columns independent of windows used
    gradient_cols = [col for col in df.columns if 'gradient' in col]

    #drop na values for sake of stopping errors


    #find averages over oscillator and gradient average values over earch window
    df['avg_oscillator'] = df[oscillator_cols].apply(lambda x: x.mean(), axis=1)
    df['avg_gradient'] = df[gradient_cols].apply(lambda x: x.mean(), axis=1).rolling(5).mean()

    df.dropna(inplace=True)

    #generate signal based on the economic rationale explained above
    df['signal_long'] = np.where((df['avg_oscillator'] > 0) & \
                                (df['avg_gradient'] > 0), 1, 0)

    df['signal_short'] = np.where((df['avg_oscillator'] < 0) & \
                                (df['avg_gradient'] < 0), -1, 0)


    conditions = [(df['signal_long'] == 1), (df['signal_short'] == -1)]
    values = [1, -1]

    df['signal'] = np.zeros(len(df['signal_long']))
    df['signal'] = np.select(conditions, values)
    return df

def main():

    end_date = dt.date.today()
    start_date = end_date - relativedelta(years=20)
    df = get_data('SPY', start_date, end_date, 'Adj Close')
    df.set_index('Date', inplace=True)

    #TODO: need to find a way to implement these out of current year, may be
    #able to parse years and just pass these as parameters
    rebals = [dt.date(year=dt.date.today().year,month=3,day=31),
            dt.date(year=dt.date.today().year, month=6, day=30),
            dt.date(year=dt.date.today().year, month=9, day=30),
            dt.date(year=dt.date.today().year, month=12, day=31)]

    #macd_df = macd_strat(df)
    #macd_stats = implement_macd(macd_df, macd_strat)
    #print(macd_stats)
    windows = [34, 50, 68]
    awesome_oscillator_strategy(df, windows)


if __name__ == '__main__':
    main()
