import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import json
import os

# Set Streamlit page configuration
st.set_page_config(page_title="PhonePe Pulse Dashboard", layout="wide")

# Database connection using SQLAlchemy
@st.cache_resource
def get_db_engine():
    try:
        engine = create_engine("mysql+mysqlconnector://root:12345@localhost:3306/phonepe_db")
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Load GeoJSON data
@st.cache_data
def load_geojson():
    try:
        with open("Indian_States.geojson", "r") as f:
            geojson_data = json.load(f)
        # Standardize state names in GeoJSON
        for feature in geojson_data["features"]:
            if "properties" not in feature or not isinstance(feature["properties"], dict):
                feature["properties"] = {}
            state_name = feature["properties"].get("NAME_1", "")
            if isinstance(state_name, str):
                feature["properties"]["State_Name"] = state_name.lower().strip()
            else:
                feature["properties"]["State_Name"] = ""
        return geojson_data
    except Exception as e:
        st.error(f"Failed to load GeoJSON data: {e}")
        return {"type": "FeatureCollection", "features": []}

# Load data from MySQL with caching
@st.cache_data
def load_data(table_name):
    engine = get_db_engine()
    if engine is None:
        st.error(f"Database connection failed for {table_name}")
        return pd.DataFrame()
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        #st.write(f"Loaded {table_name} with columns: {list(df.columns)} and shape: {df.shape}")  # Debugging
        if "States" in df.columns:
            df["States"] = df["States"].str.lower().str.strip().replace({
                "andaman and nicobar": "andaman & nicobar islands",
                "dadra and nagar haveli and daman and diu": "dadra & nagar haveli & daman & diu"
            })
            df.rename(columns={"States": "State", "transaction_type": "Transaction_type"}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Failed to load data from {table_name}: {e}")
        return pd.DataFrame()

# Load all required tables
agg_tr_df = load_data("aggregated_transaction")
agg_insur_df = load_data("aggregated_insurance")
agg_user_df = load_data("aggregated_user")
map_tr_df = load_data("map_transaction")
map_insur_df = load_data("map_insurance")
map_user_df = load_data("map_user")
top_tr_df = load_data("top_transaction")
top_insur_df = load_data("top_insurance")
top_user_df = load_data("top_user")

# Load GeoJSON
geojson_data = load_geojson()

# Sidebar navigation
st.sidebar.title("PhonePe Pulse")
page = st.sidebar.radio("Navigation", ["Home", "Case Studies"])

if page == "Home":
    st.title("PhonePe Pulse | The Beat of Progress")
    st.markdown("""
    ## Welcome to PhonePe Pulse
    Explore India's digital transaction landscape with **PhonePe Pulse**. This dashboard provides insights into transaction trends, user engagement, insurance adoption, and market expansion opportunities across states, districts, and pincodes.

    ### Key Features
    - **Transaction Analysis**: Visualize transaction volumes and amounts by state and payment type.
    - **User Engagement**: Understand device preferences and app usage patterns.
    - **Insurance Insights**: Track insurance transaction growth.
    - **Market Expansion**: Identify high-potential regions for growth.
    - Navigate to **Case Studies** for detailed analyses.
    """)

    # Quick Stats
    st.subheader("Quick Stats")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_transactions = agg_tr_df["Transaction_count"].sum() if not agg_tr_df.empty else 0
        st.metric("Total Transactions", f"{total_transactions / 1e9:.2f}B")
    with col2:
        total_amount = agg_tr_df["Transaction_amount"].sum() if not agg_tr_df.empty else 0
        st.metric("Total Amount", f"₹{total_amount / 1e12:.2f}T")
    with col3:
        total_users = top_user_df["Registered_Users"].sum() if not top_user_df.empty else 0
        st.metric("Registered Users", f"{total_users / 1e6:.2f}M")

    # Transaction Heatmap
    st.subheader("India Transaction Heatmap")
    if not agg_tr_df.empty:
        latest_year = agg_tr_df["Years"].max()
        latest_quarter = agg_tr_df[agg_tr_df["Years"] == latest_year]["Quarter"].max()
        filtered_df = agg_tr_df[(agg_tr_df["Years"] == latest_year) & (agg_tr_df["Quarter"] == latest_quarter)]
        filtered_df = filtered_df.groupby("State").agg({
            "Transaction_amount": "sum",
            "Transaction_count": "sum"
        }).reset_index()

        fig = go.Figure(data=go.Choropleth(
            geojson=geojson_data,
            featureidkey="properties.State_Name",
            locationmode="geojson-id",
            locations=filtered_df["State"],
            z=filtered_df["Transaction_amount"] / 1e6,
            colorscale="Viridis",
            marker_line_color="white",
            marker_line_width=1.5,
            zmin=0,
            zmax=filtered_df["Transaction_amount"].max() / 1e6 if not filtered_df.empty else 1000,
            colorbar=dict(
                title="Transaction Amount (₹M)",
                thickness=15,
                len=0.8,
                bgcolor="rgba(255,255,255,0.6)",
                xanchor="left",
                x=0.01,
                yanchor="bottom",
                y=0.1
            )
        ))
        fig.update_geos(
            visible=False,
            projection=dict(type="conic conformal", parallels=[12.47, 35.17], rotation={"lat": 24, "lon": 80}),
            lonaxis={"range": [68, 98]},
            lataxis={"range": [6, 38]}
        )
        fig.update_layout(
            title=f"Transactions in {latest_year} Q{latest_quarter}",
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            height=550,
            width=550
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No transaction data available for the heatmap.")

    # Transaction Trend
    st.subheader("Transaction Trend Over Time")
    if not agg_tr_df.empty:
        trend_data = agg_tr_df.groupby(["Years", "Quarter"])["Transaction_amount"].sum().reset_index()
        trend_data["Year_Quarter"] = trend_data["Years"].astype(str) + " Q" + trend_data["Quarter"].astype(str)
        fig = px.line(
            trend_data,
            x="Year_Quarter",
            y="Transaction_amount",
            title="Total Transaction Amount Over Time",
            markers=True,
            height=400
        )
        fig.update_layout(xaxis_title="Year & Quarter", yaxis_title="Transaction Amount (₹)", yaxis=dict(tickformat=".2e"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No transaction data available for trend analysis.")

if page == "Case Studies":
    case_study = st.sidebar.selectbox("Select Case Study", [
        "Decoding Transaction Dynamics",
        "Device Dominance & User Engagement",
        "Insurance Penetration & Growth",
        "Transaction Analysis for Expansion",
        "User Engagement & Growth Strategy"
    ])

    
    # Case Study 1: Decoding Transaction Dynamics
    # --- Case Study 1: Decoding Transaction Dynamics ---
    if case_study == "Decoding Transaction Dynamics":
        st.header("Decoding Transaction Dynamics on PhonePe")
        st.markdown("Analyze transaction variations across states, quarters, and payment types to drive targeted strategies.")

        col1, col2 = st.columns(2)
        selected_year = col1.selectbox("Year", sorted(agg_tr_df["Years"].unique()) if not agg_tr_df.empty else [2023], key="cs1_year")
        selected_quarter = col2.selectbox("Quarter", sorted(agg_tr_df[agg_tr_df["Years"] == selected_year]["Quarter"].unique()) if not agg_tr_df.empty else [1], key="cs1_quarter")

        tr_slice = pd.DataFrame()
        if not agg_tr_df.empty:
            tr_slice = agg_tr_df[(agg_tr_df["Years"] == selected_year) & (agg_tr_df["Quarter"] == selected_quarter)]

    # Choropleth Map
        if not tr_slice.empty:
            tr_map = tr_slice.groupby("State", as_index=False).agg({
                "Transaction_amount": "sum",
                "Transaction_count": "sum"
            })
            fig = go.Figure(data=go.Choropleth(
                geojson=geojson_data,
                featureidkey="properties.State_Name",
                locationmode="geojson-id",
                locations=tr_map["State"],
                z=tr_map["Transaction_amount"] / 1e6,
                colorscale="Greens",
                marker_line_color="white",
                marker_line_width=1.5,
                zmin=0,
                zmax=tr_map["Transaction_amount"].max() / 1e6 if not tr_map.empty else 1000,
                colorbar=dict(title="Transaction Amount (₹M)")
            ))
            fig.update_geos(visible=False, projection=dict(type="conic conformal", parallels=[12.47, 35.17], rotation={"lat": 24, "lon": 80}))
            fig.update_layout(title=f"Transactions in {selected_year} Q{selected_quarter}", height=550)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No transaction data available for the selected period.")

    # Payment Type Distribution
        st.subheader("Payment Type Distribution")
        if not tr_slice.empty and "Transaction_type" in tr_slice.columns:
            type_summary = (tr_slice.groupby("Transaction_type", as_index=False)["Transaction_count"]
                            .sum()
                            .nlargest(5, "Transaction_count"))
            if not type_summary.empty:
                fig = px.pie(type_summary, values="Transaction_count", names="Transaction_type",
                            title="Transaction Count by Type", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No transaction type data available after grouping.")
        else:
            st.warning("No transaction type data available for the selected year and quarter.")

    # Top States by Amount
        st.subheader("Top States by Transaction Amount")
        if not tr_slice.empty:
            state_summary = tr_map.nlargest(10, "Transaction_amount").copy()
            state_summary["Transaction_amount"] /= 1e12
            fig = px.bar(state_summary, x="State", y="Transaction_amount",
                        title="Top 10 States", text_auto=".2f", color="State")
            fig.update_layout(yaxis_title="Transaction Amount (₹T)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No state data available for the selected period.")


    # Case Study 2: Device Dominance & User Engagement
    if case_study == "Device Dominance & User Engagement":
        st.header("Device Dominance & User Engagement Analysis")
        st.markdown("Explore user preferences across device brands and engagement patterns by region.")

        col1, col2 = st.columns(2)
        selected_year = col1.selectbox("Year", sorted(agg_user_df["Years"].unique()) if not agg_user_df.empty else [2023], key="cs2_year")
        selected_quarter = col2.selectbox("Quarter", sorted(agg_user_df[agg_user_df["Years"] == selected_year]["Quarter"].unique()) if not agg_user_df.empty else [1], key="cs2_quarter")

        # Device Brand Distribution
        st.subheader("Device Brand Usage")
        if not agg_user_df.empty:
            filtered_df = agg_user_df[(agg_user_df["Years"] == selected_year) & (agg_user_df["Quarter"] == selected_quarter)]
            if "Brands" in filtered_df.columns:
                summary = filtered_df.groupby("Brands")["Transaction_count"].sum().nlargest(5).reset_index()
                fig = px.pie(summary, values="Transaction_count", names="Brands", title="Top Device Brands", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No device brand data available.")
        else:
            st.warning("No user data available for the selected period.")

        # App Opens by District
        st.subheader("App Opens by District")
        if not map_user_df.empty:
            filtered_map = map_user_df[(map_user_df["Years"] == selected_year) & (map_user_df["Quarter"] == selected_quarter)]
            if "AppOpens" in filtered_map.columns:
                summary = filtered_map.groupby("District")["AppOpens"].sum().nlargest(10).reset_index()
                fig = px.bar(summary, x="District", y="AppOpens", title="Top 10 Districts by App Opens", color="District")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No app opens data available.")
        else:
            st.warning("No map user data available for the selected period.")

    # Case Study 3: Insurance Penetration & Growth
    if case_study == "Insurance Penetration & Growth":
        st.header("Insurance Penetration & Growth Potential Analysis")
        st.markdown("Identify insurance transaction growth and untapped markets by state.")

        col1, col2 = st.columns(2)
        selected_year = col1.selectbox("Year", sorted(agg_insur_df["Years"].unique()) if not agg_insur_df.empty else [2023], key="cs3_year")
        selected_quarter = col2.selectbox("Quarter", sorted(agg_insur_df[agg_insur_df["Years"] == selected_year]["Quarter"].unique()) if not agg_insur_df.empty else [1], key="cs3_quarter")

        # Insurance Heatmap
        if not agg_insur_df.empty:
            filtered_df = agg_insur_df[(agg_insur_df["Years"] == selected_year) & (agg_insur_df["Quarter"] == selected_quarter)]
            filtered_df = filtered_df.groupby("State").agg({"Insurance_amount": "sum", "Insurance_count": "sum"}).reset_index()
            fig = go.Figure(data=go.Choropleth(
                geojson=geojson_data,
                featureidkey="properties.State_Name",
                locationmode="geojson-id",
                locations=filtered_df["State"],
                z=filtered_df["Insurance_amount"] / 1e3,
                colorscale="Earth",
                marker_line_color="white",
                marker_line_width=1.5,
                zmin=0,
                zmax=filtered_df["Insurance_amount"].max() / 1e3 if not filtered_df.empty else 1000,
                colorbar=dict(title="Insurance Amount (₹K)")
            ))
            fig.update_geos(
                visible=False,
                projection=dict(type="conic conformal", parallels=[12.47, 35.17], rotation={"lat": 24, "lon": 80}),
                lonaxis={"range": [68, 98]},
                lataxis={"range": [6, 38]}
            )
            fig.update_layout(title=f"Insurance Transactions in {selected_year} Q{selected_quarter}", height=550)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No insurance data available for the selected period.")

        # Growth Trend
        st.subheader("Insurance Growth Trend")
        if not agg_insur_df.empty:
            trend_data = agg_insur_df[agg_insur_df["Years"] == selected_year].groupby("Quarter")["Insurance_amount"].sum().reset_index()
            fig = px.line(trend_data, x="Quarter", y="Insurance_amount", title="Insurance Amount by Quarter", markers=True)
            fig.update_layout(yaxis_title="Insurance Amount (₹)", yaxis=dict(tickformat=".2e"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No insurance data available for trend analysis.")

    # Case Study 4: Transaction Analysis for Expansion
    if case_study == "Transaction Analysis for Expansion":
        st.header("Transaction Analysis for Market Expansion")
        st.markdown("Identify transaction trends for market expansion opportunities.")

        col1, col2 = st.columns(2)
        selected_year = col1.selectbox("Year", sorted(map_tr_df["Years"].unique()) if not map_tr_df.empty else [2023], key="cs4_year")
        selected_quarter = col2.selectbox("Quarter", sorted(map_tr_df[map_tr_df["Years"] == selected_year]["Quarter"].unique()) if not map_tr_df.empty else [1], key="cs4_quarter")

        # Transaction Heatmap
        if not map_tr_df.empty:
            filtered_df = map_tr_df[(map_tr_df["Years"] == selected_year) & (map_tr_df["Quarter"] == selected_quarter)]
            filtered_df = filtered_df.groupby("State").agg({"Transaction_amount": "sum", "Transaction_count": "sum"}).reset_index()
            fig = go.Figure(data=go.Choropleth(
                geojson=geojson_data,
                featureidkey="properties.State_Name",
                locationmode="geojson-id",
                locations=filtered_df["State"],
                z=filtered_df["Transaction_amount"] / 1e6,
                colorscale="Armyrose",
                marker_line_color="white",
                marker_line_width=1.5,
                zmin=0,
                zmax=filtered_df["Transaction_amount"].max() / 1e6 if not filtered_df.empty else 1000,
                colorbar=dict(title="Transaction Amount (₹M)")
            ))
            fig.update_geos(
                visible=False,
                projection=dict(type="conic conformal", parallels=[12.47, 35.17], rotation={"lat": 24, "lon": 80}),
                lonaxis={"range": [68, 98]},
                lataxis={"range": [6, 38]}
            )
            fig.update_layout(title=f"Transactions in {selected_year} Q{selected_quarter}", height=550)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No transaction data available for the selected period.")

        # Growth Analysis
        st.subheader("Transaction Growth Analysis")
        if not map_tr_df.empty:
            filtered_df = map_tr_df[map_tr_df["Years"] == selected_year]
            growth_data = filtered_df.groupby(["State", "Quarter"])["Transaction_amount"].sum().reset_index()
            growth_data["Growth_Percentage"] = growth_data.groupby("State")["Transaction_amount"].pct_change() * 100
            growth_data.dropna(inplace=True)
            fig = px.bar(growth_data, x="State", y="Growth_Percentage", color="Quarter", title="Quarterly Growth by State")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No transaction data available for growth analysis.")

    # Case Study 5: User Engagement & Growth Strategy
    if case_study == "User Engagement & Growth Strategy":
        st.header("User Engagement & Growth Strategy")
        st.markdown("Analyze registered users and app opens to inform growth strategies.")

        col1, col2 = st.columns(2)
        years_available = sorted(map_user_df["Years"].unique()) if not map_user_df.empty else [2023]
        selected_year = col1.selectbox("Year", years_available, key="cs5_year")
        quarters_available = sorted(map_user_df[map_user_df["Years"] == selected_year]["Quarter"].unique()) if not map_user_df.empty else [1]
        selected_quarter = col2.selectbox("Quarter", quarters_available, key="cs5_quarter")

    # User Heatmap
    if not map_user_df.empty:
        filtered_df = map_user_df[(map_user_df["Years"] == selected_year) & (map_user_df["Quarter"] == selected_quarter)]
        if not filtered_df.empty:
            filtered_df = filtered_df.groupby("State").agg({"RegisteredUsers": "sum", "AppOpens": "sum"}).reset_index()
            fig = go.Figure(data=go.Choropleth(
                geojson=geojson_data,
                featureidkey="properties.State_Name",
                locationmode="geojson-id",
                locations=filtered_df["State"],
                z=filtered_df["RegisteredUsers"] / 1e3,
                colorscale="Portland",
                marker_line_color="white",
                marker_line_width=1.5,
                zmin=0,
                zmax=filtered_df["RegisteredUsers"].max() / 1e3 if not filtered_df.empty else 1000,
                colorbar=dict(title="Registered Users (K)")
            ))
            fig.update_geos(
                visible=False,
                projection=dict(type="conic conformal", parallels=[12.47, 35.17], rotation={"lat": 24, "lon": 80}),
                lonaxis={"range": [68, 98]},
                lataxis={"range": [6, 38]}
            )
            fig.update_layout(title=f"Registered Users in {selected_year} Q{selected_quarter}", height=550)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No user data available for {selected_year} Q{selected_quarter}.")
    else:
        st.warning("No user data available.")

    # Engagement Analysis (Replaced Scatter with Stacked Bar Chart)
    st.subheader("App Opens vs. Registered Users")
    if not map_user_df.empty:
        filtered_df = map_user_df[(map_user_df["Years"] == selected_year) & (map_user_df["Quarter"] == selected_quarter)]
        if not filtered_df.empty:
            engagement_df = filtered_df.groupby("State").agg({"RegisteredUsers": "sum", "AppOpens": "sum"}).reset_index()
            fig = px.bar(engagement_df, x="State", y=["RegisteredUsers", "AppOpens"],
                         title="Registered Users vs. App Opens by State",
                         labels={"value": "Count", "variable": "Metric"},
                         barmode="stack",
                         height=400)
            fig.update_layout(xaxis_title="State", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No engagement data available for {selected_year} Q{selected_quarter}.")
    else:
        st.warning("No engagement data available.")