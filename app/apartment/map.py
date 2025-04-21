import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

def run():
    st.title("🏢 공동주택 지도 시각화 대시보드")

    # 데이터 로딩
    @st.cache_data
    def load_data():
        path = "data/apartment/apart_info.csv"
        try:
            return pd.read_csv(path, encoding="utf-8")
        except:
            return pd.read_csv(path, encoding="cp949")

    df = load_data()

    # --------------------------------------------
    # 🎛️ 필터 설정 (2행 구조)
    # --------------------------------------------
    filters = {}

    col1, col2, col3 = st.columns(3)
    with col1:
        filters["난방방식"] = st.selectbox("난방방식", ["전체"] + sorted(df["난방방식"].dropna().unique()))
    with col2:
        filters["난방연료"] = st.selectbox("난방연료", ["전체"] + sorted(df["난방연료"].dropna().unique()))
    with col3:
        filters["난방공급업체"] = st.selectbox("난방공급업체", ["전체"] + sorted(df["난방공급업체"].dropna().unique()))

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        filters["고시지역여부"] = st.selectbox("고시지역여부", ["전체", "True", "False"])
    with col5:
        filters["고시지역명"] = st.selectbox("고시지역명", ["전체"] + sorted(df["고시지역명"].dropna().unique()))
    with col6:
        filters["시도"] = st.selectbox("시도", ["전체"] + sorted(df["시도"].dropna().unique()))
    with col7:
        if filters["시도"] != "전체":
            districts = df[df["시도"] == filters["시도"]]["시군구"].dropna().unique()
        else:
            districts = []
        filters["시군구"] = st.selectbox("시군구", ["전체"] + sorted(districts))

    # 필터 적용
    filtered = df.copy()
    for key, value in filters.items():
        if value != "전체":
            if key == "고시지역여부":
                filtered = filtered[filtered[key] == (value == "True")]
            else:
                filtered = filtered[filtered[key] == value]

    # --------------------------------------------
    # 📊 카드 요약 정보
    # --------------------------------------------
    complex_col = "단지코드" if "단지코드" in filtered.columns else "단지명"
    complex_count = filtered[complex_col].nunique()
    household_total = filtered["세대수"].fillna(0).astype(int).sum()

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("단지 수", f"{complex_count:,} 개")
    with col_b:
        st.metric("총 세대 수", f"{household_total:,} 세대")

    # --------------------------------------------
    # 🗺️ 지도 시각화
    # --------------------------------------------
    map_df = filtered.dropna(subset=["위도", "경도"])
    if len(map_df) > 5000:
        map_df = map_df.sample(5000, random_state=42)

    center_lat = map_df["위도"].mean()
    center_lon = map_df["경도"].mean()

    # 색상 구분 기준
    def get_color_by(df, filters):
        if filters["난방방식"] == "중앙난방":
            return "난방연료"
        elif filters["난방방식"] == "지역난방":
            if filters["난방공급업체"] == "한국지역난방공사":
                return "고시지역여부"
            elif filters["난방공급업체"] != "전체":
                return "난방공급업체"
            else:
                return "난방공급업체"
        elif filters["난방방식"] == "개별난방":
            return "난방방식"
        else:
            return "난방방식"

    color_column = get_color_by(filtered, filters)

    color_map = {}
    if color_column == "난방방식":
        color_map = {
            "개별난방": "gray",
            "지역난방": "red",
            "중앙난방": "blue"
        }

    fig = px.scatter_mapbox(
        map_df,
        lat="위도", lon="경도",
        color=color_column,
        hover_name="단지명",
        hover_data={
            "세대수": True,
            "난방방식": True,
            "난방연료": True,
            "난방공급업체": True,
            "고시지역명": True,
            "위도": False,
            "경도": False
        },
        zoom=10,
        height=600,
        color_discrete_map=color_map
    )

    # 고시지역 geojson 추가
    with open("data/apartment/gosi_region.geojson", encoding="utf-8") as f:
        geojson_data = json.load(f)

    locations = [feature["properties"]["Name"] for feature in geojson_data["features"]]
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson_data,
        locations=locations,
        z=[1] * len(locations),
        colorscale=[[0, "rgba(255, 0, 0, 0.15)"], [1, "rgba(255, 0, 0, 0.15)"]],
        showscale=False,
        marker_line_color="red",
        marker_line_width=1,
        featureidkey="properties.Name",
        name="고시지역",
        hoverinfo='skip'
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox=dict(center=dict(lat=center_lat, lon=center_lon)),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(
            x=0,
            y=1,
            xanchor="left",
            yanchor="top"
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    # --------------------------------------------
    # 📋 데이터 테이블 (접이식)
    # --------------------------------------------
    with st.expander("📋 상세 데이터 보기", expanded=False):
        st.dataframe(
            filtered[["단지명", "세대수", "난방방식", "난방연료", "난방공급업체", "고시지역명"]],
            use_container_width=True,
            height=400
        )

    st.caption("© 2025 공동주택 대시보드")
