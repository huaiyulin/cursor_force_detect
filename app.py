import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_processor import process_force_data, generate_pdf_report

def main():
    st.title("測力板數據分析系統")
    
    # 文件上傳
    uploaded_file = st.file_uploader("請上傳CSV文件", type=['csv'])
    
    if uploaded_file is not None:
        # 讀取數據
        df = pd.read_csv(uploaded_file)
        
        # 顯示原始數據預覽
        st.subheader("數據預覽")
        st.dataframe(df.head())
        
        # 選擇欄位
        columns = df.columns.tolist()
        col1, col2 = st.columns(2)
        
        with col1:
            # 找出可能的時間欄位（包含 'time' 的欄位名）
            default_time_idx = 0
            for keyword in ['时间', '時間', 'time']:
                for idx, col in enumerate(columns):
                    if keyword in col.lower():
                        default_time_idx = idx
                        break
                if default_time_idx != 0:
                    break
                    
            time_column = st.selectbox(
                "請選擇時間欄位",
                options=columns,
                index=default_time_idx
            )
        
        with col2:
            # 找出可能的力量欄位（包含 'force' 的欄位名）
            default_force_idx = 0
            for keyword in ['sumforce', 'force']:
                for idx, col in enumerate(columns):
                    if keyword in col.lower():
                        default_force_idx = idx
                        break
                if default_force_idx != 0:
                    break
                    
            force_column = st.selectbox(
                "請選擇力量欄位",
                options=columns,
                index=default_force_idx
            )
        
        # 重命名選擇的欄位
        df = df.rename(columns={
            time_column: 'time',
            force_column: 'force'
        })
        
        # 處理數據
        df, points = process_force_data(df)
        
        # 創建力量-時間圖
        fig = go.Figure()
        
        # 添加主要曲線
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['force'],
            mode='lines',
            name='力量曲線'
        ))
        
        # 設置不同點的文字位置和對齊方式
        text_positions = {
            'A': 'top center',      # A點文字在上方靠左
            'B': 'middle right',  # B點文字在右側中間
            'C': 'bottom right'   # C點文字在右下方
        }
        
        # 添加關鍵點
        for point_name, point_data in points.items():
            # 只處理 A、B、C 點
            if point_name in ['A', 'B', 'C']:
                text_content = f'{point_name}點<br>時間: {point_data["time"]:.2f}s<br>力量: {point_data["force"]:.2f}N'
                fig.add_trace(go.Scatter(
                    x=[point_data['time']],
                    y=[point_data['force']],
                    mode='markers+text',
                    name=f'點位 {point_name}',
                    text=[text_content],
                    textposition=text_positions[point_name],
                    marker=dict(size=10),
                    textfont=dict(size=12),  # 調整文字大小
                ))
        
        # 設置圖表樣式
        fig.update_layout(
            title='力量-時間關係圖',
            xaxis_title='時間 (秒)',
            yaxis_title='力量 (N)',
            hovermode='x unified',
            # 增加圖表邊距以確保文字不會被切掉
            margin=dict(l=50, r=100, t=50, b=50)  # 增加右側邊距
        )
        
        # 顯示圖表
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示數據統計
        st.subheader("數據統計")
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        stats_col4, stats_col5 = st.columns(2)  # 新增兩列用於顯示新的統計指標
        
        with stats_col1:
            st.metric("最小力量", f"{points['A']['force']:.2f} N")
        with stats_col2:
            st.metric("最大力量", f"{points['B']['force']:.2f} N")
        with stats_col3:
            st.metric("平衡力量", f"{points['C']['force']:.2f} N")
        with stats_col4:
            st.metric("發力率 (RFD)", f"{points['stats']['RFD']:.2f} N/s")
        with stats_col5:
            st.metric("恢復時間", f"{points['stats']['recovery_time']:.2f} s")
        
        # 生成並直接下載PDF報告
        pdf_file = generate_pdf_report(df, points, fig)
        with open(pdf_file, "rb") as f:
            pdf_bytes = f.read()
        
        st.download_button(
            label="下載PDF報告",
            data=pdf_bytes,
            file_name="force_analysis_report.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main() 