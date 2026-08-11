import streamlit as st
from dotenv import load_dotenv
import os
import re
import requests

from huggingface_hub import InferenceClient

# DuckDuckGo search - package name is "duckduckgo-search" (newer versions
# also publish under "ddgs"). We try both so the app works either way.
try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS

# ---------------------------------------------------------
# Load Environment Variables
# ---------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Aqua AI Chatbot",
    page_icon="🐬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Custom CSS - New "Aurora" style: soft purple/teal gradient,
# glass-style cards, rounded pill bubbles. Completely different
# look from the old navy mascot theme.
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: radial-gradient(circle at top left, #0b2f4e 0%, #071b2c 45%, #04111c 100%);
        }

        /* Header card */
        .aurora-header {
            background: linear-gradient(135deg, rgba(56, 160, 217, 0.18), rgba(45, 212, 191, 0.12));
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border-radius: 22px;
            padding: 24px 28px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 18px;
        }
        .aqua-avatar {
            font-size: 2.6rem;
            width: 76px;
            height: 76px;
            min-width: 76px;
            border-radius: 50%;
            background: #04111c;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 3px solid #6ec6ff;
            box-shadow: 0 0 0 4px rgba(110, 198, 255, 0.15);
        }
        .aurora-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(90deg, #6ec6ff, #2dd4bf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }
        .aurora-sub {
            color: #a9c4dd;
            font-size: 0.92rem;
            margin-top: 4px;
        }
        .badge-row {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .badge {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #cfe6f5;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .badge.live {
            color: #2dd4bf;
            border-color: rgba(45, 212, 191, 0.4);
        }
        .badge-dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #2dd4bf;
            margin-right: 6px;
        }

        /* Chat bubbles */
        .msg-row {
            display: flex;
            margin-bottom: 14px;
        }
        .msg-row.user { justify-content: flex-end; }
        .msg-row.assistant { justify-content: flex-start; }

        .msg {
            max-width: 72%;
            padding: 14px 18px;
            border-radius: 18px;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .msg.user {
            background: linear-gradient(135deg, #2d8fd0, #1c6aa8);
            color: #ffffff;
            border-bottom-right-radius: 4px;
        }
        .msg.assistant {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.09);
            color: #dff1fb;
            border-bottom-left-radius: 4px;
        }
        .msg-label {
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 5px;
            opacity: 0.55;
        }

        /* Sources card under an assistant reply */
        .sources-box {
            max-width: 72%;
            margin: -6px 0 14px 0;
            padding: 10px 16px;
            border-radius: 14px;
            background: rgba(45, 212, 191, 0.06);
            border: 1px dashed rgba(45, 212, 191, 0.35);
            font-size: 0.8rem;
            color: #b6e8e0;
        }
        .sources-box a { color: #2dd4bf; text-decoration: none; }
        .sources-box a:hover { text-decoration: underline; }

        /* Weather card under a reply */
        .weather-card {
            max-width: 72%;
            margin: -6px 0 14px 0;
            padding: 16px 20px;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(56, 160, 217, 0.14), rgba(45, 212, 191, 0.10));
            border: 1px solid rgba(110, 198, 255, 0.35);
            color: #eaf6ff;
        }
        .weather-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .weather-city {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
        }
        .weather-temp {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            color: #6ec6ff;
        }
        .weather-desc {
            font-size: 0.85rem;
            color: #bcdcf2;
            text-transform: capitalize;
            margin-top: 2px;
        }
        .weather-meta {
            display: flex;
            gap: 16px;
            margin-top: 10px;
            font-size: 0.78rem;
            color: #a9c4dd;
        }
        .weather-links {
            margin-top: 10px;
            font-size: 0.78rem;
        }
        .weather-links a { color: #2dd4bf; text-decoration: none; margin-right: 12px; }
        .weather-links a:hover { text-decoration: underline; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #081a2a;
            border-right: 1px solid rgba(255,255,255,0.06);
        }
        section[data-testid="stSidebar"] * { color: #cfe6f5; }
        section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
            font-family: 'Space Grotesk', sans-serif;
            color: #ffffff;
            font-weight: 700;
        }

        .stButton>button {
            border-radius: 14px;
            border: none;
            background: linear-gradient(135deg, #2d8fd0, #1c6aa8);
            color: #ffffff;
            font-weight: 700;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #2dd4bf, #22a596);
            color: #04111c;
        }

        .stSelectbox>div>div, .stTextInput>div>div>input {
            border-radius: 12px !important;
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: #dff1fb !important;
        }

        [data-testid="stChatInput"] {
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.14) !important;
            background: rgba(255,255,255,0.04);
        }

        .stSlider [data-baseweb="slider"] > div > div {
            background: #2dd4bf !important;
        }

        .stCheckbox label p { color: #cfe6f5 !important; }

        .empty-card {
            text-align: center;
            padding: 55px 20px;
            border-radius: 22px;
            background: rgba(255,255,255,0.04);
            border: 1px dashed rgba(255,255,255,0.15);
            color: #a9c4dd;
        }
        .empty-card h3 {
            color: #ffffff;
            font-family: 'Space Grotesk', sans-serif;
        }

        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Internal model registry.
# Left = friendly label shown in UI, Right = real Hugging Face
# model id actually sent to the API.
# ---------------------------------------------------------
MODEL_OPTIONS = {
    "Aqua Flash (Fastest)": "meta-llama/Llama-3.3-70B-Instruct:fastest",
    "Aqua Coder": "Qwen/Qwen2.5-Coder-32B-Instruct:fastest",
    "Aqua Balanced": "Qwen/Qwen2.5-7B-Instruct-1M:fastest",
    "Aqua Pro (Most Capable)": "deepseek-ai/DeepSeek-R1:fastest",
}


@st.cache_resource(show_spinner=False)
def get_client(model_id: str, token: str):
    return InferenceClient(model=model_id, token=token)


def stream_response(client, model_id, history, temperature):
    stream = client.chat_completion(
        model=model_id,
        messages=history,
        temperature=temperature,
        max_tokens=1024,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# ---------------------------------------------------------
# DuckDuckGo web search helper
# ---------------------------------------------------------
def search_duckduckgo(query: str, max_results: int = 5):
    """
    Runs a DuckDuckGo search and returns a simple list of dicts:
    [{"title": ..., "body": ..., "href": ...}, ...]
    Returns an empty list if something goes wrong (no internet, etc).
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception:
        return []


def build_search_context(results):
    """
    Turns raw search results into a short text block we can hand
    to the model as extra context.
    """
    if not results:
        return ""
    lines = ["Here are some fresh web search results. Use them to answer accurately, "
             "and mention that the info comes from a web search when relevant:\n"]
    for i, r in enumerate(results, start=1):
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        lines.append(f"{i}. {title}\n   {body}\n   Source: {href}")
    return "\n".join(lines)


# ---------------------------------------------------------
# Weather tool - uses the free OpenWeatherMap API
# (https://openweathermap.org/api). Needs an API key, see .env
# ---------------------------------------------------------
# Keywords across several languages so the weather tool triggers
# no matter what language the person is typing in.
WEATHER_KEYWORDS = [
    # English
    "weather", "temperature", "temp", "forecast", "rain", "sunny",
    "humidity", "climate", "hot", "cold", "wind speed",
    # Roman Urdu / Hindi
    "mausam", "mosam", "barish", "garmi", "sardi", "hawa",
    # Urdu / Hindi script
    "موسم", "بارش", "گرمی", "سردی", "मौसम", "बारिश", "तापमान",
    # Bengali
    "আবহাওয়া", "তাপমাত্রা",
    # Arabic
    "الطقس", "درجة الحرارة",
    # Spanish / French / Portuguese / German / Turkish / Indonesian
    "clima", "tiempo", "météo", "meteo", "temps", "wetter",
    "hava durumu", "cuaca", "temperatura",
    # Chinese / Russian
    "天气", "погода",
]


def looks_like_weather_query(text: str) -> bool:
    text_lower = text.lower()
    return any(word in text_lower for word in WEATHER_KEYWORDS)


def extract_city(text: str, default_city: str) -> str:
    """
    Tries to pull a city name out of the message in several common
    phrasings (English + roman Urdu/Hindi), e.g.:
      "weather in Lahore", "Karachi ka mausam", "mausam of Multan"
    Falls back to the default city set in the sidebar if nothing found.
    """
    patterns = [
        r"\bin\s+([A-Za-z\s]{2,30})",
        r"\bfor\s+([A-Za-z\s]{2,30})",
        r"\bof\s+([A-Za-z\s]{2,30})",
        r"([A-Za-z\s]{2,30})\s+ka\s+mausam",
        r"([A-Za-z\s]{2,30})\s+ki\s+mausam",
        r"([A-Za-z\s]{2,30})\s+mein\s+mausam",
        r"([A-Za-z\s]{2,30})\s+weather",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            city = match.group(1).strip(" ?.!,")
            # Skip junk matches like "the", "today", etc.
            if city and city.lower() not in {"the", "today", "now", "here", "this"}:
                return city
    return default_city


def get_weather(city: str, api_key: str):
    """
    Calls OpenWeatherMap and returns a simple dict with the fields we
    need, or None if the lookup failed (bad city, bad key, no internet).
    """
    if not city or not api_key:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if str(data.get("cod")) != "200":
            return None
        return {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "temp": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind": data.get("wind", {}).get("speed"),
            "description": data.get("weather", [{}])[0].get("description", ""),
        }
    except Exception:
        return None


def build_weather_context(weather):
    """Turns weather data into text the model can use to answer."""
    if not weather:
        return ""
    return (
        f"LIVE WEATHER DATA (already fetched from OpenWeatherMap, right now) "
        f"for {weather['city']}, {weather['country']}: "
        f"temperature {weather['temp']}°C, feels like {weather['feels_like']}°C, "
        f"condition: {weather['description']}, humidity {weather['humidity']}%, "
        f"wind speed {weather['wind']} m/s.\n"
        "IMPORTANT: State these exact numbers directly in your answer. "
        "Do NOT say you lack real-time access, and do NOT tell the user to check "
        "external websites like AccuWeather or Weather.com for this — the data above "
        "IS the current real-time answer. Reply in the same language the user wrote in."
    )


# ---------------------------------------------------------
# API key comes only from environment - never shown in the UI.
# ---------------------------------------------------------
hf_token = os.getenv("HF_TOKEN", "")
weather_api_key = os.getenv("WEATHER_API_KEY", "")

# ---------------------------------------------------------
# Sidebar - Settings
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## Settings")

    model_label = st.selectbox(
        "Model",
        options=list(MODEL_OPTIONS.keys()),
        index=0,
        help="Aqua Flash is the fastest and most efficient option for everyday chatting.",
    )
    model_id = MODEL_OPTIONS[model_label]

    temperature = st.slider(
        "Creativity (Temperature)",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.1,
    )

    st.markdown("---")
    st.markdown("### 🔎 Web Search")

    web_search_enabled = st.checkbox(
        "Enable DuckDuckGo Search",
        value=False,
        help="When on, Aqua searches DuckDuckGo for your question before answering.",
    )

    search_result_count = st.slider(
        "Results to fetch",
        min_value=2,
        max_value=8,
        value=4,
        disabled=not web_search_enabled,
    )

    st.markdown("---")
    st.markdown("### 🌦️ Weather")

    weather_enabled = st.checkbox(
        "Enable Weather Lookup",
        value=True,
        help="When on, Aqua fetches live weather from OpenWeatherMap when you ask about weather.",
    )

    default_city = st.text_input(
        "Default city",
        value="Vehari",
        disabled=not weather_enabled,
        help="Used when you don't name a city in your message (e.g. just 'weather?').",
    )

    if weather_enabled and not weather_api_key:
        st.caption("⚠️ WEATHER_API_KEY missing — add it to .env to enable this.")

    st.markdown("---")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("Built with Hugging Face + Streamlit + DuckDuckGo + OpenWeatherMap")

# ---------------------------------------------------------
# Session State - Chat History
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
# Keeps the last search results used, per assistant message index,
# so we can show a small "Sources" box under that reply.
if "sources_by_index" not in st.session_state:
    st.session_state.sources_by_index = {}
# Keeps the weather card data used for a given assistant message index.
if "weather_by_index" not in st.session_state:
    st.session_state.weather_by_index = {}

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
search_badge = (
    '<span class="badge live"><span class="badge-dot"></span>Web Search ON</span>'
    if web_search_enabled
    else '<span class="badge">Web Search OFF</span>'
)
weather_badge = (
    '<span class="badge live"><span class="badge-dot"></span>Weather ON</span>'
    if weather_enabled and weather_api_key
    else '<span class="badge">Weather OFF</span>'
)

st.markdown(
    f"""
    <div class="aurora-header">
        <div class="aqua-avatar">🐬</div>
        <div>
            <p class="aurora-title">✨ Aqua AI Chatbot</p>
            <p class="aurora-sub">Your assistant — now with real-time web search & weather</p>
            <div class="badge-row">
                <span class="badge">{model_label}</span>
                <span class="badge">Temp {temperature}</span>
                {search_badge}
                {weather_badge}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Render existing chat history as custom bubbles
# ---------------------------------------------------------
for idx, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    label = "You" if role == "user" else "Aqua"
    st.markdown(
        f"""
        <div class="msg-row {role}">
            <div class="msg {role}">
                <div class="msg-label">{label}</div>
                {msg["content"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show sources box right under the assistant reply that used search
    if role == "assistant" and idx in st.session_state.sources_by_index:
        srcs = st.session_state.sources_by_index[idx]
        if srcs:
            links_html = "<br>".join(
                f'🔗 <a href="{s.get("href", "#")}" target="_blank">{s.get("title", s.get("href", ""))}</a>'
                for s in srcs
            )
            st.markdown(
                f'<div class="sources-box"><b>Sources:</b><br>{links_html}</div>',
                unsafe_allow_html=True,
            )

    # Show a weather card right under the assistant reply that used it
    if role == "assistant" and idx in st.session_state.weather_by_index:
        w = st.session_state.weather_by_index[idx]
        if w:
            st.markdown(
                f"""
                <div class="weather-card">
                    <div class="weather-top">
                        <div>
                            <div class="weather-city">📍 {w['city']}, {w['country']}</div>
                            <div class="weather-desc">{w['description']}</div>
                        </div>
                        <div class="weather-temp">{w['temp']}°C</div>
                    </div>
                    <div class="weather-meta">
                        <span>Feels like {w['feels_like']}°C</span>
                        <span>💧 {w['humidity']}%</span>
                        <span>💨 {w['wind']} m/s</span>
                    </div>
                    <div class="weather-links">
                        More on:
                        <a href="https://www.accuweather.com/en/search-locations?query={w['city']}" target="_blank">AccuWeather</a>
                        <a href="https://weather.com/weather/today/l/{w['city']}" target="_blank">Weather.com</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------
# Empty state
# ---------------------------------------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-card">
            <h3>🐬 Say hello!</h3>
            <p>Type your message below to start chatting with Aqua.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Chat Input
# ---------------------------------------------------------
user_prompt = st.chat_input("Type your message here...")

if user_prompt:
    if not hf_token:
        st.error("HF_TOKEN not found. Add it to your .env file (or platform secrets) and restart the app.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Base system prompt
    system_content = (
        "You are Aqua, a friendly AI assistant. Always reply in the same "
        "language the user writes in."
    )

    # If web search is on, search DuckDuckGo for the user's question
    # and fold the results into the system message as extra context.
    search_results = []
    if web_search_enabled:
        with st.spinner("Searching the web..."):
            search_results = search_duckduckgo(user_prompt, max_results=search_result_count)
        search_context = build_search_context(search_results)
        if search_context:
            system_content += "\n\n" + search_context

    # If weather lookup is on and the message looks weather-related,
    # fetch live weather and fold it into the system message too.
    weather_data = None
    if weather_enabled and weather_api_key and looks_like_weather_query(user_prompt):
        city = extract_city(user_prompt, default_city)
        with st.spinner(f"Checking weather for {city}..."):
            weather_data = get_weather(city, weather_api_key)
        weather_context = build_weather_context(weather_data)
        if weather_context:
            system_content += "\n\n" + weather_context

    # Build chat history in the plain dict format Hugging Face chat models expect
    history = [{"role": "system", "content": system_content}]
    for msg in st.session_state.messages:
        history.append({"role": msg["role"], "content": msg["content"]})

    # Show the response live, chunk by chunk, instead of waiting for the
    # whole thing to finish generating before anything appears.
    live_placeholder = st.empty()
    response_text = ""
    try:
        client = get_client(model_id, hf_token)
        for chunk in stream_response(client, model_id, history, temperature):
            response_text += chunk
            live_placeholder.markdown(
                f"""
                <div class="msg-row assistant">
                    <div class="msg assistant">
                        <div class="msg-label">Aqua</div>
                        {response_text}▌
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception as e:
        response_text = f"Error: {e}"
    live_placeholder.empty()

    st.session_state.messages.append({"role": "assistant", "content": response_text})

    # Remember which sources were used for this new assistant message,
    # so it shows up when the chat re-renders.
    new_assistant_idx = len(st.session_state.messages) - 1
    if web_search_enabled and search_results:
        st.session_state.sources_by_index[new_assistant_idx] = search_results
    if weather_data:
        st.session_state.weather_by_index[new_assistant_idx] = weather_data

    st.rerun()
    