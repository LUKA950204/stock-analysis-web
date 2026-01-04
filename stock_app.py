import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 頁面設定 (網頁版標題)
st.set_page_config(page_title="台股自動化分析系統", layout="wide")

# 設定中文字體 (針對本機執行預防亂碼)
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

st.title("📈 台股真實數據互動分析系統")
st.markdown("輸入股票代號即可獲取過去一年的趨勢圖與均線分析。")

# --- 側邊欄控制區 (整合輸入功能) ---
st.sidebar.header("查詢條件")
stock_id = st.sidebar.text_input("請輸入股票代號 (例: 2330.TW)", "2330.TW")
ma_short = st.sidebar.slider("短期均線天數", 3, 10, 5)
ma_long = st.sidebar.slider("長期均線天數", 10, 60, 20)

# --- 核心邏輯區 (整合抓取與運算) ---
if stock_id:
    with st.spinner(f'正在從 Yahoo Finance 抓取 {stock_id} 資料...'):
        try:
            # 抓取真實數據
            df = yf.download(stock_id, period="1y")
            
            if not df.empty:
                # 運算功能：計算移動平均線
                df['MA_S'] = df['Close'].rolling(window=ma_short).mean()
                df['MA_L'] = df['Close'].rolling(window=ma_long).mean()
                
                # 計算最新漲跌 (邏輯判斷)
                current_p = float(df['Close'].iloc[-1])
                prev_p = float(df['Close'].iloc[-2])
                diff = current_p - prev_p
                
                # --- 顯示功能 (整合視覺化) ---
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"{stock_id} 股價走勢圖")
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(df.index, df['Close'], label='收盤價', color='blue', alpha=0.5)
                    ax.plot(df.index, df['MA_S'], label=f'{ma_short}日均線', color='orange')
                    ax.plot(df.index, df['MA_L'], label=f'{ma_long}日均線', color='red')
                    ax.legend()
                    ax.grid(True)
                    st.pyplot(fig)
                
                with col2:
                    st.subheader("分析結果")
                    st.metric(label="最新股價", value=f"{current_p:.2f}", delta=f"{diff:+.2f}")
                    st.write(f"數據最後更新日期：\n{df.index[-1].strftime('%Y-%m-%d')}")
                    if current_p > df['MA_L'].iloc[-1]:
                        st.success("目前趨勢：股價位於長線之上 (偏多)")
                    else:
                        st.warning("目前趨勢：股價位於長線之下 (偏空)")
                
                # 暫停/循環功能在網頁版中轉化為自動重新整理介面
                st.write("---")
                st.info("💡 提示：在左側輸入新代號即可重新查詢，不需重新啟動程式。")

            else:
                st.error("找不到資料，請確認代號格式是否正確（台股請加上 .TW）。")
        except Exception as e:
            st.error(f"執行出錯：{e}")

# 退出功能：網頁版只需關閉瀏覽器分頁即可