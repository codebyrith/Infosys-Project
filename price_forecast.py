import pandas as pd
import numpy as np
import sys
from sklearn.linear_model import LinearRegression

# Default to 30 days if not provided
days = 30
if len(sys.argv) > 1:
    try:
        days = int(sys.argv[1])
    except ValueError:
        pass

# Load historical price data
df = pd.read_csv("data/processed/processed_prices.csv")
df["date"] = pd.to_datetime(df["date"])


results = []

for crypto in df["crypto_name"].unique():
    crypto_df = df[df["crypto_name"] == crypto].sort_values("date").reset_index(drop=True)

    # Use day index as feature
    crypto_df["day_index"] = np.arange(len(crypto_df))
    X = crypto_df[["day_index"]]
    y = crypto_df["price"]

    # Train linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict price N days after the last date
    last_day = crypto_df["day_index"].iloc[-1]
    predicted_price = model.predict(pd.DataFrame({"day_index": [last_day + days]}))[0]

    last_date = crypto_df["date"].iloc[-1]
    forecast_date = last_date + pd.Timedelta(days=days)

    results.append({
        "crypto_name": crypto,
        "last_date": last_date.strftime("%Y-%m-%d"),
        "forecast_date": forecast_date.strftime("%Y-%m-%d"),
        "last_price": round(crypto_df["price"].iloc[-1], 2),
        "predicted_price": round(predicted_price, 2),
    })

    print(f"{crypto}: last={results[-1]['last_price']}, predicted={results[-1]['predicted_price']} on {forecast_date.date()}")

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv("data/processed/price_forecast.csv", index=False)
print("\nForecast saved to data/processed/price_forecast.csv")
