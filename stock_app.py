import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股自動化分析系統", layout="wide")

st.title("📈 台股真實數據互動分析系統")
st.markdown("輸入股票代號即可獲取過去一年的趨勢圖與均線分析。")

# --- 2. 側邊欄控制區 ---
st.sidebar.header("查詢條件")
# 預設台積電
stock_id = st.sidebar.text_input("請輸入股票代號 (例: 2330.TW)", "2330.TW")
ma_short = st.sidebar.slider("短期均線天數", 3, 10, 5)
ma_long = st.sidebar.slider("長期均線天數", 10, 60, 20)

# --- 3. 核心邏輯區 ---
if stock_id:
    # 這裡加入 try-except 避免一開始找不到資料噴紅字
    try:
        # 抓取真實數據
        df = yf.download(stock_id, period="1y")
        
        if not df.empty:
            # 運算：計算移動平均線
            df['MA_S'] = df['Close'].rolling(window=ma_short).mean()
            df['MA_L'] = df['Close'].rolling(window=ma_long).mean()
            
            # 計算最新漲跌
            current_p = float(df['Close'].iloc[-1])
            prev_p = float(df['Close'].iloc[-2])
            diff = current_p - prev_p
            
            # --- 4. 顯示功能 (改用 st.line_chart 解決中文亂碼問題) ---
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"{stock_id} 股價走勢圖")
                # 準備繪圖數據
                chart_data = df[['Close', 'MA_S', 'MA_L']].copy()
                # 重新命名欄位，讓圖例直接顯示中文且不亂碼
                chart_data.columns = ['收盤價', f'{ma_short}日均線', f'{ma_long}日均線']
                # 使用 Streamlit 內建圖表，這在雲端部署時不會有字體問題
                st.line_chart(chart_data)
            
            with col2:
                st.subheader("即時數據分析")
                st.metric(label="最新股價", value=f"{current_p:.2f}", delta=f"{diff:+.2f}")
                st.write(f"數據更新日期：{df.index[-1].strftime('%Y-%m-%d')}")
                
                # 多空狀態判斷
                if current_p > df['MA_L'].iloc[-1]:
                    st.success("🔥 目前趨勢：股價位於長線之上 (偏多)")
                else:
                    st.warning("❄️ 目前趨勢：股價位於長線之下 (偏空)")
            
            st.info("💡 提示：您可以滑動左側滑桿，觀察不同天數均線的交叉情況。")

        else:
            st.error("⚠️ 找不到資料，請確認代號格式（如台股 2330.TW）。")
            
    except Exception as e:
        # 捕捉 Yahoo Finance 連線時的暫時性錯誤
        st.info("系統連線中，請稍候或重新輸入代號...")
