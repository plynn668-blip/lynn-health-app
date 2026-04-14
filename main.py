import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import os

# --- 1. 基础配置与文件路径 ---
st.set_page_config(page_title="Lynn's Care", layout="centered")

CHECKIN_FILE = "lynn_checkin.csv"
HEALTH_FILE = "lynn_health.csv"
PLAN_FILE = "lynn_plan.txt"

# 初始化数据文件
if not os.path.exists(PLAN_FILE):
    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        f.write("1. 每日饮水 2000ml\n2. 晚上 11 点前入睡\n3. 每日 15 分钟颈部拉伸")

def load_checkin():
    if os.path.exists(CHECKIN_FILE):
        return pd.read_csv(CHECKIN_FILE)
    return pd.DataFrame(columns=['date', 'rate'])

def load_health():
    if os.path.exists(HEALTH_FILE):
        return pd.read_csv(HEALTH_FILE)
    return pd.DataFrame(columns=['日期', '维度', '程度', '备注'])

# --- 2. 侧边栏导航 ---
st.sidebar.title("☀️ 你好, Lynn")
page = st.sidebar.radio("前往页面", ["今日打卡 & 日历", "健康状态看板"])

# ==========================================
# 页面一：今日打卡 & 日历
# ==========================================
if page == "今日打卡 & 日历":
    st.header("🏃‍♀️ Lynn 的个人主页")

    # 1. 计划修改区 (增加确认按钮)
    with open(PLAN_FILE, "r", encoding="utf-8") as f:
        current_plan = f.read()

    with st.expander("📝 修改我的健康计划"):
        temp_plan = st.text_area("在下方编辑你的计划：", value=current_plan, height=120)
        if st.button("确认修改计划"):
            with open(PLAN_FILE, "w", encoding="utf-8") as f:
                f.write(temp_plan)
            st.success("计划已更新！")
            st.rerun()

    # 2. 今日打卡区
    today_str = datetime.now().strftime("%Y-%m-%d")
    st.subheader(f"✅ 今日打卡 - {today_str}")
    
    tasks = [t for t in current_plan.split('\n') if t.strip()]
    checks = []
    for i, t in enumerate(tasks):
        checks.append(st.checkbox(t, key=f"t_{i}"))
    
    if st.button("确认今日打卡", use_container_width=True):
        rate = sum(checks) / len(tasks) if tasks else 0
        df_c = load_checkin()
        # 更新或新增
        new_entry = pd.DataFrame([{"date": today_str, "rate": rate}])
        df_c = pd.concat([df_c[df_c['date'] != today_str], new_entry])
        df_c.to_csv(CHECKIN_FILE, index=False)
        st.balloons()
        st.success("打卡成功，日历已更新！")
        st.rerun()

    # 3. 极简日历展示 (修复样式错误)
    st.divider()
    today = datetime.now()
    st.subheader(f"🗓 {today.year}年{today.month}月 打卡表")
    
    df_c = load_checkin()
    checkin_dict = dict(zip(df_c['date'], df_c['rate']))
    
    # 构建纯 HTML 日历
    cal = calendar.monthcalendar(today.year, today.month)
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    
    # HTML 样式
    html_content = """
    <style>
        .cal-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; text-align: center; }
        .cal-header { font-weight: bold; padding: 5px 0; font-size: 0.8em; color: #888; }
        .cal-day { border-radius: 8px; padding: 10px 0; font-weight: bold; font-size: 0.9em; border: 1px solid #eee; }
    </style>
    <div class="cal-container">
    """

    # 添加表头
    for wd in weekdays:
        html_content += f'<div class="cal-header">{wd}</div>'
    
    # 添加日期格子
    for week in cal:
        for day in week:
            if day == 0:
                html_content += '<div></div>'
            else:
                date_s = f"{today.year}-{today.month:02d}-{day:02d}"
                bg_color = "#ffffff"
                text_color = "#333"
                border_color = "#eee"
                
                if date_s in checkin_dict:
                    r = checkin_dict[date_s]
                    if r >= 1.0: bg_color = "#52c41a"; text_color = "white"
                    elif r > 0: bg_color = "#fadb14"; text_color = "black"
                
                if date_s == today_str:
                    border_color = "#1890ff"
                
                html_content += f'<div class="cal-day" style="background-color:{bg_color}; color:{text_color}; border: 2px solid {border_color};">{day}</div>'
    
    html_content += "</div>"
    st.markdown(html_content, unsafe_allow_html=True)
    
    st.caption("🟢 全勤 | 🟡 部分完成 | ⚪️ 未记录 | 🔵 蓝色边框为今日")

# ==========================================
# 页面二：健康看板
# ==========================================
else:
    st.header("📊 健康记录看板")
    
    with st.expander("➕ 添加新记录 (身体/心理/精神)"):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("日期", datetime.now())
        with col2:
            cat = st.selectbox("维度", ["身体状况", "心理状况", "精神状况"])
        score = st.slider("舒适度 (1难受 - 10舒服)", 1, 10, 5)
        note = st.text_area("详细记录/备注")
        if st.button("保存记录", use_container_width=True):
            df_h = load_health()
            new_h = pd.DataFrame([{"日期": d.strftime("%Y-%m-%d"), "维度": cat, "程度": score, "备注": note}])
            pd.concat([df_h, new_h]).to_csv(HEALTH_FILE, index=False)
            st.toast("记录已保存！")
            st.rerun()

    st.divider()
    
    df_h = load_health()
    if not df_h.empty:
        mode = st.radio("查询方式", ["按日期看", "按维度看"], horizontal=True)
        if mode == "按日期看":
            sel_d = st.date_input("选择日期", datetime.now()).strftime("%Y-%m-%d")
            st.dataframe(df_h[df_h['日期'] == sel_d], use_container_width=True)
        else:
            sel_c = st.selectbox("选择维度", ["身体状况", "心理状况", "精神状况"])
            st.dataframe(df_h[df_h['维度'] == sel_c].sort_values("日期", ascending=False), use_container_width=True)
    else:
        st.info("还没有记录，点上方加号开始记录吧！")