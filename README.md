# 📊 PhonePe Transaction Insights Dashboard — The Beat of Digital Payments

![PhonePe Banner](https://upload.wikimedia.org/wikipedia/commons/7/71/PhonePe_Logo.svg)

> **A fully interactive Streamlit dashboard analyzing India's digital transaction landscape using PhonePe Pulse data.**  
> Built with **Python**, **SQL**, **Plotly**, and **Streamlit** — this project delivers business insights through beautiful, data-driven visualizations.

---

## 🚀 Project Overview

With India's rapid adoption of **digital payments**, understanding transaction patterns, user engagement, and market growth areas is crucial.  
This dashboard connects to a MySQL database containing curated PhonePe Pulse data, enabling **real-time exploration** of:

- 📈 **Transaction Trends**
- 📱 **Device Usage Insights**
- 🛡 **Insurance Penetration & Growth**
- 🌏 **Geographic Payment Patterns**
- 🧩 **User Engagement Strategies**

---

## 🎯 Business Case Studies Implemented

This project delivers **five** detailed business case analyses from the PhonePe dataset:

1. **Decoding Transaction Dynamics**  
   Explore variations across states, quarters, and payment types to design targeted growth strategies.

2. **Device Dominance & User Engagement**  
   Understand which device brands dominate and how that impacts app usage across regions.

3. **Insurance Penetration & Growth Potential**  
   Identify untapped insurance markets and monitor growth trends.

4. **Transaction Analysis for Market Expansion**  
   Spot high-potential states/districts for PhonePe’s future expansion.

5. **User Engagement & Growth Strategy**  
   Compare app opens vs. registered users to measure engagement levels.

---

## 🛠 Tech Stack

- **Backend / Data Layer:** MySQL + SQLAlchemy  
- **Frontend / Dashboard:** Streamlit  
- **Data Analysis & Viz:** Pandas, Plotly (Express + Graph Objects)  
- **Geo Mapping:** Custom India GeoJSON integration  
- **ETL:** Python scripts + SQL queries for data extraction and transformation  

---

## 📂 Project Structure

```
📦 phonepe-pulse-dashboard
├── app1.py                 # Main Streamlit dashboard code
├── phonepe_analysis.ipynb  # Python analysis & preprocessing
├── pysql.ipynb              # SQL queries & data extraction
├── Business Case Study.pdf # Original case study prompts
├── 1st_PhonePay.pdf         # Project specification & guidelines
├── Indian_States.geojson   # Map boundaries for visualization
└── README.md               # This file
```

---

## 🔍 Key Features

- **Dynamic Filters:** Switch between years & quarters to see real-time data updates.
- **Interactive Maps:** Choropleth visualizations for state-wise metrics.
- **Top N Insights:** Instantly see top-performing states, districts, or device brands.
- **Time Series Trends:** Transaction & insurance growth over time.
- **Responsive Layout:** Optimized for desktop and large screens.

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository
```bash
!git clone https://github.com/PhonePe/pulse.git
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Prepare the Database
- Install MySQL and create a database named `phonepe_db`.
- Import your processed PhonePe data into relevant tables:
  - `aggregated_transaction`
  - `aggregated_insurance`
  - `aggregated_user`
  - `map_transaction`
  - `map_insurance`
  - `map_user`
  - `top_transaction`
  - `top_insurance`
  - `top_user`

### 4️⃣ Run the Dashboard
```bash
streamlit run app1.py
```
---

## 💡 Insights Gained

- **Seasonal patterns** in transaction spikes (festive quarters dominate).  
- **Brand affinity** — certain devices dominate usage in specific states.  
- **Insurance adoption gap** — large opportunities in underpenetrated states.  
- **High-growth clusters** for market expansion.

---

## 👨‍💻 Author

**Deepak Manian**  
📍 India  
💌 Reach me: [LinkedIn]() • [Email](deepsdpak@gmail.com)

---

## ⭐ Acknowledgements

- [PhonePe Pulse](https://www.phonepe.com/pulse/) for open transaction data.  
- [Streamlit](https://streamlit.io/) for making dashboards fun & fast.  
- [Plotly](https://plotly.com/) for interactive visualizations.

---

> If you like this project, **give it a ⭐ on GitHub** — it motivates me to create more awesome projects like this!
