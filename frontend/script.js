// ========== Hàm khởi tạo ==========
document.addEventListener("DOMContentLoaded", async () => {
  await loadCurrencies();
});

// ========== Hàm tải danh sách tiền tệ ==========
async function loadCurrencies() {
  try {
    const response = await fetch("http://127.0.0.1:5000/api/currencies");
    const data = await response.json();

    const selects = ["from", "to", "trend-base", "trend-target", "predict-base", "predict-target"];
    selects.forEach(id => {
      const select = document.getElementById(id);
      select.innerHTML = "";
      for (const code of data.currencies) {
        const option = document.createElement("option");
        option.value = code;
        option.textContent = code;
        select.appendChild(option);
      }
    });
  } catch (error) {
    console.error("Lỗi tải danh sách tiền tệ:", error);
  }
}


const API_URL = "http://127.0.0.1:5000/api";

window.onload = async function () {
  await loadCurrencies();
};

// async function loadCurrencies() {
//   try {
//     const response = await fetch(`${API_URL}/currencies`);
//     const data = await response.json();
//     const currencies = data.currencies;

//     const selects = ["from", "to", "trend-base", "trend-target", "predict-base", "predict-target"];
//     selects.forEach((id) => {
//       const select = document.getElementById(id);
//       select.innerHTML = currencies.map((c) => `<option value="${c}">${c}</option>`).join("");
//     });
//   } catch (error) {
//     console.error("❌ Lỗi khi tải danh sách tiền:", error);
//   }
// }

async function convert() {
  const amount = document.getElementById("amount").value;
  const from = document.getElementById("from").value;
  const to = document.getElementById("to").value;

  if (!amount) return alert("Vui lòng nhập số tiền!");

  const response = await fetch(`${API_URL}/convert?from=${from}&to=${to}&amount=${amount}`);
  const data = await response.json();

  document.getElementById("convert-result").innerText = 
    data.result ? `${amount} ${from} = ${data.result} ${to}` : `❌ ${data.error}`;
}

async function getCurrencies() {
  const res = await fetch(`${API_URL}/currencies`);
  const data = await res.json();
  const list = document.getElementById("currency-list");
  list.innerHTML = "";
  data.currencies.forEach(c => {
    const li = document.createElement("li");
    li.textContent = c;
    list.appendChild(li);
  });
}

async function getTrend() {
  const base = document.getElementById("trend-base").value;
  const target = document.getElementById("trend-target").value;
  const res = await fetch(`${API_URL}/trend?base=${base}&target=${target}`);
  const data = await res.json();

  let html = `<p>Xu hướng: <b>${data.trend}</b></p>`;
  html += "<table border='1'><tr><th>Ngày</th><th>Tỷ giá</th></tr>";
  data.data.forEach(d => html += `<tr><td>${d.date}</td><td>${d.rate}</td></tr>`);
  html += "</table>";
  document.getElementById("trend-result").innerHTML = html;
}

async function predictRate() {
  const base = document.getElementById("predict-base").value;
  const target = document.getElementById("predict-target").value;
  const res = await fetch(`${API_URL}/predict?base=${base}&target=${target}`);
  const data = await res.json();
  document.getElementById("predict-result").innerText =
    `Dự đoán: 1 ${base} ≈ ${data.predicted_rate} ${target} (Độ tin cậy: ${data.confidence})`;
}

