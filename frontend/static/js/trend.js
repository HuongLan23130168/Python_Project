const API_URL = "http://127.0.0.1:8000/api";
let chart;

/* ================== LOAD CURRENCIES ================== */
async function loadCurrencies() {
    const res = await fetch(`${API_URL}/currencies`);
    const data = await res.json();

    setupDropdown("baseSelect", data.currencies, "USD");
    setupDropdown("targetSelect", data.currencies, "VND");
}

/* ================== LOAD TREND ================== */
async function loadTrend() {
    const base = getSelected("baseSelect");
    const target = getSelected("targetSelect");

    const res = await fetch(
        `${API_URL}/trend/?base=${base}&target=${target}`
    );
    const data = await res.json();

    if (data.error) {
        console.error(data.error);
        return;
    }

    // Update label
    const label = document.getElementById("trendLabel");
    const percent = document.getElementById("trendPercent");

    label.innerText = data.trend_label;
    percent.innerText = `${data.change_percent}%`;

    label.className = "";
    if (data.change_percent > 0.5) label.classList.add("trend-up");
    else if (data.change_percent < -0.5) label.classList.add("trend-down");
    else label.classList.add("trend-stable");

    renderChart(data.data);
}

/* ================== RENDER CHART ================== */
function renderChart(dataset) {
    const ctx = document.getElementById("trendChart").getContext("2d");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: dataset.map(d => d.date),
            datasets: [{
                data: dataset.map(d => d.rate),
                borderColor: "#6d8bff",
                backgroundColor: "transparent",
                borderWidth: 3,
                tension: 0.35,
                pointRadius: 4,
                fill: false
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 7,
                        color: "#aaa"
                    },
                    grid: { display: false }
                },
                y: {
                    ticks: { color: "#aaa" },
                    grid: { color: "rgba(255,255,255,0.08)" }
                }
            }
        }
    });
}

/* ================== CUSTOM DROPDOWN ================== */
function setupDropdown(id, currencies, defaultValue) {
    const wrap = document.getElementById(id);

    wrap.innerHTML = `
        <div class="select-box" onclick="toggleList('${id}')">
            <div class="selected">
                <span class="code">${defaultValue}</span>
            </div>
            ▼
        </div>
        <div class="dropdown-list"></div>
    `;

    const list = wrap.querySelector(".dropdown-list");

    currencies.forEach(code => {
        const item = document.createElement("div");
        item.className = "dropdown-item";
        item.innerHTML = `<span>${code}</span>`;
        item.onclick = () => {
            selectOption(id, code);
            loadTrend();
        };
        list.appendChild(item);
    });
}

function toggleList(id) {
    document.querySelectorAll(".dropdown-list")
        .forEach(l => l.style.display = "none");

    const list = document.querySelector(`#${id} .dropdown-list`);
    list.style.display = list.style.display === "block" ? "none" : "block";
}

function selectOption(id, code) {
    document.querySelector(`#${id} .selected`).innerHTML =
        `<span class="code">${code}</span>`;
    document.querySelector(`#${id} .dropdown-list`).style.display = "none";
}

function getSelected(id) {
    return document.querySelector(`#${id} .code`).innerText;
}

function toggleTheme() {
    document.body.classList.toggle("light");
}

document.addEventListener("click", e => {
    if (!e.target.closest(".custom-select")) {
        document.querySelectorAll(".dropdown-list")
            .forEach(l => l.style.display = "none");
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    await loadCurrencies();
    await loadTrend();
});
