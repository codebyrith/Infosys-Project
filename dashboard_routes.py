"""
dashboard_routes.py
-------------------
Blueprint for dashboard, calculator, live market, simulator,
news, and settings pages.
"""

import requests as http_requests
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from models import (
    db,
    User,
    load_risk_results,
    load_investment_mixes,
    load_returns_summary,
    load_eta_summary,
    load_processed_prices,
    UserInvestment,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    risk_df = load_risk_results()
    mix_df = load_investment_mixes()
    returns_df = load_returns_summary()
    eta_df = load_eta_summary()

    risk_records = risk_df.to_dict("records") if not risk_df.empty else []
    mix_records = mix_df.to_dict("records") if not mix_df.empty else []
    user_investments = UserInvestment.query.filter_by(user_id=current_user.id).all()

    high_risk_count = len(risk_df[risk_df["risk_level"] == "HIGH"]) if not risk_df.empty else 0
    medium_risk_count = len(risk_df[risk_df["risk_level"] == "MEDIUM"]) if not risk_df.empty else 0
    low_risk_count = len(risk_df[risk_df["risk_level"] == "LOW"]) if not risk_df.empty else 0
    downward_count = len(risk_df[risk_df["trend"] == "DOWNWARD"]) if not risk_df.empty else 0
    total_cryptos = len(risk_df) if not risk_df.empty else 0

    best_score = round(mix_df["score"].max(), 4) if not mix_df.empty and "score" in mix_df.columns else "N/A"
    highest_return = round(eta_df["adjusted_eta_pct"].max(), 4) if not eta_df.empty and "adjusted_eta_pct" in eta_df.columns else "N/A"

    import json
    parsed_investments = []
    for inv in user_investments:
        data = json.loads(inv.crypto_data)
        parsed_investments.append({
            "id": inv.id,
            "total_amount": inv.total_amount,
            "timestamp": inv.timestamp,
            "data": data
        })

    return render_template(
        "dashboard.html",
        risk_data=risk_records,
        mix_data=mix_records,
        high_risk_count=high_risk_count,
        medium_risk_count=medium_risk_count,
        low_risk_count=low_risk_count,
        downward_count=downward_count,
        total_cryptos=total_cryptos,
        best_score=best_score,
        highest_return=highest_return,
        user_investments=parsed_investments,
    )


@dashboard_bp.route("/calculator")
@login_required
def calculator():
    mix_df = load_investment_mixes()
    mix_records = mix_df.to_dict("records") if not mix_df.empty else []
    return render_template("calculator.html", mix_data=mix_records)

from flask import redirect, url_for, flash
import json

@dashboard_bp.route("/invest", methods=["POST"])
@login_required
def invest():
    amount_str = request.form.get("amount", "0")
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.0

    if amount <= 0:
        flash("Please enter a valid amount.", "danger")
        return redirect(url_for('dashboard.calculator'))

    mix_df = load_investment_mixes()
    if mix_df.empty:
        flash("No investment mix available.", "warning")
        return redirect(url_for('dashboard.calculator'))

    # Get the top ranked allocation
    best_mix = mix_df.iloc[0].to_dict()
    crypto_data = {k.replace('_pct', ''): v for k, v in best_mix.items() if str(k).endswith('_pct')}

    new_invest = UserInvestment(
        user_id=current_user.id,
        total_amount=amount,
        crypto_data=json.dumps(crypto_data)
    )
    db.session.add(new_invest)
    db.session.commit()
    
    flash(f"Successfully invested ${amount:,.2f} in the best combination!", "success")
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route("/live-market")
@login_required
def live_market():
    return render_template("live_market.html")


@dashboard_bp.route("/simulator")
@login_required
def simulator():
    mix_df = load_investment_mixes()
    best_mix = {}
    if not mix_df.empty:
        top = mix_df.iloc[0]
        for col in mix_df.columns:
            if col.endswith("_pct"):
                name = col.replace("_pct", "")
                best_mix[name] = float(top[col])
    return render_template("simulator.html", best_mix=best_mix)


@dashboard_bp.route("/insights")
@login_required
def insights():
    return render_template("insights.html")


@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current_user.alert_high_risk = "alert_high_risk" in request.form
        current_user.alert_downward_trend = "alert_downward_trend" in request.form
        current_user.alert_daily_summary = "alert_daily_summary" in request.form
        db.session.commit()
        from flask import flash
        flash("Settings saved successfully.", "success")
    return render_template("settings.html")


# ── API: chart data ─────────────────────────────────────────────────
@dashboard_bp.route("/api/chart-data")
@login_required
def chart_data():
    risk_df = load_risk_results()
    mix_df = load_investment_mixes()
    eta_df = load_eta_summary()
    returns_df = load_returns_summary()

    risk_chart = {"labels": [], "levels": [], "etas": []}
    if not risk_df.empty:
        risk_chart["labels"] = risk_df["crypto_name"].tolist()
        risk_chart["levels"] = risk_df["risk_level"].tolist()
        risk_chart["etas"] = [round(v, 4) for v in risk_df["adjusted_eta"].tolist()]

    pie_chart = {"labels": [], "values": []}
    if not mix_df.empty:
        top = mix_df.iloc[0]
        for col in mix_df.columns:
            if col.endswith("_pct"):
                name = col.replace("_pct", "")
                val = float(top[col])
                if val > 0:
                    pie_chart["labels"].append(name)
                    pie_chart["values"].append(val)

    returns_chart = {"labels": [], "returns": [], "risks": []}
    if not mix_df.empty:
        returns_chart["labels"] = [f"Mix {int(r['rank'])}" for r in mix_df.to_dict("records")]
        returns_chart["returns"] = [round(r, 6) for r in mix_df["weighted_return"].tolist()]
        returns_chart["risks"] = [round(r, 6) for r in mix_df["weighted_risk"].tolist()]

    eta_chart = {"labels": [], "values": []}
    if not risk_df.empty:
        eta_chart["labels"] = risk_df["crypto_name"].tolist()
        eta_chart["values"] = [round(v, 4) for v in risk_df["adjusted_eta"].tolist()]

    # Performance comparison
    perf_chart = {"labels": [], "total_returns": [], "std_risks": [], "avg_returns": []}
    if not returns_df.empty:
        perf_chart["labels"] = returns_df["crypto_name"].tolist()
        perf_chart["total_returns"] = [round(r * 100, 2) for r in returns_df["total_return"].tolist()]
        perf_chart["std_risks"] = [round(r * 100, 2) for r in returns_df["std_daily_return"].tolist()]
        perf_chart["avg_returns"] = [round(r * 100, 4) for r in returns_df["average_daily_return"].tolist()]

    # ETA forecast data
    forecast = {"labels": [], "current": [], "future": []}
    if not eta_df.empty:
        forecast["labels"] = eta_df["crypto_name"].tolist()
        forecast["current"] = eta_df["current_price"].tolist()
        forecast["future"] = eta_df["estimated_future_price"].tolist()

    return jsonify(
        risk=risk_chart,
        pie=pie_chart,
        returns=returns_chart,
        eta=eta_chart,
        performance=perf_chart,
        forecast=forecast,
    )


# ── API: live crypto prices from CoinGecko ──────────────────────────
@dashboard_bp.route("/api/live-prices")
@login_required
def live_prices():
    try:
        resp = http_requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": "bitcoin,ethereum,binancecoin,solana,cardano,ripple,polkadot,dogecoin,avalanche-2,chainlink",
                "order": "market_cap_desc",
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
            timeout=15,
        )
        resp.raise_for_status()
        coins = resp.json()
        data = []
        for c in coins:
            data.append({
                "name": c.get("name", ""),
                "symbol": c.get("symbol", "").upper(),
                "image": c.get("image", ""),
                "price": c.get("current_price", 0),
                "change_24h": round(c.get("price_change_percentage_24h") or 0, 2),
                "market_cap": c.get("market_cap", 0),
                "volume": c.get("total_volume", 0),
            })
        return jsonify(success=True, data=data)
    except Exception as e:
        return jsonify(success=False, error=str(e), data=[])


# ── API: market insights ─────────────────────────────────────────────
@dashboard_bp.route("/api/insights")
@login_required
def market_insights():
    try:
        fng_resp = http_requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        fng_data = fng_resp.json().get("data", [{}])[0]
        
        trending_resp = http_requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10)
        trending_coins = trending_resp.json().get("coins", [])[:10]
        
        coins_data = []
        for item in trending_coins:
            coin = item.get("item", {})
            coins_data.append({
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "thumb": coin.get("thumb"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "price_btc": coin.get("price_btc")
            })

        data = {
            "fear_greed": {
                "value": fng_data.get("value", 50),
                "classification": fng_data.get("value_classification", "Neutral"),
                "timestamp": fng_data.get("timestamp")
            },
            "trending": coins_data
        }
        return jsonify(success=True, data=data)
    except Exception as e:
        return jsonify(success=False, error=str(e), data={})
