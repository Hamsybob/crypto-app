import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Crypto AI Pro", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile display
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Better card styling */
    .stMetric {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3a 100%);
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Success/Error/Warning boxes */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Chat messages */
    .stChatMessage {
        background: linear-gradient(135deg, #2a2a3a 0%, #1e1e2e 100%);
        border-radius: 15px;
        padding: 10px;
        margin: 5px 0;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* Dataframe */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Metrics row */
    .row-widget {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Crypto AI Pro — Ultimate Trading Suite")
st.markdown("---")

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## 🚀 Dashboard")
    st.markdown("---")
    
    st.markdown("### 📊 Select Asset")
    coin_options = {
        "Bitcoin (BTC)": "BTCUSDT",
        "Ethereum (ETH)": "ETHUSDT",
        "Zcash (ZEC)": "ZECUSDT",
        "Solana (SOL)": "SOLUSDT",
        "BNB": "BNBUSDT",
        "XRP": "XRPUSDT",
        "Dogecoin (DOGE)": "DOGEUSDT"
    }
    
    selected_coin = st.selectbox("", list(coin_options.keys()), index=2)
    trading_pair = coin_options[selected_coin]
    ticker = trading_pair.replace("USDT", "")
    
    st.markdown("---")
    
    st.markdown("### ⏰ Chart Timeframe")
    timeframe = st.radio("", ["1h", "4h", "1d", "1w"], index=2, horizontal=True)
    
    st.markdown("---")
    
    st.markdown("### 📰 News API")
    news_api_key = st.text_input("NewsAPI Key (Optional)", type="password", 
                                  placeholder="Get free at newsapi.org", 
                                  help="100 free requests/day")
    
    st.markdown("---")
    st.markdown("### 📱 Mobile Ready")
    st.caption("✅ Works on phone browser")
    st.caption("✅ Add to home screen for app-like experience")
    st.markdown("---")
    st.markdown("**Data Source:** Binance (Live)")

# ============================================
# AI TRADING BOT
# ============================================
class TradingBot:
    def __init__(self, market_data):
        self.data = market_data
    
    def get_response(self, user_input):
        msg = user_input.lower()
        
        if any(w in msg for w in ['price', 'current price', 'how much', 'cost', 'value']):
            return f"""
<div style='background: linear-gradient(135deg, #1a5c3a 0%, #0d3b23 100%); padding: 15px; border-radius: 12px;'>
<h4>💰 Price Analysis for {self.data.get('symbol', 'Asset')}</h4>
<table style='width:100%;'>
<tr><td><b>Current Price:</b></td><td style='color:#00ff00; font-size:20px;'>${self.data.get('price', 0):,.2f}</td></tr>
<tr><td><b>24h Change:</b></td><td style='color:{'#00ff00' if self.data.get('change', 0) >= 0 else '#ff4444'}'>{self.data.get('change', 0):+.2f}%</td></tr>
<tr><td><b>24h High:</b></td><td>${self.data.get('high', 0):,.2f}</td></tr>
<tr><td><b>24h Low:</b></td><td>${self.data.get('low', 0):,.2f}</td></tr>
</table>
</div>
"""
        
        if any(w in msg for w in ['buy', 'should i buy', 'entry', 'enter']):
            score = self.data.get('score', 50)
            price = self.data.get('price', 0)
            rsi = self.data.get('rsi', 50)
            
            if score >= 70:
                return f"""
<div style='background: linear-gradient(135deg, #1a5c3a 0%, #0d3b23 100%); padding: 15px; border-radius: 12px;'>
<h4>✅ STRONG BUY SIGNAL</h4>
<p><b>Score:</b> {score}/100 - Excellent setup</p>
<p><b>RSI:</b> {rsi:.1f} {'(Oversold)' if rsi < 30 else '(Neutral)'}</p>
<p><b>Entry:</b> ${price:.2f}</p>
<p><b>Stop Loss:</b> ${price * 0.95:.2f}</p>
<p><b>Take Profit:</b> ${price * 1.15:.2f}</p>
<p><b>Position Size:</b> 2% risk</p>
</div>
"""
            elif score >= 55:
                return f"""
<div style='background: linear-gradient(135deg, #5c4a1a 0%, #3b2d0d 100%); padding: 15px; border-radius: 12px;'>
<h4>🟡 CAUTIOUS BUY SIGNAL</h4>
<p><b>Score:</b> {score}/100 - Moderate setup</p>
<p><b>Entry:</b> ${price * 0.98:.2f} - ${price:.2f}</p>
<p><b>Stop Loss:</b> ${price * 0.94:.2f}</p>
<p><b>Position Size:</b> 1% risk</p>
</div>
"""
            else:
                return f"""
<div style='background: linear-gradient(135deg, #5c1a1a 0%, #3b0d0d 100%); padding: 15px; border-radius: 12px;'>
<h4>🔴 AVOID BUYING</h4>
<p><b>Score:</b> {score}/100 - Weak setup</p>
<p><b>RSI:</b> {rsi:.1f}</p>
<p>Wait for better entry conditions.</p>
</div>
"""
        
        if 'rsi' in msg:
            rsi = self.data.get('rsi', 50)
            if rsi < 30:
                signal = "🟢 OVERSOLD - Strong Buy Signal"
            elif rsi > 70:
                signal = "🔴 OVERBOUGHT - Caution Advised"
            else:
                signal = "🟡 NEUTRAL - Follow Trend"
            return f"""
<div style='background: linear-gradient(135deg, #1e2a5c 0%, #0d1a3b 100%); padding: 15px; border-radius: 12px;'>
<h4>📊 RSI (Relative Strength Index)</h4>
<p><b>Value:</b> {rsi:.1f}</p>
<p><b>Signal:</b> {signal}</p>
<p><small>RSI below 30 = oversold (buy), above 70 = overbought (sell)</small></p>
</div>
"""
        
        if any(w in msg for w in ['fear', 'greed', 'sentiment']):
            fg = self.data.get('fear_greed', 50)
            label = self.data.get('fg_label', 'Neutral')
            if fg < 30:
                advice = "🔥 EXTREME FEAR - Historically a BUY opportunity!"
            elif fg > 70:
                advice = "🟢 EXTREME GREED - Market may top, be cautious"
            else:
                advice = "😐 NEUTRAL - Normal market conditions"
            return f"""
<div style='background: linear-gradient(135deg, #2a1a5c 0%, #1a0d3b 100%); padding: 15px; border-radius: 12px;'>
<h4>😱 Fear & Greed Index</h4>
<p><b>Value:</b> {fg} - {label}</p>
<p><b>Insight:</b> {advice}</p>
</div>
"""
        
        if any(w in msg for w in ['score', 'rating']):
            return f"""
<div style='background: linear-gradient(135deg, #1a5c3a 0%, #0d3b23 100%); padding: 15px; border-radius: 12px;'>
<h4>📊 Overall Trading Score</h4>
<p><b>Score:</b> {self.data.get('score', 50)}/100</p>
<p><b>Recommendation:</b> {self.data.get('recommendation', 'Hold')}</p>
</div>
"""
        
        if 'help' in msg:
            return """
<div style='background: linear-gradient(135deg, #2a2a3a 0%, #1a1a2a 100%); padding: 15px; border-radius: 12px;'>
<h4>🤖 Commands You Can Ask:</h4>
<ul>
<li>💰 "What's the price?"</li>
<li>📈 "Should I buy?"</li>
<li>📊 "What's the RSI?"</li>
<li>😱 "Market sentiment?"</li>
<li>📊 "What's the score?"</li>
</ul>
</div>
"""
        
        return f"""
<div style='background: linear-gradient(135deg, #2a2a3a 0%, #1a1a2a 100%); padding: 15px; border-radius: 12px;'>
<h4>🤖 Trading Assistant for {self.data.get('symbol', 'crypto')}</h4>
<p>💰 Price: ${self.data.get('price', 0):,.2f} ({self.data.get('change', 0):+.2f}%)</p>
<p>📊 Score: {self.data.get('score', 50)}/100 → {self.data.get('recommendation', 'Hold')}</p>
<p>📈 RSI: {self.data.get('rsi', 50):.1f}</p>
<p>😱 Fear & Greed: {self.data.get('fear_greed', 50)}</p>
<br>
<p>💡 <b>Try:</b> "Should I buy?" or "help"</p>
</div>
"""

# ============================================
# DATA FETCHING - RELIABLE VERSION
# ============================================

@st.cache_data(ttl=30)
def fetch_binance_data(symbol_pair):
    """Fetch data from Binance with retry logic"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    for attempt in range(3):
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_pair}"
            response = requests.get(url, timeout=10, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                time.sleep(2)
                continue
        except:
            time.sleep(1)
            continue
    return None

@st.cache_data(ttl=60)
def fetch_klines_data(symbol_pair, interval="1h", limit=100):
    """Fetch klines for chart"""
    interval_map = {"1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"}
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol_pair}&interval={interval_map.get(interval, '1d')}&limit={limit}"
        response = requests.get(url, timeout=10, headers=headers)
        
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
        pass
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

def calculate_rsi_from_data(df, period=14):
    """Calculate RSI from dataframe"""
    if df is None or len(df) < period + 1:
        return 50
    close_prices = df['close'].values
    gains = []
    losses = []
    for i in range(1, period + 1):
        change = close_prices[i] - close_prices[i-1]
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
    return 100 - (100 / (1 + rs))

# ============================================
# MAIN APP
# ============================================

# Show loading message
status_placeholder = st.empty()
status_placeholder.info("🔄 Fetching live market data...")

# Fetch data
data = fetch_binance_data(trading_pair)

if not data:
    status_placeholder.error("❌ Unable to connect to Binance. Please refresh the page.")
    st.info("💡 **Troubleshooting Tips:**\n- Wait 30 seconds and press F5 to refresh\n- Check your internet connection\n- Binance API may be temporarily busy")
    st.stop()

status_placeholder.empty()

# Extract data
current_price = float(data['lastPrice'])
price_change_percent = float(data['priceChangePercent'])
high_24h = float(data['highPrice'])
low_24h = float(data['lowPrice'])
quote_volume = float(data['quoteVolume'])

# Fetch additional data
klines_df = fetch_klines_data(trading_pair, timeframe)
fg_value, fg_label = fetch_fear_greed()
btc_dom = fetch_btc_dominance()
news_sentiment, news_overall, news_articles = fetch_crypto_news(news_api_key)

# Calculate indicators
if klines_df is not None and len(klines_df) > 20:
    rsi = calculate_rsi_from_data(klines_df)
else:
    if price_change_percent > 5:
        rsi = 65
    elif price_change_percent < -5:
        rsi = 35
    else:
        rsi = 50

if price_change_percent > 5:
    stoch = 70
elif price_change_percent < -5:
    stoch = 30
else:
    stoch = 50

macd_bullish = price_change_percent > 0
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
# DISPLAY METRICS
# ============================================

st.markdown(f"## 📈 {selected_coin} Analysis")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Price", 
        f"${current_price:,.2f}", 
        f"{price_change_percent:+.2f}%",
        delta_color="normal"
    )

with col2:
    st.metric("📈 24h High", f"${high_24h:,.2f}")

with col3:
    st.metric("📉 24h Low", f"${low_24h:,.2f}")

with col4:
    # Fear & Greed with color
    fg_color = "🟢" if fg_value > 70 else "🔴" if fg_value < 30 else "🟡"
    st.metric("😱 Fear & Greed", f"{fg_color} {fg_value} — {fg_label}")

st.markdown("---")

# Candlestick Chart
if klines_df is not None and len(klines_df) > 0:
    fig = go.Figure(data=[go.Candlestick(
        x=klines_df['time'],
        open=klines_df['open'],
        high=klines_df['high'],
        low=klines_df['low'],
        close=klines_df['close'],
        name='Price'
    )])
    
    fig.update_layout(
        title=f"{selected_coin} — {timeframe} Chart",
        yaxis_title='Price (USD)',
        xaxis_title='Time',
        template='plotly_dark',
        height=450,
        xaxis_rangeslider_visible=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_xaxes(gridcolor='#333333')
    fig.update_yaxes(gridcolor='#333333')
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 Chart data loading...")

st.markdown("---")

# Technical Indicators
st.subheader("📊 Technical Indicators")

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
    if stoch < 20:
        st.success("🟢 Oversold")
    elif stoch > 80:
        st.warning("🔴 Overbought")
    else:
        st.info("🟡 Neutral")

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
        st.info(f"📰 {item['title']}\n\n📰 Source: {item['source']}")
        st.markdown("---")

# Score Display
st.subheader("📊 Overall Score")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"<h1 style='text-align: center; font-size: 48px;'>{final_score}/100</h1>", unsafe_allow_html=True)
    
    if final_score >= 65:
        st.success(f"<h3 style='text-align: center;'>{recommendation}</h3>", unsafe_allow_html=True)
    elif final_score >= 50:
        st.warning(f"<h3 style='text-align: center;'>{recommendation}</h3>", unsafe_allow_html=True)
    else:
        st.error(f"<h3 style='text-align: center;'>{recommendation}</h3>", unsafe_allow_html=True)

st.markdown("---")

# ============================================
# AI CHATBOT
# ============================================
st.subheader("🤖 AI Trading Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi! I'm your trading assistant for **{ticker}**.\n\n**Try asking:**\n• Should I buy?\n• What's the RSI?\n• Market sentiment?\n• help"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask me about trading..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🤖 Analyzing..."):
            response = trading_bot.get_response(prompt)
            st.markdown(response, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Quick buttons
st.caption("💡 Quick Questions:")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("💰 Price", use_container_width=True):
        response = trading_bot.get_response("price")
        st.session_state.messages.append({"role": "user", "content": "price"})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with col2:
    if st.button("📈 Buy?", use_container_width=True):
        response = trading_bot.get_response("should i buy")
        st.session_state.messages.append({"role": "user", "content": "should i buy"})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with col3:
    if st.button("📊 RSI", use_container_width=True):
        response = trading_bot.get_response("rsi")
        st.session_state.messages.append({"role": "user", "content": "rsi"})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with col4:
    if st.button("😱 Fear", use_container_width=True):
        response = trading_bot.get_response("fear")
        st.session_state.messages.append({"role": "user", "content": "fear"})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with col5:
    if st.button("❓ Help", use_container_width=True):
        response = trading_bot.get_response("help")
        st.session_state.messages.append({"role": "user", "content": "help"})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

st.markdown("---")

# Probability Forecast
st.subheader("🎲 Probability Forecast (30 Days)")

if final_score >= 70:
    forecast = pd.DataFrame({
        "Scenario": ["🟢 Bullish", "🟡 Neutral", "🔴 Bearish"],
        "Probability": ["55%", "30%", "15%"],
        "Target": [f"${current_price * 1.35:,.0f}", f"${current_price * 1.10:,.0f}", f"${current_price * 0.90:,.0f}"]
    })
elif final_score >= 50:
    forecast = pd.DataFrame({
        "Scenario": ["🟢 Bullish", "🟡 Neutral", "🔴 Bearish"],
        "Probability": ["35%", "40%", "25%"],
        "Target": [f"${current_price * 1.20:,.0f}", f"${current_price * 1.00:,.0f}", f"${current_price * 0.88:,.0f}"]
    })
else:
    forecast = pd.DataFrame({
        "Scenario": ["🟢 Bullish", "🟡 Neutral", "🔴 Bearish"],
        "Probability": ["20%", "35%", "45%"],
        "Target": [f"${current_price * 1.10:,.0f}", f"${current_price * 0.95:,.0f}", f"${current_price * 0.80:,.0f}"]
    })

st.dataframe(forecast, use_container_width=True, hide_index=True)

st.markdown("---")

# Footer
st.caption(f"""
**Status:** ✅ Live Data from Binance  
**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Version:** Ultimate Crypto AI Pro — Mobile Ready  
💡 **Tip:** Add this page to your phone's home screen for app-like experience
""")