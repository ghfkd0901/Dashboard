import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


def run():
    st.title("📉 전년동월 판매량 비교 대시보드")

    # --------------------------------------------
    # 1. 파일 목록에서 월 추출
    # --------------------------------------------
    data_dir = Path("data/sales/rest_sales/yoy_comparsion/by_customer")
    file_list = sorted(data_dir.glob("yoy_comparison_by_customer_*.csv"))
    available_months = [f.stem.split("_")[-1] for f in file_list]

    if not available_months:
        st.warning("⚠️ 전년동월 비교 파일이 존재하지 않습니다.")
        return

    # --------------------------------------------
    # 2. 기준 월 선택
    # --------------------------------------------
    selected_month = st.selectbox("📅 기준 월 선택", available_months, index=len(available_months) - 1)

    # --------------------------------------------
    # 3. 파일 로딩 + NaN/음수 처리
    # --------------------------------------------
    file_path = data_dir / f"yoy_comparison_by_customer_{selected_month}.csv"
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

        df["전년동월판매량"] = df["전년동월판매량"].fillna(0)
        df["당년판매량"] = df["당년판매량"].fillna(0)
        df["증감"] = df["증감"].fillna(0)
        df["증감률"] = df["증감률"].fillna(0)
        df["상태"] = df["상태"].fillna("유지")
        df["증감범주"] = df["증감범주"].fillna("정상")

        df["마커크기"] = df.apply(lambda row: row["당년판매량"] if row["상태"] != "해지" else row["전년동월판매량"], axis=1)
        df["마커크기"] = df["마커크기"].apply(lambda x: max(x, 10))

    except FileNotFoundError:
        st.error(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return

    # --------------------------------------------
    # 4. 필터 섹션 (가로 배치)
    # --------------------------------------------
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        selected_product = st.multiselect("상품명", sorted(df['상품명'].dropna().unique()))

    with col2:
        selected_usage = st.multiselect("용도", sorted(df['용도'].dropna().unique()))

    if selected_usage:
        category1_options = sorted(df[df['용도'].isin(selected_usage)]['업종분류'].dropna().unique())
    else:
        category1_options = sorted(df['업종분류'].dropna().unique())

    with col3:
        selected_category1 = st.multiselect("업종분류", category1_options)

    if selected_category1:
        category2_options = sorted(df[df['업종분류'].isin(selected_category1)]['업종'].dropna().unique())
    else:
        category2_options = sorted(df['업종'].dropna().unique())

    with col4:
        selected_category2 = st.multiselect("업종", category2_options)

    with col5:
        selected_status = st.multiselect("상태", sorted(df["상태"].dropna().unique()))

    with col6:
        st.markdown(" ")  # 공간 유지용

    # --------------------------------------------
    # 5. 필터 적용
    # --------------------------------------------
    filtered_df = df.copy()
    if selected_product:
        filtered_df = filtered_df[filtered_df['상품명'].isin(selected_product)]
    if selected_usage:
        filtered_df = filtered_df[filtered_df['용도'].isin(selected_usage)]
    if selected_category1:
        filtered_df = filtered_df[filtered_df['업종분류'].isin(selected_category1)]
    if selected_category2:
        filtered_df = filtered_df[filtered_df['업종'].isin(selected_category2)]
    if selected_status:
        filtered_df = filtered_df[filtered_df['상태'].isin(selected_status)]

    # --------------------------------------------
    # 6. 색상 맵 정의
    # --------------------------------------------
    status_color_map = {
        "해지": "red",
        "신규": "blue",
        "유지": "limegreen"
    }

    change_color_map = {
        "20% 이상 증가": "blue",
        "20% 이상 감소": "red",
        "유지": "limegreen",
        None: "lightgray"
    }

    # --------------------------------------------
    # 7. 지도 시각화
    # --------------------------------------------
    df_map = filtered_df.dropna(subset=["위도", "경도"])
    if df_map.empty:
        st.warning("⚠️ 지도에 표시할 데이터가 없습니다.")
        return

    center_lat = df_map["위도"].mean()
    center_lon = df_map["경도"].mean()

    if selected_status == ["유지"]:
        fig = px.scatter_mapbox(
            df_map,
            lat="위도",
            lon="경도",
            size="마커크기",
            size_max=25,
            color="증감범주",
            color_discrete_map=change_color_map,
            hover_name="고객명",
            hover_data={
                "고객명": True,
                "상품명": True,
                "용도": True,
                "업종": True,
                "전년동월판매량": True,
                "당년판매량": True,
                "증감": True,
                "증감률": True,
                "증감범주": True,
                "상태": True
            },
            zoom=10,
            height=600
        )
    else:
        fig = px.scatter_mapbox(
            df_map,
            lat="위도",
            lon="경도",
            size="마커크기",
            size_max=25,
            color="상태",
            color_discrete_map=status_color_map,
            hover_name="고객명",
            hover_data={
                "고객명": True,
                "상품명": True,
                "용도": True,
                "업종": True,
                "전년동월판매량": True,
                "당년판매량": True,
                "증감": True,
                "증감률": True,
                "증감범주": True,
                "상태": True
            },
            zoom=10,
            height=600
        )

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        margin={"r": 0, "t": 30, "l": 0, "b": 0}
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    # --------------------------------------------
    # 8. 상세 테이블
    # --------------------------------------------
    with st.expander("📋 상세 데이터 보기", expanded=False):
        st.dataframe(
            filtered_df[[  # 열 순서 자유롭게 변경 가능
                "고객명", "상품명", "용도", "업종",
                "전년동월판매량", "당년판매량", "증감", "증감률", "증감범주", "상태"
            ]],
            use_container_width=True,
            height=400
        )

    st.caption("© 2025 전년동월 판매량 비교 대시보드")
