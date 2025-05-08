from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import math
import time
from pandas import DataFrame
import pandas as pd
import numpy as np
import warnings
import logging

warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)
logger = logging.getLogger(__name__)
vervose = True

class MartingaleSpot(IStrategy):
    INTERFACE_VERSION: int = 3
    timeframe = "1m"

    # Stoploss:
    stoploss = -9999

    # Trailing stop:
    trailing_stop = False

    # General parameters
    position_adjustment_enable = True
    max_entry_position_adjustment = 4
    ignore_buying_expired_candle_after = 60
    order_types = {
        "entry": "market",
        "exit": "market",
        "emergency_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
        "stoploss_on_exchange_interval": 60,
        "stoploss_on_exchange_limit_ratio": 0.99
    }

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:

        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df['enter_long'] = True

        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:

        return df

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: Optional[float], max_stake: float,
                            leverage: float, entry_tag: Optional[str], side: str,
                            **kwargs) -> float:

        max_open_trades = self.config['max_open_trades']
        total_wallet = self.wallets.get_total_stake_amount()

        return (total_wallet / max_open_trades) / 16

    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                             current_rate: float, current_profit: float, min_stake: float,
                             max_stake: float, **kwargs) -> Optional[float]:

        total_wallet = self.wallets.get_total_stake_amount()
        count_of_entries = trade.nr_of_successful_entries
        condition_1 = current_profit <= -0.025 and count_of_entries == 1
        condition_2 = current_profit <= -0.05 and count_of_entries == 2
        condition_3 = current_profit <= -0.10 and count_of_entries == 3
        condition_4 = current_profit <= -0.20 and count_of_entries == 4

        if condition_1 or condition_2 or condition_3 or condition_4:
            stake_amount = trade.stake_amount
        else:
            return None

        if total_wallet - trade.stake_amount < stake_amount:
            return None

        if vervose:
            time = current_time.replace(tzinfo=None)
            logger.info(f"{time} Initiating DCA entry #{count_of_entries} for {trade.pair} with {round(stake_amount, 2)} {trade.stake_currency}")

        return stake_amount

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs):

        count_of_entries = trade.nr_of_successful_entries

        if count_of_entries == 1 and current_profit >= 0.04:
            return 'roi_4%'
        elif count_of_entries == 2 and current_profit >= 0.02:
            return 'roi_2%'
        elif count_of_entries == 3 and current_profit >= 0.01:
            return 'roi_1%'
        elif count_of_entries >= 4 and current_profit >= 0.005:
            return 'roi_0.5%'

        return None

    def confirm_trade_exit(self, pair: str, trade: Trade, order_type: str, amount: float,
                           rate: float, time_in_force: str, exit_reason: str,
                           current_time: datetime, **kwargs) -> bool:

        if vervose:
            total_wallet = self.wallets.get_total_stake_amount()
            time = current_time.replace(tzinfo=None)
            logger.info(f"{time} Total wallet: {round(total_wallet, 2)} {trade.stake_currency}")
            logger.info(f"{time} Exiting {trade.trade_direction} for {pair} because {exit_reason}")

        return True
