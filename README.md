"# stock_dashboard" 
1.---------------------------------------------------------------------------------------------------------------------------
# Model Selection and Parameters
This project implements three core models:

## A. Almgren-Chriss Market Impact Model
Purpose: The Almgren-Chriss model is a foundational tool in quantitative finance for estimating the cost of executing large trades. When a trader attempts to buy or sell a significant quantity of a security, the act of trading itself impacts the price.

The model helps quantify how much a trade will move the market price, enabling traders and portfolio managers to:
-Optimize execution strategies
-Minimize slippage
-Reduce transaction costs

Formula Used:

Impact=γ⋅Q+η⋅Q^^2
 
where:
Q: Trade size (USD equivalent)
γ: Temporary impact coefficient (linear term)
η: Permanent impact coefficient (quadratic term)

Parameters Chosen:
γ=0.0002
η=0.000001
These values are illustrative and can be tuned using historical L2 market data.

Why we use this model?

-It mathematically models market impact in a realistic, interpretable way.
-It’s widely used in institutional trading and high-frequency strategies.
-It offers a clear method to incorporate execution cost into trading and portfolio decisions.
2.---------------------------------------------------------------------------------------------------------------------------------------------------
## B. Regression Techniques Chosen
A. Quantile Regression (for Slippage Estimation)
Why Quantile Regression?

Captures the distribution of slippage under varying volatility/market conditions.
More robust to outliers than linear regression.

Model Assumptions:
Input Feature: order size
Target: Estimated slippage in USD
Volatility-adjusted using an external encoding function

Mock Parameters Used:
QuantileRegressor(quantile=0.5, alpha=0.1)
coef_ = [0.0003]
intercept_ = 0.01

B. Logistic Regression (for Maker/Taker Trade Classification)
Why Logistic Regression?

Fast binary classification model
Outputs the probability of a trade being Maker or Taker

Features Used:

Volatility (encoded as 0, 1, 2)
Fee Tier (encoded as 0 for Tier1, 1 for Tier2)

Mock Parameters Used:
coef_ = [[1.5, -1.0]]
intercept_ = [0.2]
classes_ = [0, 1]
3. ------------------------------------------------------------------------------------------------------------------------------------------------
## C. Market Impact Calculation Methodology
The Almgren-Chriss model is at the heart of the impact calculation.

How it's calculated in code:

def almgren_chriss_impact(quantity):
    return gamma * quantity + eta * (quantity ** 2)

The market impact rises linearly and quadratically with the trade size.
Captures price movement risk and liquidity drag due to aggressive orders.
Tradeoffs modeled: faster execution = higher impact.
This is especially useful in execution algorithms, high-frequency trading, or institutional trading desks.
4.---------------------------------------------------------------------------------------------------------------------------------------------------
## Performance Optimization Approaches
The system is designed to be real-time and efficient, using the following techniques:

A. Memory Management
Streamlit elements use st.empty() placeholders to reuse UI containers, avoiding memory bloat.
Pandas DataFrames are cleared and overwritten every tick (no data stacking).

B. Network Communication
Asynchronous WebSocket client using asyncio ensures non-blocking real-time data handling.
Socket runs in a background thread, isolating it from Streamlit’s event loop.

C. Data Structures
Pandas DataFrames for structured order book data
Dictionaries for metrics → easily serialized and displayed via st.metric()

D. Thread Management
WebSocket runs in a separate daemon thread to avoid freezing Streamlit’s UI thread.
Ensures UI remains responsive even during network lag.

E. Model Efficiency
Lightweight models:

Quantile regression and logistic regression are single-step, vectorized
No large model loading or external dependencies
No need for real-time re-training

F. Latency Benchmarking
Captured using three timers:

Processing latency: Time to parse + compute models
UI update latency: Time to prepare and render metrics   
Total latency: End-to-end WebSocket → UI cycle

