import streamlit as st
import pandas as pd
import os

# 页面基础设置
st.set_page_config(page_title="知乎数据分析看板", layout="wide")

st.title("📊 知乎内容数据看板")

# 1. 读取数据
CSV_FILE = 'zhihu_data.csv'

if os.path.exists(CSV_FILE):
    # 读取 CSV 文件
    # 使用 utf-8-sig 是为了兼容 Excel 生成的带 BOM 的文件
    df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')

    # 数据预处理
    df['点赞数'] = pd.to_numeric(df['点赞数'], errors='coerce').fillna(0).astype(int)
    df['评论数'] = pd.to_numeric(df['评论数'], errors='coerce').fillna(0).astype(int)
    # 转换时间格式，方便后续按时间排序或筛选
    df['发布时间'] = pd.to_datetime(df['发布时间'], errors='coerce')

    # 2. 侧边栏筛选器
    st.sidebar.header("🔍 筛选与搜索")
    
    # 关键字搜索
    keyword = st.sidebar.text_input("搜索标题关键字")
    
    # 点赞数区间筛选
    min_votes = int(df['点赞数'].min())
    max_votes = int(df['点赞数'].max())
    vote_range = st.sidebar.slider("最小点赞数", min_votes, max_votes, min_votes)

    # 应用筛选
    filtered_df = df[df['点赞数'] >= vote_range]
    if keyword:
        filtered_df = filtered_df[filtered_df['标题'].str.contains(keyword, na=False)]

    # 3. 核心指标统计 (Metric)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("抓取总条数", len(df))
    m2.metric("当前筛选条数", len(filtered_df))
    m3.metric("最高点赞", f"{filtered_df['点赞数'].max()}")
    m4.metric("平均评论", f"{filtered_df['评论数'].mean():.1f}")

    # 4. 数据表格展示 (支持链接跳转)
    st.subheader("📋 数据明细")
    
    # 为了让链接可点击，我们可以对 DataFrame 进行转换
    display_df = filtered_df.copy()
    # 将 NaN 链接处理为空字符串
    display_df['链接'] = display_df['链接'].fillna('')
    
    # 使用 Streamlit 的 column_config 功能让链接变成可点击状态
    st.data_editor(
        display_df,
        column_config={
            "链接": st.column_config.LinkColumn("原文链接", display_text="点击跳转"),
            "发布时间": st.column_config.DatetimeColumn("发布时间", format="YYYY-MM-DD HH:mm"),
            "点赞数": st.column_config.NumberColumn("👍 点赞", format="%d"),
            "评论数": st.column_config.NumberColumn("💬 评论", format="%d"),
        },
        hide_index=True,
        use_container_width=True
    )

    # 5. 图表分析
    st.subheader("📈 数据分布图")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("点赞数 Top 10 帖子")
        top_10 = filtered_df.nlargest(10, '点赞数')
        st.bar_chart(top_10, x="标题", y="点赞数")

    with chart_col2:
        st.write("点赞与评论的相关性")
        # 散点图
        st.scatter_chart(filtered_df, x="点赞数", y="评论数")

else:
    st.warning(f"未找到文件 {CSV_FILE}，请确保脚本已成功生成该文件。")
    st.info("提示：您可以先运行 Playwright 脚本来生成数据。")

# 6. 页脚小功能：点击刷新
if st.button("刷新数据"):
    st.rerun()