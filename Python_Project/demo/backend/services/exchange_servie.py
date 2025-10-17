import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

BASE = "https://api.exchangerate.host"

# ---------- Simple tiny cache to avoid too many external calls ----------
_cache = {}

def _cache_set(key, value, ttl_seconds=300):
    _cache[key] = {"value": value, "expires": datetime.utcnow() + timedelta(seconds=ttl_seconds)}

def _cache_get(key):
    v = _cache.get(key)
    if not v: 
        return None
    if datetime.utcnow() > v["expires"]:
        del _cache[key]
        return None
    return v["value"]

# ---------- API helpers ----------
def get_symbols() -> Dict[str, Dict]:
    """Return symbols map: code -> {description, code}. Cached 1 hour."""
    key = "symbols"
    cached = _cache_get(key)
    if cached:
        return cached
    url = f"{BASE}/symbols"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    j = r.json()
    symbols = j.get("symbols", {})
    _cache_set(key, symbols, ttl_seconds=3600)
    return symbols

def convert(amount: float, from_cur: str, to_cur: str) -> Dict:
    """Convert using exchangerate.host convert endpoint. Cached short."""
    from_cur = from_cur.upper()
    to_cur = to_cur.upper()
    key = f"convert:{from_cur}:{to_cur}:{amount}"
    cached = _cache_get(key)
    if cached:
        return cached
    url = f"{BASE}/convert"
    params = {"from": from_cur, "to": to_cur, "amount": amount}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    j = r.json()
    _cache_set(key, j, ttl_seconds=30)  # small cache
    return j

def get_timeseries(base: str, target: str, start_date: str, end_date: str) -> pd.Series:
    """
    Return pandas Series indexed by date (datetime) of rate: target per base.
    start_date, end_date are 'YYYY-MM-DD'
    """
    base = base.upper()
    target = target.upper()
    # Use timeseries endpoint
    url = f"{BASE}/timeseries"
    params = {"start_date": start_date, "end_date": end_date, "base": base, "symbols": target}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    j = r.json()
    if not j.get("success", True):
        raise ValueError("API timeseries error")
    rates = j.get("rates", {})
    if not rates:
        return pd.Series(dtype=float)
    dates = sorted(rates.keys())
    vals = []
    idx = []
    for d in dates:
        v = rates[d].get(target)
        if v is None:
            vals.append(np.nan)
        else:
            vals.append(float(v))
        idx.append(pd.to_datetime(d))
    s = pd.Series(data=vals, index=idx)
    s = s.sort_index()
    return s

def analyze_trend(base: str, target: str, days: int = 90) -> Dict:
    """Return stats and daily series for last `days` days."""
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)
    s = get_timeseries(base, target, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    s = s.dropna()
    if s.empty:
        return {"stats": {}, "series": []}
    stats = {
        "start_date": s.index.min().strftime("%Y-%m-%d"),
        "end_date": s.index.max().strftime("%Y-%m-%d"),
        "count": int(s.count()),
        "min": float(s.min()),
        "max": float(s.max()),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "pct_change_total": float((s.iloc[-1] / s.iloc[0] - 1) * 100) if len(s) > 1 else 0.0,
        "moving_average_7": float(s.rolling(window=7, min_periods=1).mean().iloc[-1])
    }
    series = [{"date": d.strftime("%Y-%m-%d"), "rate": float(v)} for d, v in s.items()]
    return {"stats": stats, "series": series}

def predict_rate(base: str, target: str, days: int = 7, history_days: int = 180) -> List[Dict]:
    """
    Simple linear forecast using numpy.polyfit (degree=1).
    Returns list of {date, predicted_rate}.
    """
    end = datetime.utcnow().date()
    start = end - timedelta(days=history_days)
    s = get_timeseries(base, target, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    s = s.dropna()
    if len(s) < 6:
        raise ValueError("Không đủ dữ liệu lịch sử để dự đoán (cần ít nhất 6 ngày).")
    # X: integer days 0..n-1
    X = np.arange(len(s))
    y = s.values
    # Fit line y = a*x + b
    coef = np.polyfit(X, y, deg=1)  # [a, b]
    a, b = coef[0], coef[1]
    preds = []
    last_date = s.index[-1].date()
    for i in range(1, days + 1):
        di = last_date + timedelta(days=i)
        xi = len(s) + (i - 1)
        pred = a * xi + b
        preds.append({"date": di.strftime("%Y-%m-%d"), "predicted_rate": float(pred)})
    return preds