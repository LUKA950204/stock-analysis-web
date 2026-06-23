import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股自動化分析系統", layout="wide")

st.title("📈 台股真實數據互動分析系統")
st.markdown("輸入股票代號即可獲取過去一年的趨勢圖與均線分析。")

# --- 2. 側邊欄控制區 ---
st.sidebar.header("查詢條件")
stock_id = st.sidebar.text_input("請輸入股票代號 (例: 2330.TW)", "2330.TW")
ma_short = st.sidebar.slider("短期均線天數", 3, 10, 5)
ma_long = st.sidebar.slider("長期均線天數", 10, 60, 20)

# --- 3. 核心邏輯區 ---
if stock_id:
    try:
        # 修正點 1：加上 group_by='column' 並手動降維，相容新版 yfinance 的多重索引
        df = yf.download(stock_id, period="1y", group_by='column')
        
        if not df.empty:
            # 如果發現結構是多重索引，只取第一層 (例如把 ('Close', '2330.TW') 簡化為 'Close')
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel(level=1, axis=1)
            
            # 運算：計算移動平均線
            df['MA_S'] = df['Close'].rolling(window=ma_short).mean()
            df['MA_L'] = df['Close'].rolling(window=ma_long).mean()
            
            # 計算最新漲跌
            current_p = float(df['Close'].iloc[-1])
            prev_p = float(df['Close'].iloc[-2])
            diff = current_p - prev_p
            
            # --- 4. 顯示功能 ---
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"{stock_id} 股價走勢圖")
                chart_data = df[['Close', 'MA_S', 'MA_L']].copy()
                chart_data.columns = ['收盤價', f'{ma_short}日均線', f'{ma_long}日均線']
                st.line_chart(chart_data)
            
            with col2:
                st.subheader("即時數據分析")
                st.metric(label="最新股價", value=f"{current_p:.2f}", delta=f"{diff:+.2f}")
                st.write(f"數據更新日期：{df.index[-1].strftime('%Y-%m-%d')}")
                
                if current_p > df['MA_L'].iloc[-1]:
                    st.success("🔥 目前趨勢：股價位於長線之上 (偏多)")
                else:
                    st.warning("❄️ 目前趨勢：股價位於長線之下 (偏空)")
            
            st.info("💡 提示：您可以滑動左側滑桿，觀察不同天數均線的交叉情況。")

        else:
            st.error("⚠️ 找不到資料，請確認代號格式（如台股 2330.TW）。")
            
    except Exception as e:
        # 修正點 2：不要假裝在連線中，直接把真正的錯誤原因印出來！
        st.error(f"❌ 程式執行發生錯誤！")
        st.exception(e)  # 這會在畫面上展開詳細的 Error Log，一眼就能看出是哪行壞掉
