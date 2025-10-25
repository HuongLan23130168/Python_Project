from flask import Flask, jsonify, request
import requests
from datetime import datetime
from typing import Dict

app = Flask(__name__)

BASE = "https://api.exchangerate.host"


_cache = {}

def _cache_get(key):
    value = _cache.get(key)
    if value and datetime.utcnow().timestamp() - value["time"] < value["ttl"]:
        return value["data"]
    return None

def _cache_set(key, data, ttl_seconds=30):
    _cache[key] = {"data": data, "time": datetime.utcnow().timestamp(), "ttl": ttl_seconds}

# ---------- Hàm tiện ích chuyển đổi ----------
def convert(amount: float, from_cur: str, to_cur: str) -> Dict:
    """Chuyển đổi tiền tệ theo công thức: amount * rate."""
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Số tiền phải lớn hơn 0.")
    except ValueError:
        raise ValueError("Giá trị 'amount' phải là số dương hợp lệ.")

    if not from_cur or not to_cur:
        raise ValueError("Cần nhập đầy đủ mã tiền tệ nguồn và đích (VD: USD, VND).")

    from_cur = from_cur.upper().strip()
    to_cur = to_cur.upper().strip()

    key = f"convert:{from_cur}:{to_cur}:{amount}"

    cached = _cache_get(key)
    if cached:
        return cached

    url = f"{BASE}/latest"
    params = {"base": from_cur, "symbols": to_cur}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise ConnectionError(f"Lỗi khi gọi API tỷ giá: {e}")

    rates = data.get("rates", {})
    if to_cur not in rates:
        raise ValueError(f"Không tìm thấy tỷ giá cho {to_cur} trong phản hồi API.")

    rate = rates[to_cur]
    converted_amount = round(amount * rate, 2)

    result = {
        "from": from_cur,
        "to": to_cur,
        "rate": rate,
        "amount": amount,
        "converted_amount": converted_amount,
        "timestamp": data.get("date", str(datetime.utcnow().date()))
    }

    _cache_set(key, result, ttl_seconds=30)
    return result

# ---------- API Flask ----------
@app.route("/api/convert")
def convert_currency():
    """API Flask gọi lại hàm convert() để xử lý."""
    from_currency = request.args.get("from", "USD")
    to_currency = request.args.get("to", "VND")
    amount_str = request.args.get("amount", "1")

    try:
        result = convert(amount_str, from_currency, to_currency)
        return jsonify(result)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except ConnectionError as ce:
        return jsonify({"error": str(ce)}), 500
    except Exception as e:
        return jsonify({"error": f"Lỗi không xác định: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
