**✅ Swing Trading Strategy – 10-Point Rule Explanation**

| **No.** | **Criteria** | **Timeframe** | **Explanation for Developer** |
| --- | --- | --- | --- |
| 1   | Price > EMA50 | Daily | Use 50-period EMA on daily chart. If current close > EMA50, mark ✅. |
| 2   | Price > EMA200 | Daily | Use 200-period EMA on daily chart. Helps confirm medium-term bullish bias. |
| 3   | RSI(14) between 45–60 | Daily | RSI using 14 periods. Accept if between 45 and 60, showing accumulation zone. |
| 4   | Volume > 1.5× avg (20-day) | Daily | Compare today’s volume with 20-day average. Accept if ≥ 1.5×. |
| 5   | Bullish reversal candle | Daily | Look for bullish engulfing, hammer, or inside bar. Candlestick detection logic required. |
| 6   | Price near or above Top CPR of Narrow Monthly CPR | Daily (Monthly CPR logic) | Implement **CPR narrow-range detection** (KGS logic) for Monthly CPR. Check if price is at or above **Top CPR** level. |
| 7   | Price near or above Top CPR of Narrow Weekly CPR | Hourly (Weekly CPR) | Use hourly candles. Use **Weekly CPR**, narrow detection, and check if price is near or above **Top CPR** level. |
| 8   | Volume Profile: price emerging from HVN or rejecting LVN | Daily or Hourly | Use volume-by-price zones. Match if price is breaking out from HVN zone or rejecting LVN. |
| 9   | ADX (Measures trend strength (not direction) )|     | ADX(14) > 20 → trade when trend starts forming |
| 10  | Delivery % | Daily | Stocks which having the highest delivery % in last 15 days comes here, (Daily) |

**⚡ Momentum Trading Strategy – 10-Point Rule Explanation**

| **No.** | **Criteria** | **Timeframe** | **Explanation for Developer** |
| --- | --- | --- | --- |
| 1   | Price > EMA20 | Daily | Use 20-period EMA. If price is above, it's momentum-ready. |
| 2   | Price > EMA50 | Daily | Confirm short- to medium-term alignment. |
| 3   | Price > EMA200 | Daily | Confirm strong bullish structure. |
| 4   | RSI(14) > 60 or 70 | Daily | RSI > 60 (preferably > 70). Use this to capture strong momentum. |
| 5   | Volume > 2× avg (20-day) | Daily | Compare today's volume to 20-day average. |
| 6   | Breakout from consolidation or ATH | Daily | Detect breakout candle after tight range or ATH breakout. (Simple logic: price > previous high for X days.) |
| 7   | Volume Profile: price emerging from HVN or rejecting LVN | Daily or Hourly | Same as swing — price must be rejecting high volume node (HVN) or breaking from low volume node (LVN). |
| 8   | Price near or above Top CPR of Narrow Weekly CPR | Hourly (Weekly CPR) | Use hourly candles + narrow CPR check (KGS logic). Price near or above **Top CPR**. |
| 9   | EMA Stack Confirmation | Daily | EMA20 > EMA50 > EMA200 → strong uptrend (clear momentum conformation) |
| 10  | Delivery % | Daily | Stocks which having the highest delivery % in last 15 days comes here, (Daily) |

**📦 Developer Notes:**

- CPR and **narrow range CPR logic** must follow KGS rules:
- **Volume profile zones** can be simplified:
