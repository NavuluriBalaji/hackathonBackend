import datetime
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from app.core.schema import DispensingLog, Inventory, Medicine, PHC

# Try importing Holt-Winters Exponential Smoothing from statsmodels
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

def forecast_phc_stockout(phc_id: str, medicine_id: str, db: Session, forecast_days: int = 7):
    """
    Holt-Winters Exponential Smoothing Forecasting Model:
    Models demand level, trend velocity, and 7-day weekly OPD seasonality cycles.
    Includes a recency-weighted exponential decay fallback for sparse datasets.
    """
    logs = db.query(DispensingLog).filter(
        DispensingLog.phc_id == phc_id,
        DispensingLog.medicine_id == medicine_id
    ).order_by(DispensingLog.timestamp.asc()).all()

    inv = db.query(Inventory).filter(
        Inventory.phc_id == phc_id,
        Inventory.medicine_id == medicine_id
    ).first()

    current_stock = inv.current_stock if inv else 100
    safety_threshold = inv.safety_threshold if inv else 200

    if not logs or len(logs) < 5:
        daily_rate = inv.avg_daily_consumption if inv else 20.0
        projected_curve = []
        for d in range(forecast_days + 1):
            units = max(0, int(current_stock - (daily_rate * d)))
            projected_curve.append({"t": f"T+{d*24}h", "day": d, "predicted_units": units})
        
        days_remaining = round(current_stock / max(1.0, daily_rate), 1)
        return {
            "phc_id": phc_id,
            "medicine_id": medicine_id,
            "model_type": "Baseline Constant Rate",
            "current_stock": current_stock,
            "safety_threshold": safety_threshold,
            "predicted_daily_velocity": daily_rate,
            "days_remaining": days_remaining,
            "risk_level": "CRITICAL" if days_remaining <= 3 else ("WARNING" if days_remaining <= 7 else "SAFE"),
            "predicted_stockout_breach_day": int(days_remaining) if days_remaining <= forecast_days else None,
            "depletion_curve": projected_curve
        }

    # Aggregate Daily Consumption
    data = [{"ds": l.timestamp.date(), "y": l.quantity} for l in logs]
    df = pd.DataFrame(data)
    df_daily = df.groupby("ds")["y"].sum().reset_index()

    predicted_daily_velocity = None
    model_name = "Holt-Winters Exponential Smoothing"

    # 1. Primary Model: Holt-Winters Exponential Smoothing (Trend + Weekly Seasonality)
    if HAS_STATSMODELS and len(df_daily) >= 14:
        try:
            # Fit Holt-Winters model with additive trend and 7-day seasonality
            hw_model = ExponentialSmoothing(
                df_daily["y"].values,
                trend="add",
                seasonal="add",
                seasonal_periods=7,
                initialization_method="estimated"
            ).fit()
            
            # Save fitted model to pickle file (.pkl)
            try:
                from app.core.model_persistence import save_model
                save_model(hw_model, f"holt_winters_{phc_id}_{medicine_id}.pkl")
            except Exception:
                pass

            # Predict future daily consumption values
            hw_predictions = hw_model.forecast(forecast_days)
            predicted_daily_velocity = float(max(5.0, np.mean(hw_predictions[:3])))
        except Exception:
            predicted_daily_velocity = None

    # 2. Fallback Model: Recency-Weighted Polynomial Trend Regression
    if predicted_daily_velocity is None:
        model_name = "Recency-Weighted Trend Regression"
        y = df_daily["y"].values
        weights = np.exp(np.linspace(-1.0, 0.0, len(y)))
        weights /= weights.sum()
        poly_coefficients = np.polyfit(np.arange(len(y)), y, deg=1, w=weights)
        predicted_daily_velocity = max(5.0, float(poly_coefficients[0] * len(y) + poly_coefficients[1]))

    # 3. Generate 7-Day Projected Stock Depletion Curve
    projected_curve = []
    stock_accumulator = float(current_stock)
    breach_day = None

    for d in range(forecast_days + 1):
        projected_curve.append({
            "t": f"T+{d*24}h",
            "day": d,
            "predicted_units": int(max(0, stock_accumulator))
        })
        
        if stock_accumulator <= safety_threshold and breach_day is None:
            breach_day = d
            
        stock_accumulator -= predicted_daily_velocity

    days_remaining = round(current_stock / max(1.0, predicted_daily_velocity), 1)
    risk_level = "CRITICAL" if days_remaining <= 3 else ("WARNING" if days_remaining <= 7 else "SAFE")

    return {
        "phc_id": phc_id,
        "medicine_id": medicine_id,
        "model_type": model_name,
        "current_stock": current_stock,
        "safety_threshold": safety_threshold,
        "predicted_daily_velocity": round(predicted_daily_velocity, 1),
        "days_remaining": days_remaining,
        "risk_level": risk_level,
        "predicted_stockout_breach_day": breach_day,
        "depletion_curve": projected_curve
    }
