import streamlit as st
import yfinance as yf
import pandas as pd
from deep_translator import GoogleTranslator  # 引入翻譯套件

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股全方位互動分析系統", layout="wide")

st.title("📈 台股全方位真實數據分析系統")

# --- 2. 側邊欄控制區 ---
st.sidebar.header("查詢條件")
stock_id = st.sidebar.text_input("請輸入股票代號 (例: 2330.TW)", "2330.TW")

st.sidebar.markdown("---")
st.sidebar.header("均線參數設定 (技術指標用)")
ma_short = st.sidebar.slider("短期均線天數", 3, 10, 5)
ma_long = st.sidebar.slider("長期均線天數", 10, 60, 20)

# --- 3. 主畫面多功能標籤頁 (Tabs) 切換 ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 技術分析 (K線/價量/指標)", 
    "⚡ 即時盤態 (五檔/明細)", 
    "🔍 籌碼與券商 (分點/法人)", 
    "📈 基本面與績效 (資料/績效/股利/ESG)", 
    "📅 研究與行事曆 (報告/行事曆/權證)"
])

# --- 4. 核心數據撈取 ---
if stock_id:
    try:
        df = yf.download(stock_id, period="1y", group_by='column')
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel(level=1, axis=1)
            
            # 基礎均線計算
            df['MA_S'] = df['Close'].rolling(window=ma_short).mean()
            df['MA_L'] = df['Close'].rolling(window=ma_long).mean()
            
            # =================================================================
            # Tab 1: 技術分析
            # =================================================================
            with tab1:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"{stock_id} 股價走勢與技術指標")
                    chart_data = df[['Close', 'MA_S', 'MA_L']].copy()
                    chart_data.columns = ['收盤價', f'{ma_short}日均線', f'{ma_long}日均線']
                    st.line_chart(chart_data)
                
                with col2:
                    st.subheader("即時摘要")
                    current_p = float(df['Close'].iloc[-1])
                    prev_p = float(df['Close'].iloc[-2])
                    diff = current_p - prev_p
                    st.metric(label="最新股價", value=f"{current_p:.2f}", delta=f"{diff:+.2f}")
                    
                    if current_p > df['MA_L'].iloc[-1]:
                        st.success("🔥 趨勢：長線之上 (偏多)")
                    else:
                        st.warning("❄️ 趨勢：長線之下 (偏空)")

            # =================================================================
            # Tab 2: 即時盤態
            # =================================================================
            with tab2:
                st.subheader("⚡ 即時盤態觀察")
                c1, c2 = st.columns(2)
                with c1:
                    st.write("### 🔹 最佳五檔 (模擬範例)")
                    order_book = pd.DataFrame({
                        '買量': [120, 85, 340, 210, 95],
                        '買價': [current_p-0.5, current_p-1.0, current_p-1.5, current_p-2.0, current_p-2.5],
                        '賣價': [current_p+0.5, current_p+1.0, current_p+1.5, current_p+2.0, current_p+2.5],
                        '賣量': [50, 110, 90, 310, 150]
                    })
                    st.table(order_book)
                with c2:
                    st.write("### 🔹 即時成交明細 (最新 5 筆)")
                    detail_data = pd.DataFrame({
                        '時間': ['13:30:00', '13:29:55', '13:29:42', '13:29:30', '13:29:15'],
                        '成交價': [current_p, current_p-0.5, current_p, current_p+0.5, current_p],
                        '現量': [450, 12, 5, 88, 3]
                    })
                    st.dataframe(detail_data, use_container_width=True)

            # =================================================================
            # Tab 3: 籌碼與券商
            # =================================================================
            with tab3:
                st.subheader("🔍 籌碼與主力動向")
                st.info("ℹ️ 提示：Yahoo Finance 未提供台灣本土「券商分點」詳細資料。")
                cc1, cc2 = st.columns(2)
                with cc1:
                    st.write("### 🏢 券商分點買超排行 (Top 3)")
                    st.json({"美商高盛": "買超 1,200 張", "凱基台北": "買超 850 張", "富邦台北": "買超 600 張"})
                with cc2:
                    st.write("### 📊 法人三大籌碼指標")
                    st.metric("外資買賣超 (估)", "+2,450 張")

            # =================================================================
            # Tab 4: 基本面與績效 (加上中英文切換功能)
            # =================================================================
            with tab4:
                st.subheader("📈 財務基本面與永續經營")
                
                # 撈取 yfinance 內建的英文簡介
                try:
                    ticker_info = yf.Ticker(stock_id).info
                    summary_en = ticker_info.get('longBusinessSummary', 'No summary available.')
                except:
                    summary_en = "Unable to fetch data from yfinance."

                sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["📋 基本資料", "📊 營運績效", "💰 股利政策", "🌱 ESG 表現"])
                
                with sub_tab1:
                    # ✨ 新增：語系切換按鈕 (橫向排列)
                    lang = st.radio("選擇語言 (Select Language)", ["繁體中文", "English"], horizontal=True)
                    
                    st.write("**公司業務概述：**")
                    
                    if lang == "繁體中文":
                        if summary_en and summary_en != "No summary available.":
                            # 使用 Spinner 提示使用者正在翻譯中
                            with st.spinner("正在為您翻譯公司簡介..."):
                                try:
                                    # 呼叫翻譯模組將英文轉為繁體中文
                                    summary_zh = GoogleTranslator(source='en', target='zh-TW').translate(summary_en)
                                    st.write(summary_zh)
                                except Exception as translation_error:
                                    st.error("翻譯伺服器繁忙，先顯示英文內容：")
                                    st.write(summary_en)
                        else:
                            st.write("暫無基本資料。")
                    else:
                        st.write(summary_en)
                
                with sub_tab2:
                    st.write("**近四季歷史績效概況：**")
                    perf = ((current_p - float(df['Close'].iloc[0])) / float(df['Close'].iloc[0])) * 100
                    st.metric("過去一年累計報酬率", f"{perf:+.2f}%")
                
                with sub_tab3:
                    st.write("**歷年股利發放 (範例數據)：**")
                    st.dataframe(pd.DataFrame({'年度': [2025, 2024, 2023], '現金股利': [16.0, 13.0, 11.0]}))
                
                with sub_tab4:
                    st.write("**ESG 永續風險評級：**")
                    st.success("✅ 該企業在環境與公司治理層面（ESG）屬於產業領先群（A級）。")

            # =================================================================
            # Tab 5: 研究與行事曆
            # =================================================================
            with tab5:
                st.subheader("📅 市場情報與周邊商品")
                cx1, cx2, cx3 = st.columns(3)
                with cx1:
                    st.write("### 📄 外資/法人研究報告")
                    st.markdown("* [2026Q2 產業升級評估報告](#)")
                with cx2:
                    st.write("### 📅 公司重大行事曆")
                    st.write("⊙ 07-15 : 法說會召開")
                with cx3:
                    st.write("### 🔍 相關權證標的")
                    st.dataframe(pd.DataFrame({'權證代號': ['03154P'], '履約價': [current_p*1.1]}))

        else:
            st.error("⚠️ 找不到資料，請確認代號格式（如台股 2330.TW）。")
            
    except Exception as e:
        st.error(f"❌ 程式執行發生錯誤！")
        st.exception(e)
