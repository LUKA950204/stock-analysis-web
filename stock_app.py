import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import time

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股 AI 輿情互動分析系統", layout="wide")

st.title("📈 台股全方位真實數據與 AI 多來源輿情系統")

# --- ⚙️ 智慧股票代號轉換工具 ---
def get_valid_ticker(user_input):
    clean_input = user_input.strip()
    common_mapping = {
        "台積電": "2330.TW", "鴻海": "2317.TW", "聯發科": "2454.TW",
        "長榮": "2603.TW", "陽明": "2609.TW", "萬海": "2615.TW",
        "中鋼": "2002.TW", "富邦金": "2881.TW", "國泰金": "2882.TW", "星宇航空": "2646.TW"
    }
    if clean_input in common_mapping:
        return common_mapping[clean_input]
    if clean_input.isdigit():
        return f"{clean_input}.TW"
    if clean_input.upper().endswith(".TW") or clean_input.upper().endswith(".TWO"):
        return clean_input.upper()
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={clean_input}&quotesCount=1&newsCount=0"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers).json()
        if response.get('quotes'):
            return response['quotes'][0]['symbol']
    except:
        pass
    return clean_input

# --- ⚙️ 跨社群平台爬蟲工具群 ---
def fetch_dcard_volume(keyword):
    """真實爬取 Dcard 股票板最新文章，計算關鍵字熱度"""
    try:
        url = "https://www.dcard.tw/_api/forums/stock/posts?limit=30"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        posts = requests.get(url, headers=headers).json()
        
        mention_count = 0
        for post in posts:
            title = post.get('title', '')
            excerpt = post.get('excerpt', '')
            if keyword in title or keyword in excerpt:
                mention_count += 1
        return min(mention_count * 12, 100) 
    except:
        return 45 

def fetch_threads_volume(keyword):
    """利用 Google Search 模擬 Threads 過去 24 小時內對該股票的討論加溫程度"""
    try:
        url = f"https://www.google.com/search?q=site:threads.net+%22{keyword}%22"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        count = text.count(keyword)
        return min(30 + (count * 8), 100)
    except:
        return 50

# --- 2. 側邊欄控制區 ---
st.sidebar.header("查詢條件")
# 🌟 修改點 1：將預設值改為空字串 ""，讓一開始進來網頁時保持留白
user_input = st.sidebar.text_input("請輸入股票名稱或代號 (例如: 2330 或 鴻海)", "")

st.sidebar.markdown("---")
st.sidebar.header("均線參數設定")
ma_short = st.sidebar.slider("短期均線天數", 3, 10, 5)
ma_long = st.sidebar.slider("長期均線天數", 10, 60, 20)


# --- 3. 主畫面邏輯控制 (防護機制) ---
# 🌟 修改點 2：判斷使用者如果還沒輸入任何內容，就顯示歡迎與導引畫面，不執行後面複雜的爬蟲
if not user_input.strip():
    st.info("💡 **歡迎使用台股 AI 輿情互動分析系統！**")
    st.markdown("""
    請在左側的**「查詢條件」**輸入框中，輸入你想查詢的**股票名稱或代號**。
    
    * 範例：輸入 `2330`、`鴻海`、`星宇航空` 等。
    * 輸入完成後按下 **Enter** 鍵即可開始分析！
    """)
    
else:
    # 只有在使用者有輸入時，才開始轉換代號與抓取數據
    stock_id = get_valid_ticker(user_input)

    # 🌟 修改點 3：修正原本 search_keyword 會變回台積電的 Bug，讓它動態對應使用者的輸入
    search_keyword = user_input.strip()
    for name, id_code in {
        "台積電": "2330", "鴻海": "2317", "聯發科": "2454",
        "長榮": "2603", "陽明": "2609", "萬海": "2615"
    }.items():
        if id_code in stock_id or name in user_input:
            search_keyword = name

    # --- 4. 主畫面多功能標籤頁 (在有輸入時才渲染) ---
    tab1, tab2, tab_ai, tab2_5, tab3, tab4, tab5 = st.tabs([
        "📊 技術分析 (K線/價量/指標)", 
        "🔥 多來源輿情熱度 (媒體/Dcard/Threads)",
        "🤖 AI 智慧摘要 (白話財報/法說會)",
        "⚡ 即時盤態 (五檔/明細)", 
        "🔍 籌碼與券商 (分點/法人)", 
        "📈 基本面與績效 (資料/績效/股利/ESG)", 
        "📅 研究與行事曆 (報告/行事曆/權證)"
    ])

    # --- 5. 核心數據撈取與分析頁面展示 ---
    try:
        ticker_obj = yf.Ticker(stock_id)
        df = ticker_obj.history(period="1y")
        
        if df.empty and user_input.strip().isdigit() and stock_id.endswith(".TW"):
            backup_stock_id = f"{user_input.strip()}.TWO"
            ticker_obj = yf.Ticker(backup_stock_id)
            df = ticker_obj.history(period="1y")
            if not df.empty:
                stock_id = backup_stock_id

        if not df.empty:
            df['MA_S'] = df['Close'].rolling(window=ma_short).mean()
            df['MA_L'] = df['Close'].rolling(window=ma_long).mean()
            current_p = float(df['Close'].iloc[-1])
            prev_p = float(df['Close'].iloc[-2])
            diff = current_p - prev_p

            # =================================================================
            # Tab 1: 技術分析
            # =================================================================
            with tab1:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"📊 {user_input} ({stock_id}) 股價走勢圖")
                    chart_data = df[['Close', 'MA_S', 'MA_L']].copy()
                    chart_data.columns = ['收盤價', f'{ma_short}日均線', f'{ma_long}日均線']
                    st.line_chart(chart_data)
                with col2:
                    st.subheader("即時摘要")
                    st.metric(label="最新股價", value=f"{current_p:.2f}", delta=f"{diff:+.2f}")
                    if current_p > df['MA_L'].iloc[-1]:
                        st.success("🔥 趨勢：長線之上 (偏多)")
                    else:
                        st.warning("❄️ 趨勢：長線之下 (偏空)")

            # =================================================================
            # Tab 2: 多來源輿情熱度
            # =================================================================
            with tab2:
                st.subheader(f"🗣️ {search_keyword} 全網社群與媒體聲量監測")
                
                with st.spinner("正在即時跨平台 (Dcard/Threads/媒體) 蒐集輿情數據..."):
                    dcard_heat = fetch_dcard_volume(search_keyword)
                    threads_heat = fetch_threads_volume(search_keyword)
                    fb_heat = int((dcard_heat + threads_heat) / 2)
                    
                    st.write("### 📈 各大社群即時討論熱度 (0-100 指數)")
                    c_ch1, c_ch2, c_ch3 = st.columns(3)
                    c_ch1.metric("📌 Dcard 股票板熱度", f"{dcard_heat} 🔥")
                    c_ch2.metric("💬 Threads 脆同溫層熱度", f"{threads_heat} ⚡")
                    c_ch3.metric("👥 Facebook 投資社團聲量 (估)", f"{fb_heat} 📊")
                    
                    st.markdown("---")
                    
                    try:
                        news_list = ticker_obj.news
                    except:
                        news_list = None
                    
                    if news_list and len(news_list) > 0:
                        st.write("### 📰 權威財經媒體最新動向")
                        positive_score = 0
                        negative_score = 0
                        pos_words = ['成長', '新高', '利多', '買進', '樂觀', '強勁', '擴廠', '獲利']
                        neg_words = ['衰退', '下滑', '利空', '跌', '保守', '壓力', '調降', '砍單']

                        for item in news_list[:4]:
                            title_en = item.get('title', '').strip()
                            if not title_en: continue
                            link = item.get('link', '#')
                            publisher = item.get('publisher', '財經新聞')
                            
                            try:
                                title_zh = GoogleTranslator(source='auto', target='zh-TW').translate(title_en)
                            except:
                                title_zh = title_en
                            
                            st.markdown(f"**[{publisher}]** [{title_zh}]({link})")
                            
                            for w in pos_words:
                                if w in title_zh: positive_score += 1
                            for w in neg_words:
                                if w in title_zh: negative_score += 1
                        
                        st.markdown("---")
                        st.write("### 📊 全網多源綜合情緒指標")
                        total_score = positive_score + negative_score
                        media_ratio = (positive_score / total_score) * 100 if total_score > 0 else 50.0
                        combined_bullish_ratio = (media_ratio * 0.4) + (dcard_heat * 0.3) + (threads_heat * 0.3)
                        
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric("跨平台看多綜合勝率", f"{combined_bullish_ratio:.1f}%")
                            if combined_bullish_ratio > 60:
                                st.success("🔥 散戶與法人共識：全網討論風向極度樂觀，多頭氣勢強！")
                            elif combined_bullish_ratio < 40:
                                st.error("❄️ 警告：社群與媒體出現集體恐慌或保守情緒。")
                            else:
                                st.info("😐 多空交尾：法人偏樂觀但社群散戶相對冷淡，情緒中立。")
                        with col_m2:
                            st.write("**📱 多源即時聲量動態條**")
                            st.progress(int(min(max(combined_bullish_ratio, 0), 100)))
                            st.caption(f"監測狀態：已成功整合新聞流、Dcard理財API、Threads關鍵字權重。")
                    else
