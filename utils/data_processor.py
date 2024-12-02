import pandas as pd
import numpy as np
from fpdf import FPDF
import plotly.io as pio
import os
import streamlit as st
import plotly.graph_objects as go

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # 設定中文字體
        self.add_font('kaiu', '', os.path.join(os.path.dirname(__file__), 'kaiu.ttf'), uni=True)
        
    def header(self):
        # 設定中文字體
        self.set_font('kaiu', '', 16)
        # 標題
        self.cell(0, 10, '測力板數據分析報告', 0, 1, 'C')
        # 換行
        self.ln(10)

def find_balance_point(df, max_force_idx, window_size=30, std_threshold=1):
    """找出平衡點（C點）
    
    參數:
    df: DataFrame，包含力量數據
    max_force_idx: int，B點（最大力量）的索引
    window_size: int，計算標準差時使用的窗口大小
    std_threshold: float，標準差閾值（牛頓）
    
    返回:
    dict，包含時間和力量值
    """
    # 只考慮B點之後的數據
    df_after_max = df.iloc[max_force_idx:]
    
    # 對每個點計算其前後window_size個點的標準差
    for i in range(window_size, len(df_after_max) - window_size):
        current_idx = df_after_max.index[i]
        # 取得前後window_size個點的數據
        window_data = df.loc[current_idx - window_size : current_idx + window_size, 'force']
        # 計算標準差
        std = window_data.std()
        
        # 如果標準差小於閾值，這個點就是C點
        if std < std_threshold:
            return {
                'time': df.loc[current_idx, 'time'],
                'force': df.loc[current_idx, 'force']
            }
    
    # 如果找不到符合條件的點，返回最後一個點
    last_idx = df.index[-1]
    return {
        'time': df.loc[last_idx, 'time'],
        'force': df.loc[last_idx, 'force']
    }

def process_force_data(df):
    """處理力量數據並找出關鍵點"""
    # 檢查必要的列是否存在
    required_columns = {'time', 'force'}
    current_columns = set(df.columns)
    
    if not required_columns.issubset(current_columns):
        missing_columns = required_columns - current_columns
        # 分別檢查並顯示每個缺失的欄位
        for col in missing_columns:
            if col == 'time':
                st.warning("處理數據找不到預設的時間欄位: {'time'}，請自行選擇時間欄位")
            if col == 'force':
                st.warning("處理數據找不到預設的力量欄位: {'force'}，請自行選擇力量欄位")
        return df, None
    
    # 找出A、B、C點
    min_force_idx = df['force'].idxmin()
    point_a = {
        'time': df.loc[min_force_idx, 'time'],
        'force': df.loc[min_force_idx, 'force']
    }
    
    max_force_idx = df['force'].idxmax()
    point_b = {
        'time': df.loc[max_force_idx, 'time'],
        'force': df.loc[max_force_idx, 'force']
    }
    
    point_c = find_balance_point(df, max_force_idx)
    
    # 計算額外的統計指標
    delta_force = point_b['force'] - point_a['force']  # 力量變化
    delta_time = point_b['time'] - point_a['time']     # 時間變化
    rfd = delta_force / delta_time if delta_time != 0 else 0  # 發力率
    
    recovery_time = point_c['time'] - point_b['time']  # 恢復時間
    
    points = {
        'A': point_a,
        'B': point_b,
        'C': point_c,
        'stats': {
            'RFD': rfd,
            'recovery_time': recovery_time
        }
    }
    
    return df, points

def generate_pdf_report(df, points, fig):
    """生成PDF報告"""
    pdf = FPDF()
    pdf.add_page()
    
    # 添加標題
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Force Plate Analysis Report', 0, 1, 'C')
    pdf.ln(10)  # 添加兩行的間距
    
    # 添加數據統計（縮短標題和數值之間的距離）
    pdf.set_font('Arial', 'B', 12)  # 設置粗體
    pdf.cell(80, 10, "Minimum Force (Point A):", 0, 0)  # 固定寬度為80
    pdf.set_font('Arial', '', 12)   # 取消粗體
    pdf.cell(0, 5, f"{points['A']['force']:.2f} (N) @ {points['A']['time']:.2f} (sec)", 0, 1)
    
    pdf.set_font('Arial', 'B', 12)  # 設置粗體
    pdf.cell(80, 10, "Maximum Force (Point B):", 0, 0)  # 固定寬度為80
    pdf.set_font('Arial', '', 12)   # 取消粗體
    pdf.cell(0, 5, f"{points['B']['force']:.2f} (N) @ {points['B']['time']:.2f} (sec)", 0, 1)
    
    pdf.set_font('Arial', 'B', 12)  # 設置粗體
    pdf.cell(80, 10, "Balance Force (Point C):", 0, 0)  # 固定寬度為80
    pdf.set_font('Arial', '', 12)   # 取消粗體
    pdf.cell(0, 5, f"{points['C']['force']:.2f} (N) @ {points['C']['time']:.2f} (sec)", 0, 1)
    
    # 添加額外的統計指標
    pdf.ln(5)  # 添加一些間距
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(80, 10, "Rate of Force Development:", 0, 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 5, f"{points['stats']['RFD']:.2f} (N/s)", 0, 1)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(80, 10, "Recovery Time:", 0, 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 5, f"{points['stats']['recovery_time']:.2f} (sec)", 0, 1)
    
    # 創建新的圖表實例
    new_fig = go.Figure()
    
    # 添加主要曲線
    new_fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['force'],
        mode='lines',
        name='力量曲線',
        line=dict(color='rgb(0,100,255)', width=2)
    ))
    
    # 設置不同點的文字位置和對齊方式
    text_positions = {
        'A': 'top center',      # A點文字在上方靠左
        'B': 'middle right',    # B點文字在右側中間
        'C': 'bottom right'     # C點文字在右下方
    }
    
    # 設置不同關鍵點的顏色
    colors = {
        'A': 'rgb(255,0,0)',    # 紅色
        'B': 'rgb(0,255,0)',    # 綠色
        'C': 'rgb(255,165,0)'   # 橙色
    }
    
    # 添加關鍵點
    for point_name, point_data in points.items():
        # 只處理 A、B、C 點
        if point_name in ['A', 'B', 'C']:
            text_content = f'{point_name}點<br>時間: {point_data["time"]:.2f}s<br>力量: {point_data["force"]:.2f}N'
            new_fig.add_trace(go.Scatter(
                x=[point_data['time']],
                y=[point_data['force']],
                mode='markers+text',
                name=f'點位 {point_name}',
                text=[text_content],
                textposition=text_positions[point_name],
                marker=dict(color=colors[point_name], size=12),
                textfont=dict(size=12)
            ))
    
    # 設置圖表樣式
    new_fig.update_layout(
        title='力量-時間關係圖',
        xaxis_title='時間 (秒)',
        yaxis_title='力量 (N)',
        hovermode='x unified',
        margin=dict(l=50, r=100, t=50, b=50),  # 增加右側邊距
        width=1000,
        height=600
    )
    
    # 使用高品質設置保存圖表
    pio.write_image(
        new_fig, 
        "temp_plot.png",
        format="png",
        engine="kaleido",
        scale=2  # 提高解析度
    )
    
    # 在PDF中添加圖表
    pdf.image("temp_plot.png", x=10, y=100, w=190)
    
    # 保存PDF
    pdf.output("force_analysis_report.pdf")
    
    return "force_analysis_report.pdf" 