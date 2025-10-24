from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# === HÀM LẤY TỶ GIÁ TỪ API ===
def get_exchange_rates(base_currency="USD"):
    """Lấy tỉ giá tiền tệ từ open.er-api.com theo đồng tiền cơ sở."""
    url = f"https://open.er-api.com/v6/latest/{base_currency.upper()}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            return data
    except requests.RequestException as e:
        print("Lỗi khi gọi API:", e)
    return None


# === HÀM LẤY DANH SÁCH MÃ TIỀN TỆ ===
def get_all_currency_codes():
    """Lấy danh sách tất cả mã tiền tệ từ API"""
    data = get_exchange_rates("USD")
    if not data:
        return {}
    rates = data.get("rates", {})
    return {code: code for code in rates.keys()}


# === TRANG WEB CÓ FORM + HIỂN THỊ KẾT QUẢ ===
@app.route("/", methods=["GET", "POST"])
def home():
    currencies = get_all_currency_codes()
    result = None

    if request.method == "POST":
        from_currency = request.form.get("from").upper()
        to_currency = request.form.get("to").upper()
        amount = float(request.form.get("amount"))

        data = get_exchange_rates(from_currency)
        if data and to_currency in data["rates"]:
            rate = data["rates"][to_currency]
            converted = amount * rate
            result = f"{amount:,.2f} {from_currency} = {converted:,.2f} {to_currency}"
        else:
            result = "Không thể lấy dữ liệu chuyển đổi."

    html = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>🌍 Chuyển đổi tiền tệ</title>
        <link rel="stylesheet"
              href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="bg-light">
        <div class="container mt-5 p-4 bg-white rounded shadow" style="max-width: 600px;">
            <h2 class="text-center mb-4 text-primary">🌍 Chuyển đổi tiền tệ</h2>

            <form method="POST">
                <div class="mb-3">
                    <label for="from" class="form-label">Từ tiền tệ:</label>
                    <select class="form-select" name="from" id="from" required>
                        {% for code, name in currencies.items() %}
                            <option value="{{ code }}" {% if request.form.get('from') == code %}selected{% endif %}>{{ code }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="mb-3">
                    <label for="to" class="form-label">Sang tiền tệ:</label>
                    <select class="form-select" name="to" id="to" required>
                        {% for code, name in currencies.items() %}
                            <option value="{{ code }}" {% if request.form.get('to') == code %}selected{% endif %}>{{ code }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="mb-3">
                    <label for="amount" class="form-label">Số tiền:</label>
                    <input type="number" step="0.01" min="0" class="form-control" id="amount" name="amount" 
                           value="{{ request.form.get('amount', '') }}" required>
                </div>

                <div class="text-center">
                    <button type="submit" class="btn btn-primary px-4">Chuyển đổi</button>
                </div>
            </form>

            {% if result %}
                <div class="alert alert-info text-center mt-4 fw-bold fs-5">
                    💵 {{ result }}
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, currencies=currencies, result=result)


if __name__ == "__main__":
    app.run(debug=True)
