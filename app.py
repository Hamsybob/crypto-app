import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
        "Bitcoin (BTC)": "bitcoin",
        "Ethereum (ETH)": "ethereum",
        "Zcash (ZEC)": "zcash",
        "Solana (SOL)": "solana",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "Dogecoin (DOGE)": "dogecoin",
        "Cardano (ADA)": "cardano"
    }
    
    selected_coin = st.selectbox("Coin", list(coin_options.keys()))
    coin_id = coin_options[selected_coin]
    ticker = coin_id.upper()[:3].upper()
    
    st.markdown("---")
    
    st.subheader("⏰ Timeframe")
    timeframe = st.selectbox("Chart Timeframe", ["1h", "4h", "1d", "7d"], index=2)
    
    st.markdown("---")
    
    st.subheader("🔑 API Keys (Optional)")
    news_api_key = st.text_input("NewsAPI Key", type="password", 
                                  help="Get from newsapi.org (free tier: 100 requests/day)")
    
    st.markdown("---")
    st.caption("✅ Using CoinGecko API (more reliable on cloud)")

# ============================================
# AI TRADING BOT
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
"""
            elif score >= 55:
                return f"""
🟡 **CAUTIOUS BUY** (Score: {score}/100)
- Entry: ${price * 0.98:.2f} - ${price:.2f}
- Stop Loss: ${price * 0.94:.2f}
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
# COINGECKO API FUNCTIONS (Primary - Most Reliable)
# ============================================

@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_coingecko_price(coin_id):
    """Fetch current price from CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if coin_id in data:
                return {
                    'price': data[coin_id]['usd'],
                    'change_24h': data[coin_id].get('usd_24h_change', 0),
                    'volume': data[coin_id].get('usd_24h_vol', 0),
                    'market_cap': data[coin_id].get('usd_market_cap', 0)
                }
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_coingecko_history(coin_id, days=30):
    """Fetch historical price data"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            prices = data.get('prices', [])
            return [p[1] for p in prices]  # Return just prices
        return []
    except:
        return []

def fetch_coingecko_ohlc(coin_id, days=7):
    """Fetch OHLC data for candlestick chart"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
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

def calculate_rsi(prices, period=14):
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

# ============================================
# MAIN APP
# ============================================

# Fetch current price
with st.spinner("Fetching market data..."):
    price_data = fetch_coingecko_price(coin_id)

if not price_data:
    st.error("❌ Unable to fetch data. Please try again in a few seconds.")
    st.info("CoinGecko API may be rate limited. Wait 60 seconds and refresh.")
    st.stop()

current_price = price_data['price']
price_change_percent = price_data['change_24h']
volume = price_data.get('volume', 0)
market_cap = price_data.get('market_cap', 0)

# Calculate high/low from historical data
historical_prices = fetch_coingecko_history(coin_id, days=7)
if historical_prices:
    high_24h = max(historical_prices[-24:]) if len(historical_prices) >= 24 else current_price * 1.05
    low_24h = min(historical_prices[-24:]) if len(historical_prices) >= 24 else current_price * 0.95
else:
    high_24h = current_price * 1.05
    low_24h = current_price * 0.95

# Fetch OHLC for chart
ohlc_df = fetch_coingecko_ohlc(coin_id, days=7)

# Fetch Fear & Greed
fg_value, fg_label = fetch_fear_greed()

# Fetch BTC Dominance
btc_dom = fetch_btc_dominance()

# Fetch News
news_sentiment, news_overall, news_articles = fetch_crypto_news(news_api_key)

# Calculate RSI from historical prices
if historical_prices and len(historical_prices) > 20:
    rsi = calculate_rsi(historical_prices)
else:
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

# Market data for bot
market_data = {
    'symbol': ticker,
    'price': current_price,
    'change': price_change_percent,
    'high': high_24h,
    'low': low_24h,
    'rsi': rsi,
    'stoch': stoch,
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
if ohlc_df is not None and len(ohlc_df) > 0:
    fig = go.Figure(data=[go.Candlestick(
        x=ohlc_df['time'],
        open=ohlc_df['open'],
        high=ohlc_df['high'],
        low=ohlc_df['low'],
        close=ohlc_df['close'],
        name='Price'
    )])
    fig.update_layout(title=f"{selected_coin} — {timeframe} Chart", yaxis_title='Price (USD)', 
                      xaxis_title='Date', template='plotly_dark', height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Chart data loading...")

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
    if rr_ratio > 2:
        st.success("✅ Excellent")
    elif rr_ratio > 1.5:
        st.info("👍 Good")
    else:
        st.warning("⚠️ Poor")

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
st.caption(f"📊 Data Source: CoinGecko API | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🤖 Crypto AI Pro — Complete Analysis with AI Trading Assistant")