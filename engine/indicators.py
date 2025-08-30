# --- engine/indicators.py ---

import pandas as pd
import numpy as np


#---------- # INDIVIDUAL INDICATOR CALCULATION FUNCTIONS ---------- 

def _calculate_ema(data, period): # Calculates a single Exponential Moving Average
    return data['Close'].ewm(span=period, adjust=False).mean()

def _calculate_rsi(data, period): # Calculates the Relative Strength Index (FIXED)
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = np.where(avg_loss == 0, 100, 100 - (100 / (1 + rs)))
    return rsi

def _calculate_atr(data, period=14): # Calculates Average True Range
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

def _calculate_adx(data, period=14): # Calculates Average Directional Index (ADX)
    df = data.copy()
    df['+DM'] = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']), df['High'] - df['High'].shift(1), 0)
    df['+DM'] = np.where(df['+DM'] < 0, 0, df['+DM'])
    df['-DM'] = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)), df['Low'].shift(1) - df['Low'], 0)
    df['-DM'] = np.where(df['-DM'] < 0, 0, df['-DM'])
    tr = pd.concat([df['High'] - df['Low'], abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    with np.errstate(divide='ignore', invalid='ignore'):
        plus_di = 100 * (df['+DM'].ewm(span=period, adjust=False).mean() / atr)
        minus_di = 100 * (df['-DM'].ewm(span=period, adjust=False).mean() / atr)
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.ewm(span=period, adjust=False).mean()
    return adx

def _calculate_monthly_cpr(data): # Calculates Monthly Central Pivot Range and narrow-range flag
    data['Date'] = pd.to_datetime(data['Date'])
    last_day_of_data = data['Date'].iloc[-1]
    prev_month_data = data[data['Date'].dt.to_period('M') == (last_day_of_data.to_period('M') - 1)]
    if prev_month_data.empty:
        data['Top_CPR'], data['Bottom_CPR'], data['Is_Narrow_CPR'] = np.nan, np.nan, False
        return data
    prev_high = prev_month_data['High'].max(); prev_low = prev_month_data['Low'].min(); prev_close = prev_month_data['Close'].iloc[-1]
    pivot = (prev_high + prev_low + prev_close) / 3; bc = (prev_high + prev_low) / 2; tc = (pivot - bc) + pivot
    data['Top_CPR'] = max(tc, bc); data['Bottom_CPR'] = min(tc, bc)
    is_narrow = abs(tc - bc) < (prev_close * 0.005)
    data['Is_Narrow_CPR'] = is_narrow
    return data

def _calculate_weekly_cpr(data):
    data['Date'] = pd.to_datetime(data['Date'])
    if len(data) < 7:
        data['Weekly_Top_CPR'], data['Is_Narrow_Weekly_CPR'] = np.nan, False
        return data
    
    data['Year'] = data['Date'].dt.isocalendar().year
    data['Week'] = data['Date'].dt.isocalendar().week
    
    weekly_data = data.groupby(['Year', 'Week']).agg(
        Prev_High=('High', 'max'),
        Prev_Low=('Low', 'min'),
        Prev_Close=('Close', 'last')
    ).shift(1).reset_index()
    
    data = pd.merge(data, weekly_data, on=['Year', 'Week'], how='left')
    
    pivot = (data['Prev_High'] + data['Prev_Low'] + data['Prev_Close']) / 3
    bc = (data['Prev_High'] + data['Prev_Low']) / 2
    tc = (pivot - bc) + pivot
    
    data['Weekly_Top_CPR'] = np.maximum(tc, bc)
    data['Is_Narrow_Weekly_CPR'] = abs(tc - bc) < (data['Prev_Close'] * 0.005)
    
    data.drop(columns=['Year', 'Week', 'Prev_High', 'Prev_Low', 'Prev_Close'], inplace=True)
    return data

def _calculate_vwap(data, period):
    typical_price_vol = (data['Close'] + data['High'] + data['Low']) / 3 * data['Volume']
    volume_sum = data['Volume'].rolling(window=period).sum()
    vwap = typical_price_vol.rolling(window=period).sum() / volume_sum
    return vwap

def _detect_candlestick_patterns(data):
    patterns = pd.Series("None", index=data.index)
    if 'ATR_14' not in data.columns or data['ATR_14'].isnull().all():
        return patterns

    prevRed = data['Open'].shift(2) > data['Close'].shift(2)
    todayGreen = data['Close'].shift(1) > data['Open'].shift(1)
    engulfBody = (data['Open'].shift(1) <= data['Close'].shift(2)) & (data['Close'].shift(1) >= data['Open'].shift(2))
    bodyMinSize = abs(data['Close'].shift(2) - data['Open'].shift(2)) >= 0.2 * data['ATR_14'].shift(1)
    patterns[prevRed & todayGreen & engulfBody & bodyMinSize] = "BULL_ENGULF"

    range_val = data['High'].shift(1) - data['Low'].shift(1)
    body = abs(data['Close'].shift(1) - data['Open'].shift(1))
    upperWick = data['High'].shift(1) - data['Open'].shift(1).combine(data['Close'].shift(1), max)
    lowerWick = data['Open'].shift(1).combine(data['Close'].shift(1), min) - data['Low'].shift(1)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        smallBody = body <= 0.4 * range_val
        longLower = lowerWick >= 2.0 * body
        tinyUpper = upperWick <= 0.25 * body
        closeHighPos = (data['Close'].shift(1) - data['Low'].shift(1)) / range_val >= 0.6
    
    recentDip = data['Low'].shift(1) <= data['Low'].shift(2).rolling(window=2).min()
    patterns[smallBody & longLower & tinyUpper & closeHighPos & recentDip] = "BULL_HAMMER"
    
    insideBar = (data['High'].shift(1) <= data['High'].shift(2)) & (data['Low'].shift(1) >= data['Low'].shift(2))
    breakoutUp = data['Close'] > data['High'].shift(1)
    patterns[insideBar & breakoutUp] = "BULL_INSIDE_BREAK"
    return patterns

def _detect_breakout(data):
    rolling_high = data['Close'].shift(1).rolling(window=252).max()
    return data['Close'] > rolling_high

#---------- # MASTER INDICATOR APPLICATION FUNCTION ---------- 

def add_all_indicators(data, swing_rules, momentum_rules, delivery_perc=0.0):
    if data is None or len(data) < 252: return None
    
    data['EMA_20'] = _calculate_ema(data, momentum_rules['ema_period_1'])
    data['EMA_50'] = _calculate_ema(data, swing_rules['ema_period_1'])
    data['EMA_200'] = _calculate_ema(data, swing_rules['ema_period_2'])
    data['RSI_14'] = _calculate_rsi(data, swing_rules['rsi_period'])
    data[f"Volume_Avg_{swing_rules['volume_avg_period']}"] = data['Volume'].rolling(window=swing_rules['volume_avg_period']).mean()
    data['ATR_14'] = _calculate_atr(data, 14)
    data['ADX_14'] = _calculate_adx(data, swing_rules['adx_period'])

    data = _calculate_monthly_cpr(data)
    data = _calculate_weekly_cpr(data)
    data['VWAP_60'] = _calculate_vwap(data, swing_rules.get('poc_period', 60))
    data['Candle_Pattern'] = _detect_candlestick_patterns(data)
    data['Is_52w_Breakout'] = _detect_breakout(data)
    
    # Add the real delivery percentage value to the dataframe
    data['Delivery_Perc_Value'] = delivery_perc
    
    return data.dropna(subset=['EMA_200', 'RSI_14', 'VWAP_60', 'ADX_14']).reset_index(drop=True)


def evaluate_swing_rules(row, rules):
    avg_vol_col = f"Volume_Avg_{rules['volume_avg_period']}"
    signals = []
    signals.append({'Criteria': '1. Price > EMA_50', 'SignalBool': row['Close'] > row['EMA_50'], 'ThresholdValue': f">{row['EMA_50']:.2f}", 'CurrentValue': f"{row['Close']:.2f}"})
    signals.append({'Criteria': '2. Price > EMA_200', 'SignalBool': row['Close'] > row['EMA_200'], 'ThresholdValue': f">{row['EMA_200']:.2f}", 'CurrentValue': f"{row['Close']:.2f}"})
    signals.append({'Criteria': '3. RSI in Range (45-60)', 'SignalBool': rules['rsi_range_min'] <= row['RSI_14'] <= rules['rsi_range_max'], 'ThresholdValue': f"{rules['rsi_range_min']}-{rules['rsi_range_max']}", 'CurrentValue': f"{row['RSI_14']:.2f}"})
    signals.append({'Criteria': f"4. Volume > {rules['volume_factor']}x Avg", 'SignalBool': row['Volume'] > (row[avg_vol_col] * rules['volume_factor']), 'ThresholdValue': f">{(row[avg_vol_col] * rules['volume_factor']):,.0f}", 'CurrentValue': f"{row['Volume']:,.0f}"})
    signals.append({'Criteria': '5. Bullish Reversal Candle', 'SignalBool': row['Candle_Pattern'] != "None", 'ThresholdValue': 'Engulf/Hammer/Inside', 'CurrentValue': row['Candle_Pattern']})
    signals.append({'Criteria': '6. Price > Top CPR (Narrow Monthly)', 'SignalBool': row['Close'] > row['Top_CPR'] and row['Is_Narrow_CPR'], 'ThresholdValue': f"> {row['Top_CPR']:.2f} & IsNarrow", 'CurrentValue': f"Price={row['Close']:.2f}, Narrow={row['Is_Narrow_CPR']}"})
    signals.append({'Criteria': '7. Price > Top CPR (Narrow Weekly)', 'SignalBool': row['Close'] > row['Weekly_Top_CPR'] and row['Is_Narrow_Weekly_CPR'], 'ThresholdValue': f"> {row['Weekly_Top_CPR']:.2f} & IsNarrow", 'CurrentValue': f"Price={row['Close']:.2f}, Narrow={row['Is_Narrow_Weekly_CPR']}"})
    signals.append({'Criteria': '8. Price > VWAP (Volume Weighted Avg)', 'SignalBool': row['Close'] > row['VWAP_60'], 'ThresholdValue': f"> {row['VWAP_60']:.2f}", 'CurrentValue': f"{row['Close']:.2f}"})
    signals.append({'Criteria': f"9. ADX > {rules['adx_min']}", 'SignalBool': row['ADX_14'] > rules.get('adx_min', 20), 'ThresholdValue': f">{rules.get('adx_min', 20)}", 'CurrentValue': f"{row['ADX_14']:.2f}"})
    
    # INTEGRATION: Use the real delivery data from config
    delivery_threshold = rules.get('delivery_perc_min', 35.0)
    signals.append({
        'Criteria': '10. High Delivery %',
        'SignalBool': row['Delivery_Perc_Value'] > delivery_threshold,
        'ThresholdValue': f'> {delivery_threshold}%',
        'CurrentValue': f"{row['Delivery_Perc_Value']:.2f}%"
    })
    return signals

def evaluate_momentum_rules(row, rules):
    avg_vol_col = f"Volume_Avg_{rules['volume_avg_period']}"
    signals = []
    signals.append({'Criteria': '1. Price > EMA_20', 'SignalBool': row['Close'] > row['EMA_20'], 'ThresholdValue': f">{row['EMA_20']:.2f}", 'CurrentValue': f"{row['Close']:.2f}"})
    signals.append({'Criteria': '2. Price > EMA_50', 'SignalBool': row['Close'] > row['EMA_50'], 'ThresholdValue': f">{row['EMA_50']:.2f}", 'CurrentValue': f"{row['Close']:.2f}"})
    signals.append({'Criteria': '3. Price > EMA_200', 'SignalBool': row['Close'] > row['EMA_200'], 'ThresholdValue': f">{row['EMA_200']:.2f}", 'CurrentValue': f"{row['Close']:.2f}"})
    signals.append({'Criteria': f"4. RSI > {rules['rsi_min']}", 'SignalBool': row['RSI_14'] > rules['rsi_min'], 'ThresholdValue': f">{rules['rsi_min']}", 'CurrentValue': f"{row['RSI_14']:.2f}"})
    signals.append({'Criteria': f"5. Volume > {rules['volume_factor']}x Avg", 'SignalBool': row['Volume'] > (row[avg_vol_col] * rules['volume_factor']), 'ThresholdValue': f">{(row[avg_vol_col] * rules['volume_factor']):,.0f}", 'CurrentValue': f"{row['Volume']:,.0f}"})
    signals.append({'Criteria': '6. Breakout (52-Week High)', 'SignalBool': row['Is_52w_Breakout'], 'ThresholdValue': "New 52w High", 'CurrentValue': f"Is Breakout: {row['Is_52w_Breakout']}"})
    signals.append({'Criteria': '7. Price > VWAP (Volume Weighted Avg)', 'SignalBool': row['Close'] > row['VWAP_60'], 'ThresholdValue': f"> {row['VWAP_60']:.2f}", 'CurrentValue': f"{row['Close']:.2f}"})
    signals.append({'Criteria': '8. Price > Top CPR (Narrow Weekly)', 'SignalBool': row['Close'] > row['Weekly_Top_CPR'] and row['Is_Narrow_Weekly_CPR'], 'ThresholdValue': f"> {row['Weekly_Top_CPR']:.2f} & IsNarrow", 'CurrentValue': f"Price={row['Close']:.2f}, Narrow={row['Is_Narrow_Weekly_CPR']}"})
    signals.append({'Criteria': '9. EMA Stack (20>50>200)', 'SignalBool': row['EMA_20'] > row['EMA_50'] > row['EMA_200'], 'ThresholdValue': 'EMAs Aligned', 'CurrentValue': 'Stacked'})
    
    # INTEGRATION: Use the real delivery data from config
    delivery_threshold = rules.get('delivery_perc_min', 40.0)
    signals.append({
        'Criteria': '10. High Delivery %',
        'SignalBool': row['Delivery_Perc_Value'] > delivery_threshold,
        'ThresholdValue': f'> {delivery_threshold}%',
        'CurrentValue': f"{row['Delivery_Perc_Value']:.2f}%"
    })
    return signals