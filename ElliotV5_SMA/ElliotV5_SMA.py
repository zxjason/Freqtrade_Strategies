#############################################################################################################
##    ElliotV5_SMA Strategy mod 1 by @zxjason & DS                                                         ##
##    https://github.com/zxjason/Freqtrade_Strategies                                                      ##
##    Strategy for Freqtrade https://github.com/freqtrade/freqtrade                                        ##
#############################################################################################################
##    GENERAL RECOMMENDATIONS                                                                              ##
##    For optimal performance, suggested to use only BTC and ETH.                                          ##
#############################################################################################################
##    DONATIONS                                                                                            ##
##    usdc: 0xedB85Ce16ba8268F32925f6fF48190Cea97a9b81                                                     ##
##    REFERRAL LINKS                                                                                       ##
#############################################################################################################

from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
import talib.abstract as ta
import numpy as np
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.persistence import Trade
from freqtrade.strategy import stoploss_from_open, merge_informative_pair, DecimalParameter, IntParameter

# Updated buy and sell parameters with narrowed ranges
buy_params = {
    "base_nb_candles_buy": 17,
    "ewo_high": 3.34,
    "ewo_low": -17.457,
    "low_offset": 0.978,
    "rsi_buy": 65,
    "atr_mult": 2.0  # Added ATR multiplier for dynamic stoploss
}

sell_params = {
    "base_nb_candles_sell": 49,
    "high_offset": 1.019,
    "rsi_sell": 70  # Added RSI sell threshold
}

def EWO(dataframe, ema_length=50, ema2_length=200):
    df = dataframe.copy()
    ema1 = ta.EMA(df, timeperiod=ema_length)
    ema2 = ta.EMA(df, timeperiod=ema2_length)
    emadif = (ema1 - ema2) / df['close'] * 100
    return emadif

class ElliotV5_SMA_mod1(IStrategy):
    INTERFACE_VERSION = 2

    minimal_roi = {
        "0": 0.215,
        "40": 0.132,
        "87": 0.086,
        "201": 0.03
    }

    stoploss = -0.15  # Adjusted to -15% (will be overridden by dynamic ATR)
    use_custom_stoploss = True  # Enable custom stoploss

    # Narrowed parameter ranges for efficiency
    base_nb_candles_buy = IntParameter(10, 30, default=buy_params['base_nb_candles_buy'], space='buy', optimize=True)
    base_nb_candles_sell = IntParameter(20, 60, default=sell_params['base_nb_candles_sell'], space='sell', optimize=True)
    low_offset = DecimalParameter(0.95, 0.99, default=buy_params['low_offset'], space='buy', optimize=True)
    high_offset = DecimalParameter(1.0, 1.05, default=sell_params['high_offset'], space='sell', optimize=True)

    ewo_low = DecimalParameter(-20.0, -8.0, default=buy_params['ewo_low'], space='buy', optimize=True)
    ewo_high = DecimalParameter(2.0, 12.0, default=buy_params['ewo_high'], space='buy', optimize=True)
    rsi_buy = IntParameter(30, 70, default=buy_params['rsi_buy'], space='buy', optimize=True)
    rsi_sell = IntParameter(65, 90, default=sell_params['rsi_sell'], space='sell', optimize=True)
    atr_mult = DecimalParameter(1.5, 3.0, default=buy_params['atr_mult'], space='buy', optimize=True)

    trailing_stop = True
    trailing_stop_positive = 0.01  # Increased from 0.005
    trailing_stop_positive_offset = 0.05  # Increased from 0.03
    trailing_only_offset_is_reached = True

    timeframe = '5m'
    informative_timeframe = '1h'

    process_only_new_candles = True
    startup_candle_count = 200

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, self.informative_timeframe) for pair in pairs]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Calculate EMAs for buy and sell signals
        for val in self.base_nb_candles_buy.range:
            dataframe[f'ma_buy_{val}'] = ta.EMA(dataframe, timeperiod=val)
        for val in self.base_nb_candles_sell.range:
            dataframe[f'ma_sell_{val}'] = ta.EMA(dataframe, timeperiod=val)

        # Calculate EWO with EMA
        dataframe['EWO'] = EWO(dataframe)

        # Add RSI and ATR for dynamic stoploss
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)

        # Merge informative timeframe (1h) data
        informative = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.informative_timeframe)
        informative['ema_200'] = ta.EMA(informative, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, informative, self.timeframe, self.informative_timeframe, ffill=True)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []

        # Ensure 1h trend is bullish
        bullish_1h = dataframe[f"ema_200_{self.informative_timeframe}"] < dataframe['close']

        # Entry condition 1: EWO high with RSI
        conditions.append(
            (bullish_1h) &
            (dataframe['close'] < (dataframe[f'ma_buy_{self.base_nb_candles_buy.value}'] * self.low_offset.value)) &
            (dataframe['EWO'] > self.ewo_high.value) &
            (dataframe['rsi'] < self.rsi_buy.value) &
            (dataframe['volume'] > 0)
        )

        # Entry condition 2: EWO low
        conditions.append(
            (bullish_1h) &
            (dataframe['close'] < (dataframe[f'ma_buy_{self.base_nb_candles_buy.value}'] * self.low_offset.value)) &
            (dataframe['EWO'] < self.ewo_low.value) &
            (dataframe['volume'] > 0)
        )

        if conditions:
            dataframe.loc[reduce(lambda x, y: x | y, conditions), 'buy'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            (dataframe['close'] > (dataframe[f'ma_sell_{self.base_nb_candles_sell.value}'] * self.high_offset.value)) &
            (dataframe['rsi'] > self.rsi_sell.value) &
            (dataframe['volume'] > 0)
        ]
        dataframe.loc[reduce(lambda x, y: x | y, conditions), 'sell'] = 1
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, ​**kwargs) -> float:
        # Dynamic stoploss using 2*ATR
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1]
        atr_stop = last_candle['atr'] * self.atr_mult.value
        return current_rate - atr_stop
