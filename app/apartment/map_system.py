import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def run():
    st.set_page_config(layout="wide")
    st.title("🏢 공동주택 도시가스 사용량 지도 시각화")

    @st.cache_data
    def load_data():
        apart = pd.read_csv(
            "D:/Streamlit_Project/Dashboard/data/apartment/공동주택정보등록_도로명주소_좌표포함_통계청.csv",
            encoding="cp949"
        )
        sales = pd.read_csv(
            "D:/Streamlit_Project/Dashboard/data/apartment/_파워bi용 가정용 판매량 데이터_2020~202502.csv",
            encoding="utf-8"
        )
        sales["매출년월"] = pd.to_datetime(sales["매출년월"])
        return apart, sales

    df_apart, df_sales = load_data()
    df_apart = df_apart.rename(columns={"공동주택": "아파트코드"})

    # 📅 매출년월 선택
    selected_month = st.selectbox("📅 매출년월 선택", sorted(df_sales["매출년월"].unique()))
    sales_month = (
        df_sales[df_sales["매출년월"] == selected_month]
        .groupby("공동주택명", as_index=False)["사용량_m3"]
        .sum()
    )

    # 🔗 병합 및 정제
    df = pd.merge(df_apart, sales_month, on="공동주택명", how="left")
    df = df[df["사용량_m3"] > 0].dropna(subset=["위도", "경도", "난방방식"]).copy()

    # 🔍 공동주택명 검색
    search_name = st.text_input("🔍 공동주택명 검색")
    highlight = None
    if search_name:
        match = df[df["공동주택명"].str.contains(search_name, case=False, na=False)]
        if not match.empty:
            highlight = match.iloc[0]

    st.info(f"🧭 지도에 표시된 공동주택 수: {len(df):,} 개")

    # 난방방식 ➝ 마커 심볼 매핑
    symbol_map = {
        "개별난방": "circle",
        "열병합(Co-gen)": "square",
        "중앙난방(가스)": "diamond",
        "중앙난방(기름)": "cross",
        "지역난방": "star",
        "CES(집단에너지)": "triangle-up",
        "신서(집단에너지)": "x",
        "기타": "triangle-down"
    }
    df["symbol"] = df["난방방식"].map(symbol_map).fillna("circle")

    # 강조 색상 처리
    df["marker_color"] = df["사용량_m3"]
    if highlight is not None:
        df.loc[df["공동주택명"] == highlight["공동주택명"], "marker_color"] = df["사용량_m3"].max() + 1_000_000
        center_lat = highlight["위도"]
        center_lon = highlight["경도"]
    else:
        center_lat = df["위도"].mean()
        center_lon = df["경도"].mean()

    # 시각화 시작
    fig = go.Figure()

    for heating_type, group in df.groupby("symbol"):
        fig.add_trace(go.Scattermapbox(
            lat=group["위도"],
            lon=group["경도"],
            mode="markers",
            marker=dict(
                size=12,
                color=group["marker_color"],
                colorscale="Plasma",
                cmin=df["사용량_m3"].min(),
                cmax=df["사용량_m3"].max(),
                showscale=False,
                symbol=heating_type
            ),
            customdata=group[["공동주택명", "세대수", "사용량_m3", "주소", "난방방식"]],
            hovertemplate="""
                <b>%{customdata[0]}</b><br><br>
                🏠 세대수: %{customdata[1]:,} 세대<br>
                🔥 사용량: %{customdata[2]:,.0f} m³<br>
                🛠 난방방식: %{customdata[4]}<br>
                📍 주소: %{customdata[3]}<br>
                <extra></extra>
            """,
            name=f"{group['난방방식'].iloc[0]}"
        ))

    # 색상 범례 전용 trace
    fig.add_trace(go.Scattermapbox(
        lat=[None],
        lon=[None],
        mode="markers",
        marker=dict(
            size=0,
            color=df["marker_color"],
            colorscale="Plasma",
            cmin=df["사용량_m3"].min(),
            cmax=df["사용량_m3"].max(),
            showscale=True,
            colorbar=dict(
                title="사용량<br>(m³)",
                x=1.0,
                y=0.5,
                len=0.75
            )
        ),
        hoverinfo='none',
        showlegend=False
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        mapbox_zoom=11,
        height=700,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(
            title="난방방식",
            x=0,
            y=1,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.7)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 데이터 보기", expanded=False):
        st.dataframe(df[["공동주택명", "세대수", "난방방식", "사용량_m3", "주소"]], use_container_width=True)

if __name__ == "__main__":
    run()
