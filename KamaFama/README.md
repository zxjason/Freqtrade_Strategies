### KamaFama策略说明

目前关于该策略的公开信息较少，但如果您也发现E0V1E策略的实际表现未达预期，建议关注我的最新策略**KamaFama**。虽然其胜率（约66%）并非极高，但在全年运行250组交易对时仍能保持稳定的整体盈利比率。

我将逐步发布模拟测试结果以供参考。

* * *

### KamaFama_2 改进版

在原始策略基础上，我移除了部分卖出条件，并新增了**快速盈利卖出（fastk profit sell）​**机制。这一调整将胜率显著提升至**96-98%​**。

初步测试表明，KamaFama_2的表现优于E0V1E：

- ​**入场更平滑**​：相较于E0V1E常在价格剧烈波动后入场，KamaFama_2的入场点通常位于更平缓的价格区间，即使入场后价格短暂下跌（如-2%），也能快速回升至盈利区间。
    
- ​**胜率验证**​：回测显示的95-98%胜率在实盘模拟中得以保持，通过**累积小额盈利**实现日终收益稳定增长。
    

* * *

### 2025年实盘交易数据

#### ​**2025年2月**​（截至2月6日）

| 日期  | 交易次数 | 收益（USDT） | 收益率 |
| :---: | :---: | :---: | :---: |
| 2025-02-06 | 1   | 3,619 | +1.24% |
| 2025-02-05 | 3   | 6,296 | +2.20% |
| 2025-02-04 | 2   | -20,53 | -6.70% |
| 2025-02-03 | 2   | 12,465 | +4.23% |
| 2025-02-02 | 6   | -50,74 | -14.69% |
| 2025-02-01 | 5   | -28,72 | -7.67% |

#### ​**2025年1月**​（部分关键日）

| 日期  | 交易次数 | 收益（USDT） | 收益率 |
| :---: | :---: | :---: | :---: |
| 2025-01-31 | 3   | 22,56 | +6.61% |
| 2025-01-29 | 4   | 25,98 | +7.61% |
| 2025-01-19 | 5   | -11,09 | -6.35% |
| 2025-01-01 | 92  | 105,2 | +31.32% |


* * *

### 策略技术背景

- ​**KAMA指标**​：策略核心采用**适应性移动平均线（Kaufman's Adaptive Moving Average）​**，通过动态调整平滑系数适应市场波动，减少滞后性。
    
- ​**风险控制**​：结合ATR（平均真实波幅）设定动态止损/止盈，避免高波动期过度交易。
    

* * *

#### 关键术语说明

- ​**E0V1E**​：一种依赖价格摆动高点（swing high）入场的策略，但易受市场剧烈波动影响。
- ​**Dry-run测试**​：模拟交易环境中的策略验证，避免实盘资金风险。
