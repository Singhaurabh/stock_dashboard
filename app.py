import asyncio
import websockets
import json
import threading
import streamlit as st
import pandas as pd
import numpy as np
import time
import logger
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import QuantileRegressor

# UI SETUP ---
st.set_page_config(layout="wide")
st.title('Real-Time Crypto Order Book Simulator and Analytics using OKX Exchange')

with st.sidebar:
    exchange = st.selectbox("Exchange", ['OKX'])
    spot_asset = st.selectbox("Spot Asset", ['BTC-USDT-SWAP'])
    order_type = st.selectbox("Order Type", ['Market'])
    quantity_usd = st.number_input("Quantity (~USD)", min_value=1, value=100)
    volatility = st.selectbox("Volatility", ['Low', 'Medium', 'High'])
    fee_tier = st.selectbox("Fee Tier", ['Tier1 (Regular)', 'Tier2 (VIP)'])

placeholder = st.empty()
output_placeholder = st.empty()

orderbook_df = pd.DataFrame(columns=["Side", "Price", "Quantity"])
output_data = {}

# Almgren-Chriss parameters (example values)
gamma = 0.0002
eta = 0.000001

# Logistic regression model for Maker/Taker
# Feature vector: [volatility_encoded, fee_tier_encoded]
log_reg = LogisticRegression()
log_reg.coef_ = np.array([[1.5, -1.0]])
log_reg.intercept_ = np.array([0.2])
log_reg.classes_ = np.array([0, 1])

# Quantile regressor (mock) for slippage - Normally trained on historical data
quant_reg = QuantileRegressor(quantile=0.5, alpha=0.1)
quant_reg.coef_ = np.array([0.0003])
quant_reg.intercept_ = 0.01

## importing the logger file

from logger import log_latency_to_csv  # if saved separately

# Timing sections
start_time = time.time()
# processing... e.g., parsing data, updating DF
processing_latency = time.time() - start_time

# UI rendering(storing the start time of the  ui)
ui_start = time.time()
# calculating the ui latency
ui_latency = time.time() - ui_start
# calculating the total latency
total_latency = time.time() - start_time

# Log all
log_latency_to_csv(
    processing_latency * 1000,
    ui_latency * 1000,
    total_latency * 1000
)

# Encoding helpers
def encode_volatility(vol):
    mapping = {'Low': 0, 'Medium': 1, 'High': 2}
    return mapping.get(vol, 1)

def encode_fee_tier(tier):
    return 0 if 'Tier1' in tier else 1

# Model implementations
def almgren_chriss_impact(quantity):
    return gamma * quantity + eta * (quantity ** 2)

def quantile_slippage(quantity, volatility_encoded):
    # Mock implementation: intercept + coef * quantity adjusted by volatility - Bascially a formula for calculating the slippage
    base_slip = quant_reg.intercept_ + quant_reg.coef_[0] * quantity
    volatility_factor = 1 + 0.05 * volatility_encoded  # slight increase with volatility
    return max(base_slip * volatility_factor, 0)

def logistic_maker_taker(volatility_encoded, fee_tier_encoded):
    x = np.array([[volatility_encoded, fee_tier_encoded]])
    log_odds = np.dot(x, log_reg.coef_.T) + log_reg.intercept_
    prob = 1 / (1 + np.exp(-log_odds))
    return prob[0][0]

def calculate_expected_fees(quantity_usd, fee_tier):
    fee_rate = 0.001 if 'Tier1' in fee_tier else 0.0005
    return quantity_usd * fee_rate

def calculate_latency(start_time):
    return round((time.time() - start_time) * 1000, 2)  # ms

# WebSocket Handler
def run_websocket():
    uri = f"wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/{spot_asset}"

    async def connect():
        async with websockets.connect(uri) as websocket:
            # Latency Benchmarking
            # Data Processing Latency
            while True:
                start_time = time.time()
                msg = await websocket.recv()
                data = json.loads(msg)

                bids = pd.DataFrame(data['bids'], columns=["Price", "Quantity"]).astype(float)
                asks = pd.DataFrame(data['asks'], columns=["Price", "Quantity"]).astype(float)
                bids["Side"] = "Bid"
                asks["Side"] = "Ask"
                combined = pd.concat([bids, asks])

                global orderbook_df, output_data
                orderbook_df = combined

                vol_enc = encode_volatility(volatility)
                fee_enc = encode_fee_tier(fee_tier)

                #Model Processing

                slippage = quantile_slippage(quantity_usd, vol_enc)
                fees = calculate_expected_fees(quantity_usd, fee_tier)
                impact = almgren_chriss_impact(quantity_usd)
                maker_taker_ratio = logistic_maker_taker(vol_enc, fee_enc)
                latency = calculate_latency(start_time)
                net_cost = slippage + fees + impact

                proceesing_latency = time.time()-start_time
                #Data processing end's here

                output_data = {
                    "Expected Slippage": f"${slippage:.4f}",
                    "Expected Fees": f"${fees:.4f}",
                    "Market Impact": f"${impact:.4f}",
                    "Maker/Taker Proportion": f"{maker_taker_ratio:.2f}",
                    "Internal Latency": f"{latency} ms",
                    "Net Cost": f"${net_cost:.4f}"
                }


    asyncio.run(connect())

# Start WebSocket thread
threading.Thread(target=run_websocket, daemon=True).start()

# Display loop
while True:
    if not orderbook_df.empty:
        with placeholder.container():
            st.subheader("Real-Time Order Book (Top 10 Levels)")
            st.dataframe(orderbook_df.sort_values(by="Price", ascending=False).head(10), use_container_width=True)

        with output_placeholder.container():
            st.subheader("Calculated Metrics")
            for k, v in output_data.items():
                st.metric(label=k, value=v)
    time.sleep(1)
