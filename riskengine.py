import numpy as np
import pandas as pd
import datetime as dt
from utils import get_data


def average_trading_range(df, periods=20):
    '''
    find average trading range of asset/security over lookback period
    Based on Perry Kaufman's 'Systems Trading and Methods'

    params
    ======
    df (pd.Dataframe): dataframe object containing OHLC data for asset/security
    periods (int): lookback period from which to calculate ATRs

    return
    ======
    calculated average trading range for asset based on lookback period
    '''
    #general average trading range implementation

    #could be initiated as zeroes array and iteratively changed
    ranges = list()

    #grab all applicable rows
    data = df[-periods:]

    #TODO: really need to look into a vectorized solution, iterrows is sloppy
    for i, dat in data.iterrows():
        #first day in period - use HML
        if i == 0:
            range = df.iloc[i]['High'] - df.iloc[i]['Low']
            ranges.append(range)

        #find all applicable absolute levels, append max to running list
        else:
            day_range = df.iloc[i]['High'] - df.iloc[i]['Low']
            high_close = abs(df.iloc[i]['High'] - df.iloc[i-1]['Close'])
            low_close = abs(df.iloc[i]['Low'] - df.iloc[i-1]['Close'])
            ranges.append(max(day_range, high_close, low_close))

    #thinking of changing this to an int/float and taking val / periods instead
    return np.average(ranges)


class RiskEngine(object):
    '''
    This class creates an asset-class agnostic generalized risk calculation engine

    params
    ======
    notional_amount (float): notional amount of portfolio to allocate into -
                            will change as markets move
    max_notional (float): used to constrain/scale assets within portfolio
    max_exposure (float): max gross exposure to markets allowed
    traded_markets (list): list of tickers for desired assets
    end_date (datetime.date): datetime object representing end date for strategy
                            testing
    lookback (int): lookback period from which to derive allocation/sizing
    '''
    def __init__(self, notional_amount=100_000_000.00,
                max_notional=100_000_000.00, max_exposure=1.0,
                traded_markets=['CL=F','ES=F','CC=F','ZC=F','SB=F','NG=F'],
                end=dt.date.today(), lookback=200):

        self.__notional = notional_amount
        self.__max_size = max_notional / notional_amount
        self.__max_exposure = max_exposure
        self.__traded_markets = traded_markets
        self.__end = end
        self.__start = end - dt.timedelta(lookback)

        #only variable that needs explanation: gets df for each market in list
        self.__data = [get_data(market, self.get_start(),
                       self.get_end()) for market in self.get_markets()]


   #getters
    def get_start(self):
        return self.__start

    def get_end(self):
        return self.__end

    def get_notional(self):
        return self.__notional

    def get_markets(self):
        return self.__traded_markets

    def get_data(self):
        return self.__data

    def get_max_size(self):
        return self.__max_size

    def get_max_exposure(self):
        return self.__max_exposure


    #setters
    def set_notional(self, amount):
        self.__notional = amount

    def set_markets(self, markets):
        self.__markets = markets


    def set_max_size(self, size):
        self.__max_size = size


    def set_max_exposure(self, exposure):
        self.__max_exposure = exposure

    #TODO: need to add some more setters and organize neatly


    def atr_parity(self, lookback_period):
        '''
        calculates position sizes based on asset atr over given time horizon.
        Based on Perry Kaufman's 'Trading Systems and Methods'

        params
        ======
        lookback_period (int): lookback period from which to to calculate atr
        position sizing

        return
        ======
        '''

        #utility function to allocate capital based on ATR parity
        market_data = self.get_data()
        markets = self.get_markets()

        #set up some dictionaries from which to set keep track of data
        allocation_atrs = dict()
        close_price = dict()

        #notional is full portfolio, max size is max tranche size as decimal
        allocation = self.get_notional() * self.get_max_size()

        #initial full exposure set at 0 - used to scale position size
        contract_exposure = 0
        for df, market in zip(market_data, markets):
            #find unconstrained exposure for each market
            atr = average_trading_range(df, lookback_period)
            allocation_to_atr = allocation / atr
            #close price from market
            market_close = df.iloc[-1]['price']

            #for use later...
            allocation_atrs[market] = allocation_to_atr
            close_price[market] = market_close

            #unconstrained $ exposure
            value = market_close * allocation_to_atr

            #value added to full exposure of portfolio for scaling
            contract_exposure += value


        scaler =  allocation / contract_exposure
        shares = dict()
        for market in markets:
            #find scaled exposure to each security
            close = close_price[market]
            scaled = (allocation_atrs[market] * close) * scaler
            num_shares = round(scaled / close,0)
            shares[market] = (num_shares, close)

        return shares


    def vol_targeting(self, target=0.25):
        '''
        Position sizing of assets based on volatility
        Based on Rob Carver's 'Systematic Trading'

        param
        =====
        target (float): annualized volatility target

        return
        ======
        position sizes of each asset
        '''
        annual_cash_vol = target * self.get_notional()


        market_data = self.get_data()
        markets = self.get_markets()

        #set up some dictionaries from which to set keep track of data
        allocation_atrs = dict()
        close_price = dict()

        #notional is full portfolio, max size is max tranche size as decimal
        allocation = self.get_notional() * self.get_max_size()

        #initial full exposure set at 0 - used to scale position size
        contract_exposure = 0
        for df, market in zip(market_data, markets):
            pass


def main():
    engine = RiskEngine()
    shares = engine.atr_parity(lookback_period=20)
    print(shares)

    #portfolio tranche size to allocate positions within
    port_tranche = engine.get_max_size() * engine.get_notional()
    for ticker, (num_shares, closing_price) in shares.items():
        market_value = num_shares*closing_price
        percent_tranche = market_value/port_tranche
        print(f'TICKER: {ticker}, SHARES: {num_shares:,}')
        print(f'MARKET VALUE: ${market_value:,.2f}, PERCENT OF PORTFOLIO TRANCHE: {percent_tranche:.2%}')


if __name__ == '__main__':
    main()
