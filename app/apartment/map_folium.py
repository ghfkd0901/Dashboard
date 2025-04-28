import streamlit as st
import pandas as pd
import folium
from folium import CircleMarker
import json
from streamlit_folium import st_folium
import plotly.express as px

def run():
    st.title("🏢 공동주택 지도 시각화 대시보드 (Folium 최종 버전)")

    # 데이터 로딩
    @st.cache_data
    def load_data():
        path = "data/apartment/apart_info_vworld.csv"
        try:
            return pd.read_csv(path, encoding="utf-8")
        except:
            return pd.read_csv(path, encoding="cp949")

    df = load_data()

    # --------------------------------------------
    # 🎛️ 필터 설정 (모두 Multiselect)
    # --------------------------------------------
    filters = {}

    col1, col2, col3 = st.columns(3)
    with col1:
        filters["난방방식"] = st.multiselect("난방방식", sorted(df["난방방식"].dropna().unique()))
    with col2:
        filters["난방연료"] = st.multiselect("난방연료", sorted(df["난방연료"].dropna().unique()))
    with col3:
        filters["난방공급업체"] = st.multiselect("난방공급업체", sorted(df["난방공급업체"].dropna().unique()))

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        filters["고시지역여부"] = st.multiselect("고시지역여부", [True, False])
    with col5:
        filters["고시지역명"] = st.multiselect("고시지역명", sorted(df["고시지역명"].dropna().unique()))
    with col6:
        filters["시도"] = st.multiselect("시도", sorted(df["시도"].dropna().unique()))
    with col7:
        if filters["시도"]:
            districts = df[df["시도"].isin(filters["시도"])]["시군구"].dropna().unique()
        else:
            districts = df["시군구"].dropna().unique()
        filters["시군구"] = st.multiselect("시군구", sorted(districts))

    # 🧹 필터 적용
    filtered = df.copy()
    for key, value in filters.items():
        if value:
            filtered = filtered[filtered[key].isin(value)]

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

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="cartodb positron")

    # 색상 구분 함수
    def get_color_by(df, filters):
        if filters["난방방식"] and len(filters["난방방식"]) == 1 and filters["난방방식"][0] == "중앙난방":
            return "난방연료"
        elif filters["난방방식"] and len(filters["난방방식"]) == 1 and filters["난방방식"][0] == "지역난방":
            if filters["난방공급업체"] and "한국지역난방공사" in filters["난방공급업체"]:
                return "고시지역여부"
            else:
                return "난방공급업체"
        elif filters["난방방식"] and len(filters["난방방식"]) == 1 and filters["난방방식"][0] == "개별난방":
            return "난방방식"
        else:
            return "난방방식"

    color_column = get_color_by(filters=filters, df=filtered)

    if color_column == "난방방식":
        value_color_map = {
            "개별난방": "gray",
            "지역난방": "red",
            "중앙난방": "blue"
        }
    else:
        unique_values = filtered[color_column].dropna().unique()
        palette = px.colors.qualitative.Set1
        color_list = palette * ((len(unique_values) // len(palette)) + 1)
        value_color_map = {v: color_list[i] for i, v in enumerate(sorted(unique_values))}

    # 지도에 마커 추가
    for idx, row in map_df.iterrows():
        color_key = row[color_column]
        color = value_color_map.get(color_key, "gray")

        tooltip_text = (
            f"단지명: {row['단지명']}<br>"
            f"세대수: {row['세대수']} 세대<br>"
            f"난방방식: {row['난방방식']}<br>"
            f"난방연료: {row['난방연료']}<br>"
            f"난방공급업체: {row['난방공급업체']}<br>"
            f"고시지역명: {row['고시지역명']}"
        )

        CircleMarker(
            location=[row["위도"], row["경도"]],
            radius=4,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(row["단지명"], max_width=300),
            tooltip=folium.Tooltip(tooltip_text, sticky=True)
        ).add_to(m)

    # 고시지역 geojson 추가 (클릭/호버 완전 차단)
    with open("data/apartment/gosi_region.geojson", encoding="utf-8") as f:
        geojson_data = json.load(f)

    folium.GeoJson(
        geojson_data,
        name="고시지역",
        style_function=lambda feature: {
            "fillColor": "red",
            "color": "red",
            "weight": 1,
            "fillOpacity": 0.2,
            "opacity": 0.2,
            "interactive": False
        },
        tooltip=None
    ).add_to(m)

    # 지도 보여주기 + 클릭 감지
    st_data = st_folium(m, width="100%", height=800, returned_objects=["last_object_clicked"])

    if st_data and st_data["last_object_clicked"] is not None:
        clicked_lat = st_data["last_object_clicked"]["lat"]
        clicked_lon = st_data["last_object_clicked"]["lng"]

        clicked_df = map_df[
            (map_df["위도"].sub(clicked_lat).abs() < 0.0001) &
            (map_df["경도"].sub(clicked_lon).abs() < 0.0001)
        ]

        if not clicked_df.empty:
            clicked_row = clicked_df.iloc[0]

            # 사이드바에 단지 정보 표시
            st.sidebar.markdown(f"## 🏢 {clicked_row['단지명']}")
            for col in clicked_df.columns:
                value = clicked_row[col]
                if pd.notnull(value):
                    st.sidebar.markdown(f"""
                    <div style="background-color: #f9f9f9; padding: 8px 12px; border-radius: 8px; margin-bottom: 5px;">
                        <b>{col}</b><br>{value}
                    </div>
                    """, unsafe_allow_html=True)

    # 📋 전체 데이터 테이블 (접이식)
    with st.expander("📋 상세 데이터 보기", expanded=False):
        st.dataframe(
            filtered[["단지명", "세대수", "난방방식", "난방연료", "난방공급업체", "고시지역명"]],
            use_container_width=True,
            height=400
        )

    st.caption("© 2025 공동주택 대시보드 (Folium 최종 버전)")

