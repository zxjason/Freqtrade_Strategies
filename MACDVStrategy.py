#############################################################################################################
##                MACD-V Strategy by ZxJaSoN                                                               ##
##           https://github.com/zxjason/Freqtrade_Strategies                                               ##
##                                                                                                         ##
##    Strategy for Freqtrade https://github.com/freqtrade/freqtrade                                        ##
##                                                                                                         ##
#############################################################################################################
##               GENERAL RECOMMENDATIONS                                                                   ##
##                                                                                                         ##
##   For optimal performance, suggested to use only BTC and ETH.                                           ##
#############################################################################################################
##               HOLD SUPPORT                                                                              ##
#############################################################################################################
##               DONATIONS                                                                                 ##
##                                                                                                         ##
##                                                                                                         ##
##               REFERRAL LINKS                                                                            ##
##                                                                                                         ##
#############################################################################################################

from freqtrade.strategy import IStrategy, merge_informative_pair
from freqtrade.strategy import DecimalParameter, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import numpy as np

class MACDVStrategy(IStrategy):
    
    # 策略参数
    stoploss = -0.99  # 禁用止损
    timeframe = '1d'

    # 参数设置
    ema_period = IntParameter(200, 200, default=200, space='buy')
    exit_profit_pct = DecimalParameter(0.0285, 0.0285, default=0.0285, space='sell')
    macdv_threshold = IntParameter(70, 70, default=70, space='buy')

    # 时间相关退出参数
    exit_after_days_profit = IntParameter(15, 15, default=15, space='sell')
    exit_after_days = IntParameter(77, 77, default=77, space='sell')

    # 策略配置
    startup_candle_count = 300  # 确保足够计算EMA200
    process_only_new_candles = True
    use_exit_signal = True
    ignore_roi_if_entry_signal = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 计算EMA200
        dataframe['ema200'] = ta.EMA(dataframe, timeperiod=self.ema_period.value)

        # 计算MACD-V指标
        fast_len = 12
        slow_len = 26
        atr_len = 26
        signal_len = 9

        # 计算EMA快慢线
        ema_fast = ta.EMA(dataframe, timeperiod=fast_len)
        ema_slow = ta.EMA(dataframe, timeperiod=slow_len)
        
        # 计算ATR
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=atr_len)
        
        # 计算MACD-V
        dataframe['macd'] = ((ema_fast - ema_slow) / dataframe['atr']) * 100
        dataframe['signal'] = ta.EMA(dataframe['macd'], timeperiod=signal_len)
        dataframe['hist'] = dataframe['macd'] - dataframe['signal']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 多头入场条件
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['ema200']) &  # 价格在EMA200上方
                (dataframe['macd'] > self.macdv_threshold.value) &  # MACD-V超过70
                (dataframe['volume'] > 0)  # 确保有成交量
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 初始化所有退出信号为0
        dataframe['exit_signal'] = 0

        # 条件1：达到目标利润2.85%
        dataframe.loc[
            (dataframe['close'] >= dataframe['open'] * (1 + self.exit_profit_pct.value)),
            'exit_signal'
        ] = 1

        # 条件2：MACD-V下穿信号线
        dataframe.loc[
            (dataframe['macd'] < dataframe['signal']) &
            (dataframe['macd'].shift(1) >= dataframe['signal'].shift(1)),
            'exit_signal'
        ] = 1

        # 合并退出条件
        dataframe.loc[
            (dataframe['exit_signal'] == 1),
            'exit_long'
        ] = 1

        return dataframe

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        # 基于时间的退出条件
        if (current_time - trade.open_date_utc).days >= self.exit_after_days.value:
            return 'time_exit_77_days'
        
        if current_profit > 0 and (current_time - trade.open_date_utc).days >= self.exit_after_days_profit.value:
            return 'time_exit_15_days_profit'

        return None

    # 风险管理设置
    @property
    def protections(self):
        return [
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": 3
            }
        ]
