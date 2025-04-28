import streamlit as st
from app.apartment import map as apart_map
from app.apartment import map_folium as apart_map_folium 
from app.sales import comparison_map_by_customer as comparison_map_by_customer  # 고객명 기준만 사용

st.set_page_config(page_title="Sales Dashboard", layout="wide")

st.sidebar.title("Sales Dashboard")

# 상위 메뉴
main_category = st.sidebar.selectbox("Select Category", ["🏢 Apartment", "📉 Sales"])

# 하위 메뉴
if main_category == "🏢 Apartment":
    sub_page = st.sidebar.radio("Apartment Pages", ["📍 Map (Plotly)", "🗺️ Map (Folium)"])

    if sub_page == "📍 Map (Plotly)":
        apart_map.run()
    elif sub_page == "🗺️ Map (Folium)":
        apart_map_folium.run()

elif main_category == "📉 Sales":
    sub_page = st.sidebar.radio("Sales Pages", [
        "👥 YoY Comparison (Customer)"
    ])

    if sub_page == "👥 YoY Comparison (Customer)":
        comparison_map_by_customer.run()