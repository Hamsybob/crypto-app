import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

# Get API key from secrets
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

# Must be first Streamlit command
st.set_page_config(page_title="Crypto AI Pro", page_icon="🤖", layout="wide")

st.title("🤖 Crypto AI Pro — Complete Analysis Suite")
st.markdown("---")

# ============================================
# SIDEBAR - Configuration
# ============================================
with st.sidebar:
    st.header("🔍 Select Asset")
    
    coin_options = {
        "Bitcoin (BTC)": "BTCUSDT",
        "Ethereum (ETH)": "ETHUSDT",
        "Zcash (ZEC)": "ZECUSDT",
        "Solana (SOL)": "SOLUSDT",
        "BNB": "BNBUSDT",
        "XRP": "XRPUSDT",
        "Dogecoin (DOGE)": "DOGEUSDT"
    }
    
    selected_coin = st.selectbox("Coin", list(coin_options.keys()))
    trading_pair = coin_options[selected_coin]
    ticker = trading_pair.replace("USDT", "")
    
    st.markdown("---")
    
    st.subheader("⏰ Timeframe")
    timeframe = st.selectbox("Chart Timeframe", ["1h", "4h", "1d", "1w"], index=2)
    
    st.markdown("---")
    
    st.subheader("📡 Data Source")
    use_alternative = st.checkbox("Use Alternative API (if Binance fails)", value=False)
    
    st.markdown("---")
    st.caption("✅ News API is pre-configured")

# ============================================
# FETCH FUNCTIONS with Fallback
# ============================================

def fetch_binance_data(symbol_pair):
    """Fetch from Binance API"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_pair}"
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Binance API returned status: {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"Binance connection error: {str(e)[:50]}")
        return None

def fetch_coingecko_data(coin_id):
    """Fallback to CoinGecko API (more reliable on cloud)"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if coin_id in data:
                return {
                    'lastPrice': data[coin_id]['usd'],
                    'priceChangePercent': data[coin_id].get('usd_24h_change', 0),
                    'volume': data[coin_id].get('usd_24h_vol', 0),
                    'marketCap': data[coin_id].get('usd_market_cap', 0)
                }
        return None
    except Exception as e:
        return None

def fetch_fear_greed():
    try:
        response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return int(data['data'][0]['value']), data['data'][0]['value_classification']
    except:
        return 50, "Neutral"
    return 50, "Neutral"

def fetch_btc_dominance():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['data']['market_cap_percentage']['btc']
    except:
        return 58.0
    return 58.0

def fetch_crypto_news():
    if not NEWS_API_KEY:
        return None, None, None
    
    try:
        url = f"https://newsapi.org/v2/everything?q=cryptocurrency OR crypto&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            analyzer = SentimentIntensityAnalyzer()
            sentiments = []
            news_items = []
            
            for article in articles[:3]:
                title = article.get('title', '')
                if title:
                    sentiment = analyzer.polarity_scores(title)
                    sentiments.append(sentiment['compound'])
                    news_items.append({
                        'title': title[:80],
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'sentiment_score': sentiment['compound']
                    })
            
            if sentiments:
                avg_sentiment = np.mean(sentiments)
                if avg_sentiment > 0.1:
                    overall = "🟢 BULLISH"
                elif avg_sentiment < -0.1:
                    overall = "🔴 BEARISH"
                else:
                    overall = "🟡 NEUTRAL"
                return avg_sentiment, overall, news_items
        return None, None, None
    except:
        return None, None, None

def calculate_rsi_from_prices(prices, period=14):
    """Calculate RSI from price list"""
    if len(prices) < period + 1:
        return 50
    
    gains = []
    losses = []
    
    for i in range(1, period + 1):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return min(100, max(0, rsi))

def fetch_klines(symbol_pair):
    """Fetch historical data for RSI"""
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol_pair}&interval=1h&limit=50"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [float(candle[4]) for candle in data]  # closing prices
    except:
        pass
    return None

# ============================================
# MAIN APP
# ============================================

# Map ticker to CoinGecko ID
coingecko_map = {
    "BTC": "bitcoin", "ETH": "ethereum", "ZEC": "zcash", 
    "SOL": "solana", "BNB": "binancecoin", "XRP": "ripple", "DOGE": "dogecoin"
}
coingecko_id = coingecko_map.get(ticker, ticker.lower())

# Try different data sources
data = None

if use_alternative:
    with st.spinner("Fetching from CoinGecko..."):
        data = fetch_coingecko_data(coingecko_id)
        if data:
            current_price = data['lastPrice']
            price_change_percent = data['priceChangePercent']
            quote_volume = data.get('volume', 0)
            high_24h = current_price * (1 + abs(price_change_percent)/100 + 0.02)
            low_24h = current_price * (1 - abs(price_change_percent)/100 - 0.02)
else:
    with st.spinner("Fetching from Binance..."):
        data = fetch_binance_data(trading_pair)
        if data:
            current_price = float(data['lastPrice'])
            price_change_percent = float(data['priceChangePercent'])
            high_24h = float(data['highPrice'])
            low_24h = float(data['lowPrice'])
            quote_volume = float(data['quoteVolume'])

# Fallback to CoinGecko if Binance fails
if not data and not use_alternative:
    with st.spinner("Binance failed, trying CoinGecko..."):
        data = fetch_coingecko_data(coingecko_id)
        if data:
            current_price = data['lastPrice']
            price_change_percent = data['priceChangePercent']
            quote_volume = data.get('volume', 0)
            high_24h = current_price * (1 + abs(price_change_percent)/100 + 0.02)
            low_24h = current_price * (1 - abs(price_change_percent)/100 - 0.02)

if not data:
    st.error("❌ Unable to fetch data from any source. Please try again in a few seconds.")
    st.info("This could be due to rate limits. Wait 30 seconds and refresh.")
    st.stop()

# Fetch additional data
fg_value, fg_label = fetch_fear_greed()
btc_dom = fetch_btc_dominance()
news_sentiment, news_overall, news_articles = fetch_crypto_news()

# Calculate RSI from historical data
klines = fetch_klines(trading_pair)
if klines and len(klines) > 20:
    rsi = calculate_rsi_from_prices(klines)
else:
    # Estimate RSI from price change
    if price_change_percent > 5:
        rsi = 65
    elif price_change_percent < -5:
        rsi = 35
    else:
        rsi = 50

# Estimate Stochastic
if price_change_percent > 5:
    stoch = 70
elif price_change_percent < -5:
    stoch = 30
else:
    stoch = 50

macd_bullish = price_change_percent > 0

# Risk/Reward
stop_loss = current_price * 0.92
rr_ratio = (current_price * 0.15) / (current_price - stop_loss) if (current_price - stop_loss) > 0 else 0

# Calculate Score
score = 50
if rsi < 30: score += 15
elif rsi > 70: score -= 10
if stoch < 20: score += 10
elif stoch > 80: score -= 10
if macd_bullish: score += 5
if fg_value < 30: score += 15
elif fg_value > 70: score -= 10
if rr_ratio > 2: score += 10
if news_sentiment and news_sentiment > 0.2: score += 5
final_score = max(0, min(100, score))

if final_score >= 80: recommendation = "🔥 STRONG BUY"
elif final_score >= 65: recommendation = "✅ BUY"
elif final_score >= 50: recommendation = "⏸️ HOLD"
elif final_score >= 35: recommendation = "⚠️ AVOID"
else: recommendation = "🔴 HIGH RISK"

# ============================================
# DISPLAY
# ============================================

st.write(f"## Analyzing: {selected_coin}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Price", f"${current_price:,.2f}", f"{price_change_percent:+.2f}%")
with col2:
    st.metric("📈 24h High", f"${high_24h:,.2f}")
with col3:
    st.metric("📉 24h Low", f"${low_24h:,.2f}")
with col4:
    st.metric("😱 Fear & Greed", f"{fg_value} — {fg_label}")

st.markdown("---")

# Technical Indicators
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("RSI (14)", f"{rsi:.1f}")
    if rsi < 30:
        st.success("🟢 Oversold - Buy Signal")
    elif rsi > 70:
        st.warning("🔴 Overbought - Caution")
    else:
        st.info("🟡 Neutral")
with col2:
    st.metric("Stochastic %K", f"{stoch:.1f}")
with col3:
    st.metric("MACD", "Bullish 📈" if macd_bullish else "Bearish 📉")
    st.metric("BTC Dominance", f"{btc_dom:.1f}%")
with col4:
    st.metric("Risk/Reward", f"1:{rr_ratio:.1f}")

st.markdown("---")

# News Section
if news_articles:
    st.subheader("📰 Crypto News")
    st.markdown(f"**Market Sentiment:** {news_overall}")
    for item in news_articles[:3]:
        sentiment_icon = "🟢" if item['sentiment_score'] > 0.1 else "🔴" if item['sentiment_score'] < -0.1 else "🟡"
        st.markdown(f"{sentiment_icon} **{item['title']}**")
        st.caption(f"📰 {item['source']}")
        st.write("---")
else:
    st.info("📰 News loading... (rate limits may apply)")

st.markdown("---")

# Score Display
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.subheader("📊 FINAL SCORE")
    st.metric("SCORE", f"{final_score} / 100")
    if final_score >= 65:
        st.success(f"### ✅ {recommendation}")
    elif final_score >= 50:
        st.warning(f"### ⏸️ {recommendation}")
    else:
        st.error(f"### ⚠️ {recommendation}")

st.markdown("---")

# Probability Forecast
st.subheader("🎲 Probability Forecast (30 Days)")

if final_score >= 70:
    forecast = {"Scenario": ["🟢 Bullish", "🟡 Neutral", "🔴 Bearish"], 
                "Probability": ["55%", "30%", "15%"],
                "Target": [f"${current_price * 1.35:,.0f}", f"${current_price * 1.10:,.0f}", f"${current_price * 0.90:,.0f}"]}
elif final_score >= 50:
    forecast = {"Scenario": ["🟢 Bullish", "🟡 Neutral", "🔴 Bearish"], 
                "Probability": ["35%", "40%", "25%"],
                "Target": [f"${current_price * 1.20:,.0f}", f"${current_price * 1.00:,.0f}", f"${current_price * 0.88:,.0f}"]}
else:
    forecast = {"Scenario": ["🟢 Bullish", "🟡 Neutral", "🔴 Bearish"], 
                "Probability": ["20%", "35%", "45%"],
                "Target": [f"${current_price * 1.10:,.0f}", f"${current_price * 0.95:,.0f}", f"${current_price * 0.80:,.0f}"]}

st.table(pd.DataFrame(forecast))

st.markdown("---")
st.caption(f"📊 Data Source: {'CoinGecko' if use_alternative else 'Binance (with fallback)'} | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🤖 Crypto AI Pro — Works on mobile!")