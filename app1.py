# PhonePe Transaction Analysis Dashboard
# A simplified and refined Streamlit application for analyzing PhonePe transaction data

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import json

# ========================
# CONFIGURATION
# ========================
st.set_page_config(
    page_title="PhonePe Transaction Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# DATABASE CONNECTION
# ========================
@st.cache_resource
def get_database_engine():
    """Create database connection with error handling."""
    try:
        engine = create_engine("mysql+mysqlconnector://root:12345@localhost:3306/phonepe_db")
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# ========================
# DATA LOADING FUNCTIONS
# ========================
@st.cache_data
def load_geojson_data():
    """Load and process GeoJSON data with Odisha fix."""
    try:
        with open("Indian_States.geojson", "r") as f:
            geojson_data = json.load(f)
        
        # Process state names and fix Odisha mapping
        for feature in geojson_data["features"]:
            if "properties" not in feature:
                feature["properties"] = {}
            
            state_name = feature["properties"].get("NAME_1", "")
            if isinstance(state_name, str):
                # Standardize state name
                standardized_name = state_name.lower().strip()
                
                # Hardcoded fix for Odisha
                if standardized_name == "orissa":
                    standardized_name = "odisha"
                
                feature["properties"]["State_Name"] = standardized_name
            else:
                feature["properties"]["State_Name"] = ""
        
        return geojson_data
    except Exception as e:
        st.error(f"Failed to load GeoJSON data: {e}")
        return {"type": "FeatureCollection", "features": []}

@st.cache_data
def load_table_data(table_name):
    """Load data from database table with state name standardization."""
    engine = get_database_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        
        # Standardize state names if States column exists
        if "States" in df.columns:
            df["States"] = df["States"].str.lower().str.strip()
            
            # Apply state name mappings including Odisha fix
            state_mappings = {
                "andaman and nicobar": "andaman & nicobar islands",
                "dadra and nagar haveli and daman and diu": "dadra & nagar haveli & daman & diu",
                "orissa": "odisha"  # Hardcoded Odisha fix
            }
            df["States"] = df["States"].replace(state_mappings)
            
            # Rename States column to State for consistency
            df.rename(columns={"States": "State"}, inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Failed to load data from {table_name}: {e}")
        return pd.DataFrame()

# ========================
# DATA LOADING
# ========================
@st.cache_data
def load_all_data():
    """Load all required data tables."""
    tables = {
        "agg_transaction": "aggregated_transaction",
        "agg_insurance": "aggregated_insurance", 
        "agg_user": "aggregated_user",
        "map_transaction": "map_transaction",
        "map_insurance": "map_insurance",
        "map_user": "map_user",
        "top_transaction": "top_transaction",
        "top_insurance": "top_insurance",
        "top_user": "top_user"
    }
    
    data = {}
    for key, table_name in tables.items():
        data[key] = load_table_data(table_name)
    
    return data

# ========================
# VISUALIZATION FUNCTIONS
# ========================
def create_choropleth_map(df, value_col, title, color_scale="Viridis", value_suffix=""):
    """Create a standardized choropleth map."""
    if df.empty:
        st.warning("No data available for the map.")
        return None
    
    fig = go.Figure(data=go.Choropleth(
        geojson=geojson_data,
        featureidkey="properties.State_Name",
        locationmode="geojson-id",
        locations=df["State"],
        z=df[value_col],
        colorscale=color_scale,
        marker_line_color="white",
        marker_line_width=1.5,
        colorbar=dict(title=f"{value_col.replace('_', ' ').title()} ({value_suffix})")
    ))
    
    fig.update_geos(
        visible=False,
        projection=dict(type="conic conformal", parallels=[12.47, 35.17], rotation={"lat": 24, "lon": 80}),
        lonaxis={"range": [68, 98]},
        lataxis={"range": [6, 38]}
    )
    
    fig.update_layout(
        title=title,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        height=600
    )
    
    return fig

def create_pie_chart(df, values_col, names_col, title):
    """Create a standardized pie chart."""
    if df.empty:
        st.warning("No data available for the chart.")
        return None
    
    fig = px.pie(df, values=values_col, names=names_col, title=title, hole=0.4)
    fig.update_layout(height=400)
    return fig

def create_bar_chart(df, x_col, y_col, title, text_auto=True):
    """Create a standardized bar chart."""
    if df.empty:
        st.warning("No data available for the chart.")
        return None
    
    fig = px.bar(df, x=x_col, y=y_col, title=title, text_auto=text_auto, color=x_col)
    fig.update_layout(height=400, xaxis_title=x_col.replace('_', ' ').title(), 
                     yaxis_title=y_col.replace('_', ' ').title())
    return fig

# ========================
# MAIN APPLICATION
# ========================

# Load all data
data = load_all_data()
geojson_data = load_geojson_data()

# Sidebar Navigation
st.sidebar.title("PhonePe Transactions")
st.sidebar.markdown("### Navigate through different analysis sections")
page = st.sidebar.radio("Select Section", ["📊 Dashboard", "🔍 Case Studies"])

# ========================
# HOME PAGE / DASHBOARD
# ========================
if page == "📊 Dashboard":
    st.title("📱 PhonePe Transaction Analysis Dashboard")
    st.markdown("""
    ## Welcome to PhonePe Transaction Insights
    
    Explore India's digital payment landscape through comprehensive transaction analysis. 
    This dashboard provides insights into:
    
    - **💳 Transaction Patterns**: Volume and amount trends across states and time periods
    - **📱 User Engagement**: Device preferences and app usage analytics  
    - **🛡️ Insurance Growth**: Insurance transaction analysis and market penetration
    - **📈 Market Expansion**: Identify high-potential regions for business growth
    
    Navigate to **Case Studies** for detailed business analysis scenarios.
    """)

    # Quick Statistics
    st.subheader("📈 Quick Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_transactions = data["agg_transaction"]["Transaction_count"].sum() if not data["agg_transaction"].empty else 0
        st.metric("Total Transactions", f"{total_transactions / 1e9:.1f}B")
    
    with col2:
        total_amount = data["agg_transaction"]["Transaction_amount"].sum() if not data["agg_transaction"].empty else 0
        st.metric("Total Amount", f"₹{total_amount / 1e12:.1f}T")
    
    with col3:
        total_users = data["top_user"]["Registered_Users"].sum() if not data["top_user"].empty else 0
        st.metric("Registered Users", f"{total_users / 1e6:.1f}M")
        
    with col4:
        total_insurance = data["agg_insurance"]["Insurance_amount"].sum() if not data["agg_insurance"].empty else 0
        st.metric("Insurance Amount", f"₹{total_insurance / 1e9:.1f}B")

    # Main Dashboard Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗺️ Transaction Heatmap")
        if not data["agg_transaction"].empty:
            latest_year = data["agg_transaction"]["Years"].max()
            latest_quarter = data["agg_transaction"][data["agg_transaction"]["Years"] == latest_year]["Quarter"].max()
            
            filtered_df = data["agg_transaction"][
                (data["agg_transaction"]["Years"] == latest_year) & 
                (data["agg_transaction"]["Quarter"] == latest_quarter)
            ].groupby("State").agg({
                "Transaction_amount": "sum",
                "Transaction_count": "sum"
            }).reset_index()
            
            filtered_df["Amount_M"] = filtered_df["Transaction_amount"] / 1e6
            
            fig = create_choropleth_map(
                filtered_df, 
                "Amount_M", 
                f"Transaction Amount - {latest_year} Q{latest_quarter}",
                "Viridis",
                "₹M"
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Transaction Trend")
        if not data["agg_transaction"].empty:
            trend_data = data["agg_transaction"].groupby(["Years", "Quarter"])["Transaction_amount"].sum().reset_index()
            trend_data["Period"] = trend_data["Years"].astype(str) + " Q" + trend_data["Quarter"].astype(str)
            
            fig = px.line(
                trend_data, 
                x="Period", 
                y="Transaction_amount",
                title="Transaction Amount Over Time",
                markers=True
            )
            fig.update_layout(
                height=600,
                xaxis_title="Time Period",
                yaxis_title="Transaction Amount (₹)",
                yaxis=dict(tickformat=".2e")
            )
            st.plotly_chart(fig, use_container_width=True)

# ========================
# CASE STUDIES PAGE
# ========================
elif page == "🔍 Case Studies":
    st.title("🔍 Business Case Studies")
    
    case_study = st.sidebar.selectbox("Select Case Study", [
        "💳 Transaction Dynamics Analysis",
        "📱 Device Usage & User Engagement", 
        "🛡️ Insurance Market Analysis",
        "🎯 Market Expansion Strategy",
        "👥 User Growth Analysis"
    ])

    # Case Study 1: Transaction Dynamics
    if case_study == "💳 Transaction Dynamics Analysis":
        st.header("💳 Transaction Dynamics Analysis")
        st.markdown("**Objective**: Analyze transaction patterns across states, quarters, and payment types for strategic decision making.")
        
        # Time Period Selection
        col1, col2 = st.columns(2)
        with col1:
            years = sorted(data["agg_transaction"]["Years"].unique()) if not data["agg_transaction"].empty else [2023]
            selected_year = st.selectbox("Select Year", years, key="td_year")
        with col2:
            quarters = sorted(data["agg_transaction"][data["agg_transaction"]["Years"] == selected_year]["Quarter"].unique()) if not data["agg_transaction"].empty else [1]
            selected_quarter = st.selectbox("Select Quarter", quarters, key="td_quarter")

        if not data["agg_transaction"].empty:
            filtered_data = data["agg_transaction"][
                (data["agg_transaction"]["Years"] == selected_year) & 
                (data["agg_transaction"]["Quarter"] == selected_quarter)
            ]
            
            if not filtered_data.empty:
                # State-wise Analysis
                state_summary = filtered_data.groupby("State").agg({
                    "Transaction_amount": "sum",
                    "Transaction_count": "sum"
                }).reset_index()
                state_summary["Amount_M"] = state_summary["Transaction_amount"] / 1e6
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🗺️ State-wise Transaction Heatmap")
                    fig = create_choropleth_map(
                        state_summary, 
                        "Amount_M", 
                        f"Transactions - {selected_year} Q{selected_quarter}",
                        "Blues",
                        "₹M"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("💰 Top 10 States by Amount")
                    top_states = state_summary.nlargest(10, "Transaction_amount")
                    top_states["Amount_B"] = top_states["Transaction_amount"] / 1e9
                    
                    fig = create_bar_chart(
                        top_states, 
                        "State", 
                        "Amount_B", 
                        "Top States by Transaction Amount (₹B)"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                # Payment Type Analysis
                st.subheader("📊 Payment Type Distribution")
                if "Transaction_type" in filtered_data.columns:
                    payment_summary = filtered_data.groupby("Transaction_type")["Transaction_count"].sum().nlargest(5).reset_index()
                    fig = create_pie_chart(
                        payment_summary, 
                        "Transaction_count", 
                        "Transaction_type",
                        "Transaction Distribution by Payment Type"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

    # Case Study 2: Device Usage & User Engagement
    elif case_study == "📱 Device Usage & User Engagement":
        st.header("📱 Device Usage & User Engagement Analysis")
        st.markdown("**Objective**: Understand user device preferences and engagement patterns to optimize app performance.")
        
        # Time Period Selection
        col1, col2 = st.columns(2)
        with col1:
            years = sorted(data["agg_user"]["Years"].unique()) if not data["agg_user"].empty else [2023]
            selected_year = st.selectbox("Select Year", years, key="device_year")
        with col2:
            quarters = sorted(data["agg_user"][data["agg_user"]["Years"] == selected_year]["Quarter"].unique()) if not data["agg_user"].empty else [1]
            selected_quarter = st.selectbox("Select Quarter", quarters, key="device_quarter")

        if not data["agg_user"].empty:
            user_data = data["agg_user"][
                (data["agg_user"]["Years"] == selected_year) & 
                (data["agg_user"]["Quarter"] == selected_quarter)
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📱 Device Brand Distribution")
                if not user_data.empty and "Brands" in user_data.columns:
                    brand_summary = user_data.groupby("Brands")["Transaction_count"].sum().nlargest(8).reset_index()
                    fig = create_pie_chart(
                        brand_summary, 
                        "Transaction_count", 
                        "Brands",
                        "User Distribution by Device Brand"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🏙️ Top Districts by App Opens")
                if not data["map_user"].empty:
                    map_user_filtered = data["map_user"][
                        (data["map_user"]["Years"] == selected_year) & 
                        (data["map_user"]["Quarter"] == selected_quarter)
                    ]
                    if not map_user_filtered.empty and "AppOpens" in map_user_filtered.columns:
                        district_opens = map_user_filtered.groupby("District")["AppOpens"].sum().nlargest(10).reset_index()
                        fig = create_bar_chart(
                            district_opens, 
                            "District", 
                            "AppOpens",
                            "Top Districts by App Opens"
                        )
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)

    # Case Study 3: Insurance Market Analysis  
    elif case_study == "🛡️ Insurance Market Analysis":
        st.header("🛡️ Insurance Market Analysis")
        st.markdown("**Objective**: Analyze insurance transaction growth and identify market expansion opportunities.")
        
        # Time Period Selection
        col1, col2 = st.columns(2)
        with col1:
            years = sorted(data["agg_insurance"]["Years"].unique()) if not data["agg_insurance"].empty else [2023]
            selected_year = st.selectbox("Select Year", years, key="ins_year")
        with col2:
            quarters = sorted(data["agg_insurance"][data["agg_insurance"]["Years"] == selected_year]["Quarter"].unique()) if not data["agg_insurance"].empty else [1]
            selected_quarter = st.selectbox("Select Quarter", quarters, key="ins_quarter")

        if not data["agg_insurance"].empty:
            insurance_data = data["agg_insurance"][
                (data["agg_insurance"]["Years"] == selected_year) & 
                (data["agg_insurance"]["Quarter"] == selected_quarter)
            ]
            
            if not insurance_data.empty:
                insurance_summary = insurance_data.groupby("State").agg({
                    "Insurance_amount": "sum",
                    "Insurance_count": "sum"
                }).reset_index()
                insurance_summary["Amount_K"] = insurance_summary["Insurance_amount"] / 1e3
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🗺️ Insurance Coverage Heatmap")
                    fig = create_choropleth_map(
                        insurance_summary, 
                        "Amount_K", 
                        f"Insurance Amount - {selected_year} Q{selected_quarter}",
                        "Oranges",
                        "₹K"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("📈 Quarterly Growth Trend")
                    yearly_data = data["agg_insurance"][data["agg_insurance"]["Years"] == selected_year]
                    if not yearly_data.empty:
                        growth_trend = yearly_data.groupby("Quarter")["Insurance_amount"].sum().reset_index()
                        fig = px.line(
                            growth_trend, 
                            x="Quarter", 
                            y="Insurance_amount",
                            title="Insurance Growth by Quarter",
                            markers=True
                        )
                        fig.update_layout(height=400, yaxis=dict(tickformat=".2e"))
                        st.plotly_chart(fig, use_container_width=True)

    # Case Study 4: Market Expansion Strategy
    elif case_study == "🎯 Market Expansion Strategy":
        st.header("🎯 Market Expansion Strategy Analysis")
        st.markdown("**Objective**: Identify high-potential regions and growth opportunities for market expansion.")
        
        # Time Period Selection
        col1, col2 = st.columns(2)
        with col1:
            years = sorted(data["map_transaction"]["Years"].unique()) if not data["map_transaction"].empty else [2023]
            selected_year = st.selectbox("Select Year", years, key="exp_year")
        with col2:
            quarters = sorted(data["map_transaction"][data["map_transaction"]["Years"] == selected_year]["Quarter"].unique()) if not data["map_transaction"].empty else [1]
            selected_quarter = st.selectbox("Select Quarter", quarters, key="exp_quarter")

        if not data["map_transaction"].empty:
            expansion_data = data["map_transaction"][
                (data["map_transaction"]["Years"] == selected_year) & 
                (data["map_transaction"]["Quarter"] == selected_quarter)
            ]
            
            if not expansion_data.empty:
                expansion_summary = expansion_data.groupby("State").agg({
                    "Transaction_amount": "sum",
                    "Transaction_count": "sum"
                }).reset_index()
                expansion_summary["Amount_M"] = expansion_summary["Transaction_amount"] / 1e6
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🗺️ Market Penetration Heatmap")
                    fig = create_choropleth_map(
                        expansion_summary, 
                        "Amount_M", 
                        f"Market Penetration - {selected_year} Q{selected_quarter}",
                        "Reds",
                        "₹M"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("📊 Growth Opportunity Analysis")
                    # Calculate growth potential based on transaction density
                    expansion_summary["Growth_Score"] = (
                        expansion_summary["Transaction_amount"] / expansion_summary["Transaction_count"]
                    ).fillna(0)
                    
                    top_growth = expansion_summary.nlargest(10, "Growth_Score")
                    fig = create_bar_chart(
                        top_growth, 
                        "State", 
                        "Growth_Score",
                        "States with Highest Growth Potential"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

    # Case Study 5: User Growth Analysis
    elif case_study == "👥 User Growth Analysis":
        st.header("👥 User Growth Analysis")
        st.markdown("**Objective**: Analyze user registration patterns and engagement metrics for growth strategy.")
        
        # Time Period Selection
        col1, col2 = st.columns(2)
        with col1:
            years = sorted(data["map_user"]["Years"].unique()) if not data["map_user"].empty else [2023]
            selected_year = st.selectbox("Select Year", years, key="user_year")
        with col2:
            quarters = sorted(data["map_user"][data["map_user"]["Years"] == selected_year]["Quarter"].unique()) if not data["map_user"].empty else [1]
            selected_quarter = st.selectbox("Select Quarter", quarters, key="user_quarter")

        if not data["map_user"].empty:
            user_growth_data = data["map_user"][
                (data["map_user"]["Years"] == selected_year) & 
                (data["map_user"]["Quarter"] == selected_quarter)
            ]
            
            if not user_growth_data.empty:
                user_summary = user_growth_data.groupby("State").agg({
                    "RegisteredUsers": "sum",
                    "AppOpens": "sum"
                }).reset_index()
                user_summary["Users_K"] = user_summary["RegisteredUsers"] / 1e3
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("👥 User Distribution Heatmap") 
                    fig = create_choropleth_map(
                        user_summary, 
                        "Users_K", 
                        f"Registered Users - {selected_year} Q{selected_quarter}",
                        "Purples",
                        "K Users"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("📱 User Engagement Analysis")
                    # Calculate engagement rate
                    user_summary["Engagement_Rate"] = (
                        user_summary["AppOpens"] / user_summary["RegisteredUsers"]
                    ).fillna(0)
                    
                    top_engagement = user_summary.nlargest(10, "Engagement_Rate")
                    fig = create_bar_chart(
                        top_engagement, 
                        "State", 
                        "Engagement_Rate",
                        "States with Highest User Engagement"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

# ========================
# FOOTER
# ========================
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    **PhonePe Transaction Dashboard**
    
    This dashboard analyzes PhonePe transaction data to provide insights for business decision making.
    
    **Data Sources**: PhonePe Pulse GitHub Repository
    **Technology Stack**: Streamlit, Plotly, Pandas, MySQL
    """
)
