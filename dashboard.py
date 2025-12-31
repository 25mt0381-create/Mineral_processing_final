import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from datetime import timedelta
from math import sqrt
from sklearn.metrics import mean_squared_error
import numpy as np
import warnings
import os
warnings.filterwarnings("ignore")

# ==========================================
# 1. PAGE SETUP
# ==========================================
st.set_page_config(page_title="Critical Mineral Dashboard", layout="wide")
st.title("Indian Critical Mineral Intelligence Dashboard ($)")
st.caption("Granularity: Month-Wise | Data Cutoff: September 2025")

# CONFIGURATION (Your specific paths)
curr_dir= os.getcwd()
base_file = os.path.join(curr_dir, "data", "transformed", "consolidated_all_hscodes.xlsx")
mapping_file = os.path.join(curr_dir, "data", "hscodes", "cleaned_HS_Codes_for_processing.xlsx")

# ==========================================
# 2. DATA LOADING
# ==========================================
@st.cache_data
def load_data():
    try:
        # Load Main Data
        df = pd.read_excel(base_file)
        df['Date_Parsed'] = pd.to_datetime(df['Date'], format='%b-%Y')
        
        # --- CUTOFF FILTER (Sept 2025) ---
        df = df[df['Date_Parsed'] <= "2025-09-30"]
        
        # Load Mapping
        map_df = pd.read_excel(mapping_file)
        map_df.columns = map_df.columns.str.strip()
        
        # Check if required columns exist in mapping file
        if 'HSCode' not in map_df.columns:
            raise KeyError(f"'HSCode' column not found in mapping file. Available columns: {list(map_df.columns)}")
        if 'Element respective' not in map_df.columns:
            raise KeyError(f"'Element respective' column not found in mapping file. Available columns: {list(map_df.columns)}")
        
        hs_code_map = dict(zip(map_df['HSCode'], map_df['Element respective']))
        
        # Check if HSCode column exists in base file
        if 'HSCode' not in df.columns:
            raise KeyError(f"'HSCode' column not found in base data file. Available columns: {list(df.columns)}")
        
        # Apply Map
        df['Mineral'] = df['HSCode'].map(hs_code_map)
        df = df[df['Mineral'].notna()]
        
        return df.sort_values('Date_Parsed')
    except KeyError as e:
        st.error(f"Column Error: {e}")
        st.info(f"Base file: {base_file}")
        st.info(f"Mapping file: {mapping_file}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading files: {e}")
        st.info(f"Base file: {base_file}")
        st.info(f"Mapping file: {mapping_file}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

df = load_data()

# Add cache clear button for debugging
if st.sidebar.button("🔄 Clear Cache & Reload Data"):
    st.cache_data.clear()
    st.rerun()

if not df.empty:
    # ==========================================
    # 3. SIDEBAR CONTROLS
    # ==========================================
    st.sidebar.header("Filters")
    mineral = st.sidebar.selectbox("Select Mineral", df['Mineral'].unique())

    # Filter Data for Selection
    mineral_df = df[df['Mineral'] == mineral]
    
    # Enforce Month-Wise Granularity (Sum duplicates, fill missing months with 0)
    # This ensures we have a continuous monthly timeline
    monthly_import = mineral_df[mineral_df['Type'] == 'Import'].set_index('Date_Parsed')['Value'].resample('MS').sum().fillna(0)
    monthly_export = mineral_df[mineral_df['Type'] == 'Export'].set_index('Date_Parsed')['Value'].resample('MS').sum().fillna(0)

    # ==========================================
    # 4. MAIN TABS
    # ==========================================
    tab1, tab2, tab3 = st.tabs(["📈 Market Analysis", "📊 Monthly Data View", "🤖 AI Forecasting (Optimized)"])

    # --- TAB 1: MARKET ANALYSIS ---
    with tab1:
        st.subheader(f"{mineral} Trade Overview")
        
        # Top Level Metrics
        imp_total = monthly_import.sum()
        exp_total = monthly_export.sum()
        dep_ratio = (imp_total / (imp_total + exp_total)) * 100 if (imp_total + exp_total) > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Imports", f"$ {imp_total:,.0f} Millions")
        c2.metric("Total Exports", f"$ {exp_total:,.0f} Millions")
        c3.metric("Dependency Ratio", f"{dep_ratio:.1f}%", help="Imports / Total Trade")
        
        # Combined Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_import.index, y=monthly_import, mode='lines+markers', name='Imports', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=monthly_export.index, y=monthly_export, mode='lines+markers', name='Exports', line=dict(color='orange')))
        
        fig.update_layout(title=f"Month-Wise Trade Trends ({mineral})", 
                          xaxis_title="Date", yaxis_title="Value Millions (USD $)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: MONTHLY DATA TABLE ---
    with tab2:
        st.subheader("Month-Wise Granular Data")
        st.markdown("Detailed breakdown of trade values for every month.")
        
        # Combine into a clean table
        combined_df = pd.DataFrame({
            'Imports Million ($)': monthly_import, 
            'Exports Million ($)': monthly_export
        })
        
        # Add a Net Trade Column
        combined_df['Net Trade Balance'] = combined_df['Exports Million ($)'] - combined_df['Imports Million ($)']
        
        # Sort newest first
        st.dataframe(combined_df.sort_index(ascending=False).style.format("$ {:,.0f}"), use_container_width=True)
        
        # Download Option
        csv = combined_df.to_csv().encode('utf-8')
        st.download_button("Download Monthly Data (CSV)", csv, f"{mineral}_monthly_data.csv", "text/csv")

    # --- TAB 3: AI FORECASTING (CHAMPION/CHALLENGER) ---
    with tab3:
        st.subheader("12-Month Import Forecast")
        st.caption("Automatically selecting the best model (ARIMA vs Holt-Winters) based on accuracy.")
        
        if len(monthly_import) > 12:
            with st.spinner("Running Model Tournament..."):
                # 1. Split Train/Test (Hidden 6 months)
                train = monthly_import[:-6]
                test = monthly_import[-6:]
                
                # --- MODEL A: ARIMA ---
                try:
                    model_a = ARIMA(train, order=(5,1,0))
                    fit_a = model_a.fit()
                    pred_a = fit_a.forecast(steps=6)
                    rmse_a = sqrt(mean_squared_error(test, pred_a))
                except:
                    rmse_a = float('inf')

                # --- MODEL B: HOLT-WINTERS ---
                try:
                    model_b = ExponentialSmoothing(train, trend='add', seasonal=None, damped_trend=True)
                    fit_b = model_b.fit()
                    pred_b = fit_b.forecast(steps=6)
                    rmse_b = sqrt(mean_squared_error(test, pred_b))
                except:
                    rmse_b = float('inf')
                
                # 2. Pick Winner & Retrain on FULL Data
                if rmse_a < rmse_b:
                    winner = "ARIMA (5,1,0)"
                    error_score = rmse_a
                    
                    final_model = ARIMA(monthly_import, order=(5,1,0))
                    final_fit = final_model.fit()
                    forecast = final_fit.forecast(steps=12)
                else:
                    winner = "Holt-Winters (Exp. Smoothing)"
                    error_score = rmse_b
                    
                    final_model = ExponentialSmoothing(monthly_import, trend='add', seasonal=None, damped_trend=True)
                    final_fit = final_model.fit()
                    forecast = final_fit.forecast(steps=12)

                # 3. Calculate MAPE
                non_zero_test = test[test != 0]
                # We need the predictions from the winning model for the test period to calculate MAPE correctly
                if winner == "ARIMA (5,1,0)":
                    winner_test_preds = pred_a
                else:
                    winner_test_preds = pred_b
                    
                non_zero_pred = winner_test_preds[test != 0]
                
                mape = (abs((non_zero_test - non_zero_pred) / non_zero_test).mean()) * 100 if len(non_zero_test) > 0 else 0.0

            # 4. Display Results
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.success(f"🏆 Winning Model: {winner}")
            col_res2.metric("RMSE (Error Margin)", f"{error_score:,.2f}")
            col_res3.metric("MAPE (Error %)", f"{mape:.2f}%")
            
            # 5. Plot Forecast
            future_dates = [monthly_import.index[-1] + timedelta(days=30*i) for i in range(1, 13)]
            
            fig2 = go.Figure()
            # Historical Data
            fig2.add_trace(go.Scatter(x=monthly_import.index, y=monthly_import, mode='lines', name='Historical', line=dict(color='gray')))
            # Forecast Data
            fig2.add_trace(go.Scatter(x=future_dates, y=forecast, mode='lines+markers', name='Forecast', line=dict(color='green', width=3)))
            
            fig2.update_layout(title=f"AI Prediction for {mineral} (Next 12 Months)", yaxis_title="Imports Million (USD $)")
            st.plotly_chart(fig2, use_container_width=True)
            
        else:
            st.warning("Not enough data to run the AI Tournament (Need 12+ months).")