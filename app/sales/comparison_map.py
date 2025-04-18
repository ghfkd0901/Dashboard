import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

def run():
    st.title("📉 Year-over-Year Sales Comparison")

    try:
        df = pd.read_csv("data/sale_comparison_map/sales_comparison.csv")
    except:
        st.warning("⚠️ sales_comparison.csv not found in data/sale_comparison_map/")
        return

    st.write("Preview of sales comparison data", df.head())

    m = folium.Map(location=[35.8722, 128.6025], zoom_start=11)

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            popup=f"{row['name']} ({row['change_rate']}%)",
            color='green' if row["change_rate"] >= 0 else 'red',
            fill=True,
            fill_opacity=0.6
        ).add_to(m)

    st_folium(m, width=700, height=500)
