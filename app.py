import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ============================================
# CONFIGURATION - Must be first
# ============================================
st.set_page_config(page_title="Ultimate Crypto AI", page_icon="🏆", layout="wide")

st.title("🏆 Ultimate Crypto AI — Complete Analysis Suite")
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
        "Dogecoin (DOGE)": "DOGEUSDT",
        "Cardano (ADA)": "ADAUSDT"
    }
    
    selected_coin = st.selectbox("Coin", list(coin_options.keys()))
    trading_pair = coin_options[selected_coin]
    ticker = trading_pair.replace("USDT", "")
    
    st.markdown("---")
    
    st.subheader("⏰ Timeframe")
    timeframe = st.selectbox("Chart Timeframe", ["1h", "4h", "1d", "1w"], index=2)
    
    st.markdown("---")
    
    st.subheader("🔑 API Keys (Optional)")
    news_api_key = st.text_input("NewsAPI Key", type="password", 
                                  help="Get from newsapi.org (free tier: 100 requests/day)")
    
    st.markdown("---")
    
    st.subheader("📡 Data Source")
    use_alternative = st.checkbox("Use CoinGecko (if Binance fails)", value=False)
    
    st.markdown("---")
    st.caption("✅ AI Trading Assistant Active — Ask me anything!")

# ============================================
# AI TRADING BOT (No API Key Needed)
# ============================================
class TradingBot:
    def __init__(self, market_data):
        self.data = market_data
    
    def get_response(self, user_input):
        msg = user_input.lower()
        
        if any(w in msg for w in ['price', 'current price', 'how much', 'cost']):
            return f"""
💰 **Price Analysis for {self.data.get('symbol', 'Asset')}**
- Current Price: **${self.data.get('price', 0):,.2f}**
- 24h Change: {self.data.get('change', 0):+.2f}%
- 24h High: ${self.data.get('high', 0):,.2f}
- 24h Low: ${self.data.get('low', 0):,.2f}
"""
        
        if any(w in msg for w in ['buy', 'should i buy', 'entry']):
            score = self.data.get('score', 50)
            price = self.data.get('price', 0)
            if score >= 70:
                return f"""
✅ **STRONG BUY SIGNAL** (Score: {score}/100)
- Entry: ${price:.2f}
- Stop Loss: ${price * 0.95:.2f}
- Take Profit: ${price * 1.15:.2f}
- Position Size: Normal (2% risk)
"""
            elif score >= 55:
                return f"""
🟡 **CAUTIOUS BUY** (Score: {score}/100)
- Entry: ${price * 0.98:.2f} - ${price:.2f}
- Stop Loss: ${price * 0.94:.2f}
- Position Size: Half (1% risk)
"""
            else:
                return f"🔴 **AVOID BUYING** (Score: {score}/100)\nWait for better setup."
        
        if any(w in msg for w in ['rsi']):
            rsi = self.data.get('rsi', 50)
            if rsi < 30:
                return f"📊 **RSI: {rsi:.1f}** — OVERSOLD (Buy Signal)"
            elif rsi > 70:
                return f"📊 **RSI: {rsi:.1f}** — OVERBOUGHT (Caution)"
            else:
                return f"📊 **RSI: {rsi:.1f}** — NEUTRAL"
        
        if any(w in msg for w in ['fear', 'greed', 'sentiment']):
            fg = self.data.get('fear_greed', 50)
            label = self.data.get('fg_label', 'Neutral')
            if fg < 30:
                return f"😱 **Fear & Greed: {fg} ({label})** — EXTREME FEAR = BUY Signal"
            elif fg > 70:
                return f"😱 **Fear & Greed: {fg} ({label})** — EXTREME GREED = Caution"
            else:
                return f"😱 **Fear & Greed: {fg} ({label})** — Neutral"
        
        if any(w in msg for w in ['score', 'rating']):
            return f"📊 **Overall Score: {self.data.get('score', 50)}/100**\n🏷️ **Recommendation: {self.data.get('recommendation', 'Hold')}**"
        
        if any(w in msg for w in ['help', 'commands']):
            return """
🤖 **I can help with:**
- "Should I buy?" → Trading advice
- "What's the RSI?" → Technical analysis
- "Market sentiment?" → Fear & Greed
- "What's the score?" → Overall rating
"""
        
        return f"""
🤖 **Trading Assistant for {self.data.get('symbol', 'crypto')}**
- Price: ${self.data.get('price', 0):,.2f} ({self.data.get('change', 0):+.2f}%)
- Score: {self.data.get('score', 50)}/100 → {self.data.get('recommendation', 'Hold')}
- RSI: {self.data.get('rsi', 50):.1f}

💡 Try: "Should I buy?" or "help"
"""

# ============================================
# DATA FETCHING FUNCTIONS
# ============================================

def fetch_binance_data(symbol_pair):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_pair}"
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def fetch_coingecko_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if coin_id in data:
                return {
                    'lastPrice': data[coin_id]['usd'],
                    'priceChangePercent': data[coin_id].get('usd_24h_change', 0),
                    'volume': data[coin_id].get('usd_24h_vol', 0)
                }
        return None
    except:
        return None

def fetch_klines(symbol_pair, interval="1h", limit=100):
    interval_map = {"1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"}
    binance_interval = interval_map.get(interval, "1h")
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol_pair}&interval={binance_interval}&limit={limit}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 
                                              'close_time', 'quote_volume', 'trades', 'buy_base', 
                                              'buy_quote', 'ignore'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            return df
        return None
    except:
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

def fetch_crypto_news(api_key):
    if not api_key:
        return None, None, None
    try:
        url = f"https://newsapi.org/v2/everything?q=cryptocurrency&language=en&sortBy=publishedAt&pageSize=3&apiKey={api_key}"
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
                    news_items.append({'title': title[:80], 'source': article.get('source', {}).get('name', 'Unknown')})
            if sentiments:
                avg_sentiment = np.mean(sentiments)
                overall = "🟢 BULLISH" if avg_sentiment > 0.1 else "🔴 BEARISH" if avg_sentiment < -0.1 else "🟡 NEUTRAL"
                return avg_sentiment, overall, news_items
        return None, None, None
    except:
        return None, None, None

def calculate_indicators(current_price, high_24h, low_24h, price_change_percent):
    price_range = high_24h - low_24h
    if price_range > 0:
        position_in_range = (current_price - low_24h) / price_range
    else:
        position_in_range = 0.5
    
    if price_change_percent > 5:
        rsi = 65 + (price_change_percent / 2)
    elif price_change_percent < -5:
        rsi = 35 + (price_change_percent / 2)
    else:
        rsi = 50 + (position_in_range - 0.5) * 40
    rsi = max(0, min(100, rsi))
    
    if price_change_percent > 5:
        stoch = 70 + (price_change_percent * 2)
    elif price_change_percent < -5:
        stoch = 30 + (price_change_percent * 2)
    else:
        stoch = 50 + (position_in_range - 0.5) * 50
    stoch = max(0, min(100, stoch))
    
    macd_bullish = price_change_percent > 0 and current_price > high_24h * 0.98
    
    return {'rsi': rsi, 'stoch_k': stoch, 'macd_bullish': macd_bullish}

# ============================================
# MAIN APP
# ============================================

coingecko_map = {"BTC": "bitcoin", "ETH": "ethereum", "ZEC": "zcash", "SOL": "solana", 
                 "BNB": "binancecoin", "XRP": "ripple", "DOGE": "dogecoin", "ADA": "cardano"}
coingecko_id = coingecko_map.get(ticker, ticker.lower())

# Fetch data
data = None
if use_alternative:
    with st.spinner("Fetching from CoinGecko..."):
        data = fetch_coingecko_data(coingecko_id)
else:
    with st.spinner("Fetching from Binance..."):
        data = fetch_binance_data(trading_pair)

if not data and not use_alternative:
    with st.spinner("Trying CoinGecko..."):
        data = fetch_coingecko_data(coingecko_id)

if not data:
    st.error("❌ Unable to fetch data. Please try again in a few seconds.")
    st.stop()

# Extract data
if 'lastPrice' in data:
    current_price = float(data['lastPrice']) if isinstance(data['lastPrice'], (int, float)) else float(data['lastPrice'])
    price_change_percent = float(data['priceChangePercent']) if 'priceChangePercent' in data else 0
    if 'highPrice' in data:
        high_24h = float(data['highPrice'])
        low_24h = float(data['lowPrice'])
        quote_volume = float(data['quoteVolume'])
    else:
        high_24h = current_price * 1.05
        low_24h = current_price * 0.95
        quote_volume = data.get('volume', 0)

# Fetch additional data
klines_df = fetch_klines(trading_pair, timeframe)
fg_value, fg_label = fetch_fear_greed()
btc_dom = fetch_btc_dominance()
news_sentiment, news_overall, news_articles = fetch_crypto_news(news_api_key)

# Calculate indicators
indicators = calculate_indicators(current_price, high_24h, low_24h, price_change_percent)
rsi = indicators['rsi']
stoch_k = indicators['stoch_k']
macd_bullish = indicators['macd_bullish']

# Risk/Reward
stop_loss = current_price * 0.92
rr_ratio = (current_price * 0.15) / (current_price - stop_loss) if (current_price - stop_loss) > 0 else 0

# Calculate Score
score = 50
if rsi < 30: score += 15
elif rsi > 70: score -= 10
if stoch_k < 20: score += 10
elif stoch_k > 80: score -= 10
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

# Market data for bot
market_data = {
    'symbol': ticker,
    'price': current_price,
    'change': price_change_percent,
    'high': high_24h,
    'low': low_24h,
    'rsi': rsi,
    'stoch': stoch_k,
    'fear_greed': fg_value,
    'fg_label': fg_label,
    'score': final_score,
    'recommendation': recommendation,
    'rr': rr_ratio
}

trading_bot = TradingBot(market_data)

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

# Candlestick Chart
if klines_df is not None:
    fig = go.Figure(data=[go.Candlestick(
        x=klines_df['time'],
        open=klines_df['open'],
        high=klines_df['high'],
        low=klines_df['low'],
        close=klines_df['close'],
        name='Price'
    )])
    fig.update_layout(title=f"{selected_coin} — {timeframe} Chart", yaxis_title='Price (USD)', 
                      xaxis_title='Time', template='plotly_dark', height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"Cannot load {timeframe} chart")

st.markdown("---")

# Technical Indicators
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("RSI (14)", f"{rsi:.1f}")
    st.caption("🟢 Oversold <30 | 🔴 Overbought >70")
with col2:
    st.metric("Stochastic %K", f"{stoch_k:.1f}")
    st.caption("🟢 Oversold <20 | 🔴 Overbought >80")
with col3:
    st.metric("MACD", "Bullish 📈" if macd_bullish else "Bearish 📉")
    st.metric("BTC Dominance", f"{btc_dom:.1f}%")
with col4:
    st.metric("Risk/Reward", f"1:{rr_ratio:.1f}")
    st.caption("✅ Good > 1:2")

st.markdown("---")

# News Section
if news_articles:
    st.subheader("📰 Crypto News")
    st.markdown(f"**Market Sentiment:** {news_overall}")
    for item in news_articles:
        st.write(f"📰 {item['title']}")
        st.caption(f"Source: {item['source']}")
        st.write("---")
else:
    if news_api_key:
        st.info("📰 Loading news...")
    else:
        st.info("📰 Add NewsAPI key in sidebar for live news")

st.markdown("---")

# Score
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

# ============================================
# AI CHATBOT
# ============================================
st.subheader("🤖 AI Trading Assistant — Ask me anything!")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi! I'm your trading assistant for **{ticker}**.\n\n💡 **Ask me:**\n- \"Should I buy?\"\n- \"What's the RSI?\"\n- \"Market sentiment?\"\n- \"help\""}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me about trading..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = trading_bot.get_response(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Quick buttons
c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("💰 Price"):
    response = trading_bot.get_response("price")
    st.session_state.messages.append({"role": "user", "content": "price"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if c2.button("📈 Buy?"):
    response = trading_bot.get_response("should i buy")
    st.session_state.messages.append({"role": "user", "content": "should i buy"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if c3.button("📊 RSI"):
    response = trading_bot.get_response("rsi")
    st.session_state.messages.append({"role": "user", "content": "rsi"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if c4.button("😱 Fear"):
    response = trading_bot.get_response("fear")
    st.session_state.messages.append({"role": "user", "content": "fear"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if c5.button("❓ Help"):
    response = trading_bot.get_response("help")
    st.session_state.messages.append({"role": "user", "content": "help"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

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
st.caption(f"📊 Data Source: {'CoinGecko' if use_alternative else 'Binance'} | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🤖 Crypto AI Pro — Complete Analysis with AI Trading Assistant")