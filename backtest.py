#the og imports
import pandas as pd
import numpy as np

#date handling
import datetime as dt
from dateutil.relativedelta import relativedelta

#plotting packages
import seaborn as sns
import matplotlib.pyplot as plt

#xustom imports
from utils import get_data, ZScorer


def dollar_value(df, initial_amount=100):
    return (df['signal'].shift(1) * df['daily_returns']).cumsum().apply(np.exp)

def plot_macd(df):
    buy_and_hold = df['price'].apply(np.log).diff(1).cumsum().apply(np.exp)

    fig, ax = plt.subplots(3,1)
    df['cumulative_value'].plot(ax=ax[0], title='Strategy Returns')
    buy_and_hold.plot(ax=ax[1], title='Buy and Hold')
    df['signal'].plot(ax=ax[2], title='Long/Short')
    plt.show()


def plot_awesome(df):
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

def implement_awesome_oscillator(df, func, windows):

    strategy = func(df, windows)

    # strategy['daily_returns'] = strategy['Close/Last'].pct_change()
    strategy['daily_returns'] = strategy['price'].apply(np.log).diff(1)
    dollar_total = dollar_value(strategy)
    full_frame = pd.concat([strategy, dollar_total.rename('cumulative_value')], \
                                                        axis=1)
    plot_awesome(full_frame)
    return full_frame

def implement_macd(df, func):

    strategy = func(df=df)

    # strategy['daily_returns'] = strategy['Close/Last'].pct_change()
    strategy['daily_returns'] = strategy['price'].apply(np.log).diff(1)
    dollar_total = dollar_value(strategy)
    full_frame = pd.concat([strategy, dollar_total.rename('cumulative_value')], \
                                                        axis=1)
    plot_macd(full_frame)
    return full_frame

def implement_breakout(df, func, params=[]):
    short_window = 10
    long_window = 30
    strategy = func(df=df, st=short_window, lt=long_window)

    # strategy['daily_returns'] = strategy['Close/Last'].pct_change()
    strategy['daily_returns'] = strategy['price'].apply(np.log).diff(1)
    dollar_total = dollar_value(strategy)
    full_frame = pd.concat([strategy, dollar_total.rename('cumulative_value')], \
                            axis=1)
    plot_breakout(full_frame, st=short_window, lt=long_window)
    return full_frame



def scoring_split(data: dict, splits=10, ranking_scores=[],
                ranking_func=None) -> dict:
    '''
    generic scoring function to pass data and return scoring

    params
    ======
    data (dict): dictionary of data of form {identifier : datapoint}
    splits (int): number of buckets by which data is ranked
    ranking_scores (list): attribution score for each split
    ranking_func (func): function that compares two values for scoring

    returns
    =======
    dictionary containing each input identifier along with their bucket
    attribution score


    reqs
    ====
    as of now len(ranking_scores) MUST equal splits in order to allocate
    scoring attributions for each scenario

    '''
    ret = dict()

    if len(ranking_scores) != splits:
        #unfort going against pep with the longer msg
        msg = f'Number of ranking splits {splits} does not equal number of scoring metrics {len(ranking_scores)}'
        raise ValueError(msg)

    pct_splits = [1 / split for split in range(1, splits + 1)]


    for identifier, datapoint in data.items():
        #TODO: rank each datapoint in data dictionary based on input score
        
        #can i use itemgetter here? maybe a list comp works
        pass


    return ret

def aggregate_scoring(funcs=[], datas=[], param_list=[]) -> dict:
    '''
    a consolidated scoring function to be run over aggregate pricing/fundamental
    dataset to determine point-in-time scoring of securities

    params
    ======
    funcs (list): list of scoring functions to apply
    datas (list): list of dataframes over which scoring will be applied
    param_list (list): list of parameters to apply to each function

    returns
    =======
    dictionary containing each identifier's aggregate raw score

    reqs
    ====
    length of funcs, datas, and params must all be the same
    '''
    len_f = len(funcs)
    len_d = len(datas)
    len_p = len(param_list)
    agg = dict()


    if (len_f != len_d) or (len_d != len_p):
        #TODO: could be a bit better in exception catching here

        print(f'Function list length: {len_f}')
        print(f'Data list length: {len_d}')
        print(f'Parameter list length: {len_p}')

        raise ValueError('One of these is not like the other...')

    #zip these bad boys together so that they can be iterated over
    for data, params, func in zip(datas, param_list, funcs):
        #not as generalizable as i would have liked but params make it easy

        #scores data based on each input function and spits out score dict
        scores = scoring_split(data, params['splits'],
                              params['ranking_scores'], func)

        #map each id's score from input into aggregated scoring tally
        for id, score in scores.items():

            #checks if id already exists in aggregation function
            if agg[id]:
                agg[id] += score

            #cant add int to None datatype  :)
            else:
                agg[id] = score

    return agg



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

    implement_awesome_oscillator(df, awesome_oscillator_strategy, windows)



if __name__ == '__main__':
    main()
