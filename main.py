import streamlit as st
from app.apartment import map as apart_map
from app.sales import comparison_map as comparison_map

st.set_page_config(page_title="Sales Dashboard", layout="wide")

st.sidebar.title("Sales Dashboard")

# 상위 메뉴
main_category = st.sidebar.selectbox("Select Category", ["🏢 Apartment", "📉 Sales"])

# 하위 메뉴
if main_category == "🏢 Apartment":
    sub_page = st.sidebar.radio("Apartment Pages", ["📍 Map"])

    if sub_page == "📍 Map":
        apart_map.run()

elif main_category == "📉 Sales":
    sub_page = st.sidebar.radio("Sales Pages", ["📉 YoY Comparison"])

    if sub_page == "📉 YoY Comparison":
        comparison_map.run()
