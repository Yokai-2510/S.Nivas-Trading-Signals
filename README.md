# Automated Trading Signal Engine for NSE

**An advanced, configurable, GUI-based tool to scan the Indian stock market (Nifty 500 & F&O stocks) for high-probability swing and momentum trading opportunities.**

This engine automates the tedious process of daily stock screening by evaluating hundreds of stocks against sophisticated, multi-point technical criteria. It processes historical data, calculates a suite of technical indicators, and generates concise, actionable reports, allowing traders to focus on analysis rather than manual scanning.

---

## 🎯 Core Objective

The primary goal of this project is to create a semi-automated signal engine that streamlines trade discovery. It scans a wide universe of stocks daily, applies a custom 10-point checklist for both Swing and Momentum trading styles, and shortlists candidates that meet a high threshold of technical strength.

---

## ✨ Key Features

*   **Dual Trading Strategies:** Generates separate signals for both **Swing Trading** (capturing pullbacks in an uptrend) and **Momentum Trading** (riding strong breakouts).
*   **Comprehensive Stock Universe:** Scans all stocks within the **Nifty 500** and the **Futures & Options (F&O)** segment for maximum coverage.
*   **Sophisticated 10-Point Rule Engine:** Each stock is evaluated against a detailed, multi-indicator checklist, including EMAs, RSI, Volume, ADX, Candlestick Patterns, and more.
*   **Official Delivery Percentage Analysis:** Integrates data from the official **NSE Bhavcopy** to analyze the delivery percentage of stocks—a key indicator of institutional accumulation.
*   **Intuitive Graphical User Interface (GUI):** A user-friendly interface built with CustomTkinter allows for easy operation: fetching data, running analysis, and exporting results with just a few clicks.
*   **Fully Configurable:** All rules, parameters (EMA periods, RSI levels, etc.), data source URLs, and file paths can be modified directly from the Configuration tab in the app or via the `config.json` file.
*   **Flexible Reporting:** Exports detailed analysis reports to local **Excel files**, either as a single consolidated report with multiple sheets or as individual files for each analysis type.

---

## 🛠️ Modular Architecture

The project is built with a clean, modular design to ensure maintainability and scalability. The core logic is separated from the user interface, allowing for independent development and testing.

```
.
├── engine/
│   ├── fetch_data.py       # Handles downloading tickers, OHLCV, and Bhavcopy data.
│   ├── indicators.py       # Core logic for calculating all technical indicators (EMA, RSI, ADX, CPR, VWAP, etc.).
│   ├── format_dataset.py   # Formats the raw signal data into a wide, human-readable report.
│   └── create_report.py    # Handles the creation of the final Excel reports.
├── source/
│   └── config.json         # Central configuration file for all parameters and settings.
├── app_gui.py              # The main GUI application window and user-facing controls.
├── main.py                 # The backend engine that orchestrates the data fetching, analysis, and reporting threads.
└── requirements.txt        # List of all Python dependencies.
```

---

## 📈 Trading Strategies & Signal Logic

The engine uses two distinct, 10-point rule sets to identify trading candidates.

### ✅ Swing Trading Strategy

This strategy aims to identify stocks that are in a confirmed uptrend and are currently experiencing a minor pullback or consolidation, presenting a low-risk entry point.

| No. | Criteria | Implementation Logic & Purpose |
|:---:|---|---|
| **1** | **Price > 50 EMA** | The closing price must be above the 50-day Exponential Moving Average, confirming a healthy medium-term uptrend. |
| **2** | **Price > 200 EMA** | The closing price must also be above the 200-day EMA, ensuring a strong long-term bullish bias. |
| **3** | **RSI (14) in Range** | The 14-period Relative Strength Index must be between **45 and 60**. This signifies that the stock is neither overbought nor oversold, but rather in a potential accumulation or consolidation zone after a dip. |
| **4** | **Volume Surge** | Today's volume must be at least **1.5 times** the 20-day average volume, indicating a surge in interest and potential for a move higher. |
| **5** | **Bullish Reversal Candle** | A bullish reversal pattern must have formed on the previous day's candle. The engine detects: **Bullish Engulfing**, **Hammer**, or an **Inside Bar with a Bullish Breakout**. |
| **6** | **Narrow Monthly CPR** | The stock must be trading above the **Top CPR** line of a narrow Monthly Central Pivot Range. This "KGS Narrow CPR" logic suggests a high probability of a trending move. |
| **7** | **Narrow Weekly CPR** | Similarly, the stock should be trading above the **Top CPR** of a narrow Weekly Central Pivot Range, confirming bullish strength on a shorter timeframe. |
| **8** | **Volume Profile Support** | The price must be above the 60-day **Volume Weighted Average Price (VWAP)**. This acts as a proxy for the Point of Control, indicating the price is above the recent high-volume consensus area. |
| **9** | **Trend Strength (ADX)**| The 14-period Average Directional Index (ADX) must be **greater than 20**, confirming that a tangible trend is in place (not a sideways market). |
| **10**| **High Delivery %** | The delivery percentage from the most recent **NSE Bhavcopy** file must be **greater than 35%**. This suggests that a high portion of shares were bought for delivery, indicating genuine accumulation, not just intraday trading. |

### ⚡ Momentum Trading Strategy

This strategy aims to identify stocks that are already in a strong uptrend and are breaking out to new highs with significant volume and momentum.

| No. | Criteria | Implementation Logic & Purpose |
|:---:|---|---|
| **1** | **Price > 20 EMA** | The closing price must be above the 20-day EMA, confirming strong short-term momentum. |
| **2** | **Price > 50 EMA** | The price must also be above the 50-day EMA, aligning the short- and medium-term trends. |
| **3** | **Price > 200 EMA** | The price must be decisively above the 200-day EMA, indicating a powerful, structurally sound bull market for the stock. |
| **4** | **Strong RSI (14)** | The 14-period RSI must be **greater than 60** (preferably > 70). This captures stocks that are exhibiting strong bullish momentum and are in "overbought" territory, which is often a characteristic of a trending move. |
| **5** | **High Volume Breakout** | Today's volume must be at least **2.0 times** the 20-day average volume, confirming that the breakout has strong conviction behind it. |
| **6** | **52-Week Breakout** | The stock's closing price must be making a new **52-week high**. This is a simple but powerful indicator of a major breakout from a long-term consolidation. |
| **7** | **Volume Profile Support** | The price must be above the 60-day **Volume Weighted Average Price (VWAP)**, ensuring the breakout is supported by recent volume. |
| **8** | **Narrow Weekly CPR** | The stock must be trading above the **Top CPR** of a narrow Weekly Central Pivot Range, indicating a high probability of a continued trending day or week. |
| **9** | **Bullish EMA Stack** | The EMAs must be perfectly aligned in a bullish stack: **20 EMA > 50 EMA > 200 EMA**. This is a classic visual confirmation of a very strong, multi-timeframe uptrend. |
| **10**| **High Delivery %** | The delivery percentage from the most recent **NSE Bhavcopy** must be **greater than 40%**, indicating strong buying conviction and institutional interest in the breakout. |

---

## 🚀 Getting Started

Follow these steps to set up and run the Signal Engine on your local machine.

### Prerequisites
*   Python 3.8 or newer
*   Git

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-folder>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initial Run & Directory Creation:**
    The first time you run the app, it will look for a `source` directory. Please create it manually in the project root if it doesn't exist.
    ```bash
    mkdir source
    ```
    The `config.json` file should be placed inside this `source` directory.

### How to Run the Application

1.  **Launch the GUI:**
    With your virtual environment activated, run the `app_gui.py` file.
    ```bash
    python app_gui.py
    ```

2.  **Step 1: Fetch Data**
    *   Click the **"FETCH LATEST DATA"** button. This will download the latest ticker lists and historical price data from the configured sources and save them locally to the `source` directory.
    *   You can control which data is fetched from the `Configuration` -> `File & Data` tab.

3.  **Step 2: Run Analysis**
    *   Once data is fetched, the **"RUN ANALYSIS"** button will be enabled.
    *   Select which analyses you want to run (e.g., N500 Swing, FNO Momentum).
    *   Click the button to start the analysis. The engine will process the local data, calculate all indicators (including fetching the latest delivery %), and generate the signal reports in memory.

4.  **Step 3: Export Results**
    *   After the analysis is complete, the **"EXPORT RESULTS"** button will be enabled.
    *   Click it to save the generated reports to Excel files in the designated output folder.

5.  **Configuration**
    *   Navigate to the **Configuration** tab to customize all aspects of the engine, from indicator parameters to file paths and data URLs.
    *   Click **"Save Configuration"** to persist your changes to `source/config.json`.

---

## Disclaimer

This tool is for educational and informational purposes only. The signals generated are based on predefined technical criteria and do not constitute financial advice or a recommendation to buy or sell any security. Always perform your own due diligence and consult with a qualified financial advisor before making any investment decisions. The author is not responsible for any financial losses incurred.
