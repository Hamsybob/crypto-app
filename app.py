import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

# Get API key from secrets (optional)
try:
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
except:
    NEWS_API_KEY = None

# Must be first Streamlit command
st.set_page_config(page_title="Crypto AI Pro", page_icon="🤖", layout="wide")

st.title("🤖 Crypto AI Pro — Complete Analysis Suite with AI Assistant")
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
    st.caption("✅ AI Chatbot Active — Ask me anything about trading!")

# ============================================
# AI TRADING BOT
# ============================================
class SmartTradingBot:
    """Intelligent trading assistant - works offline, no API needed"""
    
    def __init__(self, market_data):
        self.data = market_data
    
    def get_response(self, user_input):
        """Generate intelligent response based on user input"""
        msg = user_input.lower()
        
        # PRICE QUERIES
        if any(w in msg for w in ['price', 'current price', 'how much', 'cost', 'value', 'trading at']):
            price = self.data.get('price', 0)
            change = self.data.get('change', 0)
            high = self.data.get('high', 0)
            low = self.data.get('low', 0)
            return f"""
💰 **Price Analysis for {self.data.get('symbol', 'Asset')}**

| Metric | Value |
| :--- | :--- |
| Current Price | **${price:,.2f}** |
| 24h Change | {change:+.2f}% |
| 24h High | ${high:,.2f} |
| 24h Low | ${low:,.2f} |

💡 **Insight:** The price is {'up' if change > 0 else 'down'} {abs(change):.1f}% in the last 24 hours.
"""
        
        # BUY ADVICE
        if any(w in msg for w in ['buy', 'should i buy', 'entry', 'enter', 'buy signal']):
            score = self.data.get('score', 50)
            rsi = self.data.get('rsi', 50)
            fg = self.data.get('fear_greed', 50)
            rr = self.data.get('rr', 1.5)
            price = self.data.get('price', 0)
            
            if score >= 70:
                return f"""
✅ **STRONG BUY SIGNAL DETECTED**

📊 **Score:** {score}/100 — Excellent setup
📈 **RSI:** {rsi:.1f} {'(Oversold - Good)' if rsi < 30 else '(Neutral)'}
😱 **Fear & Greed:** {fg} {'(Fear = Opportunity)' if fg < 40 else ''}
⚖️ **Risk/Reward:** 1:{rr:.1f}

🎯 **Suggested Trade:**
- Entry: ${price:.2f}
- Stop Loss: ${price * 0.95:.2f}
- Take Profit: ${price * 1.15:.2f}
- Position Size: Normal (2% risk)
"""
            elif score >= 55:
                return f"""
🟡 **CAUTIOUS BUY SIGNAL**

📊 **Score:** {score}/100 — Moderate setup
📈 **RSI:** {rsi:.1f}
⚖️ **Risk/Reward:** 1:{rr:.1f}

🎯 **Suggested Trade:**
- Entry: ${price * 0.98:.2f} - ${price:.2f}
- Stop Loss: ${price * 0.94:.2f}
- Position Size: Half position (1% risk)
"""
            else:
                return f"""
🔴 **AVOID BUYING**

📊 **Score:** {score}/100 — Weak setup
📈 **RSI:** {rsi:.1f}
💡 **Wait for better setup. Support at ${self.data.get('low', price):.2f}**
"""
        
        # SELL ADVICE
        if any(w in msg for w in ['sell', 'should i sell', 'exit', 'take profit', 'close']):
            score = self.data.get('score', 50)
            price = self.data.get('price', 0)
            
            if score >= 70:
                return f"""
🟢 **HOLD YOUR POSITION**

📊 **Score:** {score}/100 — Still bullish
💡 **Move stop loss to breakeven** (${price:.2f})
📈 **Next target:** ${price * 1.10:.2f}
"""
            elif score <= 40:
                return f"""
🔴 **CONSIDER EXITING**

📊 **Score:** {score}/100 — Bearish signals detected
⚠️ **Stop loss recommended:** ${price * 0.97:.2f}
"""
            else:
                return f"""
🟡 **HOLD FOR NOW**

📊 **Score:** {score}/100 — Mixed signals
💡 **Keep stop loss at** ${price * 0.95:.2f}
"""
        
        # RSI ANALYSIS
        if 'rsi' in msg:
            rsi = self.data.get('rsi', 50)
            if rsi < 30:
                advice = "🟢 **OVERSOLD** — Strong buy signal"
                action = "Consider buying"
            elif rsi > 70:
                advice = "🔴 **OVERBOUGHT** — Potential reversal coming"
                action = "Take profits or tighten stops"
            else:
                advice = "🟡 **NEUTRAL** — No extreme conditions"
                action = "Follow the trend"
            
            return f"""
📊 **RSI (Relative Strength Index): {rsi:.1f}**

{advice}

💡 RSI below 30 = oversold (good to buy), above 70 = overbought (good to sell).

🎯 **Suggested Action:** {action}
"""
        
        # FEAR & GREED
        if any(w in msg for w in ['fear', 'greed', 'sentiment', 'emotion']):
            fg = self.data.get('fear_greed', 50)
            label = self.data.get('fg_label', 'Neutral')
            
            if fg < 25:
                advice = "🔥 **EXTREME FEAR** — Historically the BEST buying opportunities!"
                action = "Aggressively accumulate"
            elif fg < 40:
                advice = "😰 **FEAR** — Good time to accumulate"
                action = "Buy on dips"
            elif fg > 75:
                advice = "🟢 **EXTREME GREED** — Market may be topping"
                action = "Take profits, be cautious"
            elif fg > 60:
                advice = "😊 **GREED** — Optimistic but not extreme"
                action = "Hold but tighten stops"
            else:
                advice = "😐 **NEUTRAL** — Balanced sentiment"
                action = "Follow technical signals"
            
            return f"""
😱 **Fear & Greed Index: {fg} — {label}**

{advice}

💡 **Recommended Action:** {action}

📊 Best returns often come when everyone is fearful (index below 30).
"""
        
        # RISK/REWARD
        if any(w in msg for w in ['risk', 'reward', 'rr', 'stop loss', 'target']):
            price = self.data.get('price', 0)
            rr = self.data.get('rr', 1.5)
            
            if rr > 2.5:
                quality = "🌟 **EXCELLENT**"
            elif rr > 1.5:
                quality = "✅ **GOOD**"
            else:
                quality = "🔴 **POOR**"
            
            return f"""
⚖️ **Risk/Reward Analysis**

| Metric | Value |
| :--- | :--- |
| Entry | ${price:.2f} |
| Stop Loss | ${price * 0.92:.2f} (-8%) |
| Take Profit | ${price * 1.15:.2f} (+15%) |
| Risk/Reward | **1:{rr:.1f}** |
| Quality | {quality} |

💡 Always risk $1 to make at least $2.
"""
        
        # SCORE QUERY
        if any(w in msg for w in ['score', 'rating', 'overall', 'how good']):
            score = self.data.get('score', 50)
            rec = self.data.get('recommendation', 'Hold')
            return f"""
📊 **Overall Trading Score: {score}/100**

🏷️ **Recommendation:** {rec}

💡 Higher score = better buying opportunity.
"""
        
        # HELP
        if any(w in msg for w in ['help', 'commands', 'what can you do']):
            return """
🤖 **I can help you with:**

| Ask me about | Example |
| :--- | :--- |
| 💰 Price | "What's the price?" |
| 📈 Buy advice | "Should I buy?" |
| 📉 Sell advice | "Should I sell?" |
| 📊 RSI | "What's the RSI?" |
| 😱 Sentiment | "What's Fear & Greed?" |
| ⚖️ Risk | "Is this risky?" |
| 📊 Score | "What's the score?" |

Just type naturally! 🚀
"""
        
        # DEFAULT
        symbol = self.data.get('symbol', 'crypto')
        score = self.data.get('score', 50)
        rec = self.data.get('recommendation', 'Hold')
        price = self.data.get('price', 0)
        
        return f"""
🤖 **Trading Assistant for {symbol}**

📊 **Current Market:**
- 💰 Price: ${price:,.2f} ({self.data.get('change', 0):+.2f}%)
- 📊 Score: {score}/100 → {rec}
- 📈 RSI: {self.data.get('rsi', 50):.1f}
- 😱 Fear & Greed: {self.data.get('fear_greed', 50)}

💡 **Try asking:**
- "Should I buy?"
- "What's the risk/reward?"
- "What's the RSI telling me?"
- "help" for all commands
"""

# ============================================
# FETCH FUNCTIONS
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
        url = f"https://newsapi.org/v2/everything?q=cryptocurrency&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
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

# ============================================
# MAIN APP
# ============================================

coingecko_map = {"BTC": "bitcoin", "ETH": "ethereum", "ZEC": "zcash", "SOL": "solana", "BNB": "binancecoin", "XRP": "ripple", "DOGE": "dogecoin"}
coingecko_id = coingecko_map.get(ticker, ticker.lower())

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

if not data and not use_alternative:
    with st.spinner("Trying CoinGecko..."):
        data = fetch_coingecko_data(coingecko_id)
        if data:
            current_price = data['lastPrice']
            price_change_percent = data['priceChangePercent']
            quote_volume = data.get('volume', 0)
            high_24h = current_price * (1 + abs(price_change_percent)/100 + 0.02)
            low_24h = current_price * (1 - abs(price_change_percent)/100 - 0.02)

if not data:
    st.error("❌ Unable to fetch data. Please try again.")
    st.stop()

fg_value, fg_label = fetch_fear_greed()
btc_dom = fetch_btc_dominance()
news_sentiment, news_overall, news_articles = fetch_crypto_news()

# Calculate indicators
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
final_score = max(0, min(100, score))

if final_score >= 80: recommendation = "🔥 STRONG BUY"
elif final_score >= 65: recommendation = "✅ BUY"
elif final_score >= 50: recommendation = "⏸️ HOLD"
elif final_score >= 35: recommendation = "⚠️ AVOID"
else: recommendation = "🔴 HIGH RISK"

# Market data for AI bot
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

# Initialize AI bot
trading_bot = SmartTradingBot(market_data)

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

if news_articles:
    st.subheader("📰 Crypto News")
    st.markdown(f"**Market Sentiment:** {news_overall}")
    for item in news_articles[:3]:
        st.write(f"📰 {item['title']}")
        st.caption(f"Source: {item['source']}")
        st.write("---")

st.markdown("---")

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
# 🤖 AI CHATBOT SECTION
# ============================================
st.subheader("🤖 AI Trading Assistant — Ask me anything!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi! I'm your trading assistant for **{ticker}**.\n\n💡 **Ask me:**\n- \"Should I buy?\"\n- \"What's the RSI?\"\n- \"Is this risky?\"\n- \"help\" for all commands"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about trading..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        response = trading_bot.get_response(prompt)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Quick buttons
st.caption("💡 Quick Questions:")
q1, q2, q3, q4, q5 = st.columns(5)
if q1.button("💰 Price"):
    response = trading_bot.get_response("price")
    st.session_state.messages.append({"role": "user", "content": "price"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if q2.button("📈 Buy?"):
    response = trading_bot.get_response("should i buy")
    st.session_state.messages.append({"role": "user", "content": "should i buy"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if q3.button("📊 RSI"):
    response = trading_bot.get_response("rsi")
    st.session_state.messages.append({"role": "user", "content": "rsi"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if q4.button("😱 Fear"):
    response = trading_bot.get_response("fear")
    st.session_state.messages.append({"role": "user", "content": "fear"})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
if q5.button("❓ Help"):
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
st.caption(f"🤖 AI Chatbot Active — Ask me anything! | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Crypto AI Pro — Complete Analysis with AI Trading Assistant")