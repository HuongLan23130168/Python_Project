from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# =======================
# 1️⃣ API: Xem các loại tiền tệ
# =======================
@app.route("/api/currencies")
def get_currencies():
    """
    Lấy danh sách tất cả các loại tiền tệ từ API open.er-api.com
    """
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD")
        data = response.json()
        currencies = list(data["rates"].keys())
        return jsonify({"currencies": currencies})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =======================
# 2️⃣ API: Chuyển đổi tiền tệ
# =======================
@app.route("/api/convert")
def convert_currency():
    """
    API: Chuyển đổi tiền tệ từ 'from' sang 'to' với số tiền 'amount'
    - Kiểm tra dữ liệu đầu vào (số âm, ký tự, rỗng,...)
    - Lấy tỷ giá thực tế từ API open.er-api.com
    - Tính toán theo công thức: result = round(amount * rate, 2)
    """

    # Lấy tham số đầu vào
    from_currency = request.args.get("from", "USD").upper().strip()
    to_currency = request.args.get("to", "VND").upper().strip()
    amount_str = request.args.get("amount", "1").strip()

    # Kiểm tra dữ liệu đầu vào
    if not from_currency or not to_currency:
        return jsonify({"error": "Vui lòng nhập mã tiền tệ nguồn và đích."}), 400

    # Kiểm tra giá trị amount hợp lệ
    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({"error": "Số tiền phải lớn hơn 0."}), 400
    except ValueError:
        return jsonify({"error": "Giá trị 'amount' phải là số hợp lệ."}), 400

    # Gọi API để lấy tỷ giá
    try:
        response = requests.get(f"https://open.er-api.com/v6/latest/{from_currency}", timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return jsonify({"error": f"Lỗi khi gọi API tỷ giá: {e}"}), 500

    # Kiểm tra dữ liệu API trả về
    if "rates" not in data or to_currency not in data["rates"]:
        return jsonify({"error": f"Không tìm thấy tỷ giá {from_currency} → {to_currency}."}), 404

    # Lấy tỷ giá và tính toán
    rate = data["rates"][to_currency]
    result = round(amount * rate, 2)

    # Trả kết quả JSON
    return jsonify({
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
        "rate": rate,
        "result": result,
        "timestamp": data.get("time_last_update_utc", str(datetime.utcnow()))
    })
# =======================
# 3️⃣ API: Phân tích xu hướng tiền tệ
# =======================
@app.route("/api/trend")
def analyze_trend():
    """
    Giả lập phân tích xu hướng 7 ngày qua của tỷ giá giữa base và target
    """
    base = request.args.get("base", "USD").upper()
    target = request.args.get("target", "VND").upper()

    try:
        # Lấy tỷ giá hiện tại
        response = requests.get(f"https://open.er-api.com/v6/latest/{base}")
        data = response.json()
        current_rate = data["rates"].get(target, 1.0)

        # Giả lập dữ liệu 7 ngày (dao động nhẹ ±2%)
        today = datetime.today()
        rates = []
        for i in range(7):
            date = (today - timedelta(days=6 - i)).strftime("%Y-%m-%d")
            fake_rate = round(current_rate * (1 + random.uniform(-0.02, 0.02)), 4)
            rates.append({"date": date, "rate": fake_rate})

        trend = "upward 📈" if rates[-1]["rate"] > rates[0]["rate"] else "downward 📉"

        return jsonify({
            "base": base,
            "target": target,
            "trend": trend,
            "data": rates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =======================
# 4️⃣ API: Dự đoán tỷ giá
# =======================
@app.route("/api/predict")
def predict_rate():
    """
    Dự đoán tỷ giá trong tương lai dựa vào dữ liệu hiện tại (giả lập ±3%)
    """
    base = request.args.get("base", "USD").upper()
    target = request.args.get("target", "VND").upper()

    try:
        response = requests.get(f"https://open.er-api.com/v6/latest/{base}")
        data = response.json()
        rate = data["rates"].get(target)

        if not rate:
            return jsonify({"error": f"Không tìm thấy tỷ giá {base} -> {target}"}), 404

        # Dự đoán tỷ giá ngẫu nhiên trong phạm vi ±3%
        predicted_rate = round(rate * (1 + random.uniform(-0.03, 0.03)), 4)
        confidence = random.choice(["Low", "Medium", "High"])

        return jsonify({
            "base": base,
            "target": target,
            "current_rate": rate,
            "predicted_rate": predicted_rate,
            "confidence": confidence
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =======================
# Run server
# =======================
if __name__ == "__main__":
    app.run(debug=True)