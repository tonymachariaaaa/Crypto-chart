import json
import time
import threading
import urllib.request
import urllib.parse
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from collections import deque

HOST = "127.0.0.1"
PORT = 8080

COINS = [
    ("bitcoin", "BTC", "Bitcoin"),
    ("ethereum", "ETH", "Ethereum"),
    ("solana", "SOL", "Solana"),
    ("binancecoin", "BNB", "BNB"),
    ("ripple", "XRP", "XRP"),
    ("dogecoin", "DOGE", "Dogecoin"),
    ("the-open-network", "TON", "Toncoin"),
    ("cardano", "ADA", "Cardano"),
]

messages = deque(maxlen=200)
messages_lock = threading.Lock()

market = {"data": [], "updated": 0, "error": None}
market_lock = threading.Lock()


def fetch_prices():
    ids = ",".join(c[0] for c in COINS)
    query = urllib.parse.urlencode({
        "ids": ids,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    })

    url = (
        "https://api.coingecko.com/api/v3/simple/price?"
        + query
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CryptoPulse/1.0"}
    )

    with urllib.request.urlopen(request, timeout=12) as response:
        raw = json.loads(response.read().decode("utf-8"))

    result = []

    for coin_id, symbol, name in COINS:
        item = raw.get(coin_id, {})

        result.append({
            "id": coin_id,
            "symbol": symbol,
            "name": name,
            "price": item.get("usd"),
            "change": item.get("usd_24h_change")
        })

    return result


def market_worker():
    while True:
        try:
            data = fetch_prices()

            with market_lock:
                market["data"] = data
                market["updated"] = time.time()
                market["error"] = None

        except Exception as exc:
            with market_lock:
                market["error"] = str(exc)

        time.sleep(60)


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#080d18">

<title>CryptoPulse | Crypto Markets</title>

<style>
:root {
    color-scheme: dark;
    --bg: #080d18;
    --panel: #111a2a;
    --line: #27354b;
    --text: #edf3ff;
    --muted: #93a2ba;
    --green: #27d99a;
    --red: #ff647c;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font: 15px Arial, sans-serif;
}

header {
    background: #0c1322;
    border-bottom: 1px solid var(--line);
    padding: 15px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}

.logo {
    font-size: 23px;
    font-weight: bold;
}

.logo span {
    color: var(--green);
}

nav {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

nav button {
    background: transparent;
    color: var(--muted);
    border: 1px solid transparent;
    padding: 9px;
    cursor: pointer;
    border-radius: 7px;
}

nav button.active,
nav button:hover {
    background: #1a2940;
    color: white;
}

main {
    max-width: 1150px;
    margin: auto;
    padding: 22px 14px;
}

h1 {
    font-size: clamp(28px, 5vw, 43px);
    letter-spacing: -1px;
}

h1 span {
    color: var(--green);
}

h2 {
    font-size: 21px;
}

p {
    line-height: 1.6;
}

.muted {
    color: var(--muted);
}

.green {
    color: var(--green);
}

.red {
    color: var(--red);
}

.grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 20px 0;
}

.card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 15px;
    min-width: 0;
}

.price {
    font-size: 23px;
    font-weight: bold;
    margin: 12px 0 5px;
    overflow-wrap: anywhere;
}

button,
input,
select {
    font: inherit;
}

input,
select {
    background: #0a1220;
    color: white;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 11px;
    min-width: 0;
}

input {
    width: 100%;
}

.action {
    border: 0;
    background: var(--green);
    color: #06130e;
    font-weight: bold;
    border-radius: 8px;
    padding: 11px 14px;
    cursor: pointer;
}

.secondary {
    background: #233149;
    color: white;
    border: 1px solid #354761;
}

.tools {
    display: flex;
    gap: 10px;
    margin: 15px 0;
}

.tools input {
    flex: 1;
}

.tablewrap {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    white-space: nowrap;
}

th,
td {
    text-align: left;
    padding: 13px 10px;
    border-bottom: 1px solid var(--line);
}

th {
    color: var(--muted);
    font-size: 12px;
}

.chat {
    height: 330px;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.message {
    padding: 10px;
    border: 1px solid var(--line);
    background: #101b2b;
    border-radius: 9px;
    overflow-wrap: anywhere;
}

.message b {
    color: #a9bbff;
}

.message small {
    color: var(--muted);
    margin-left: 8px;
}

.composer {
    display: grid;
    grid-template-columns: 110px 1fr auto;
    gap: 8px;
    border-top: 1px solid var(--line);
    padding: 12px;
}

.chart {
    width: 100%;
    height: 260px;
    display: block;
}

.stat {
    padding: 12px 0;
    border-bottom: 1px solid var(--line);
}

footer {
    text-align: center;
    color: var(--muted);
    padding: 25px 10px;
    font-size: 12px;
}

@media(max-width: 750px) {
    .grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .composer {
        grid-template-columns: 1fr auto;
    }

    .composer .username {
        grid-column: 1 / -1;
    }

    .composer .messagebox {
        grid-column: 1;
    }

    .composer button {
        grid-column: 2;
    }
}

@media(max-width: 360px) {
    .grid {
        grid-template-columns: 1fr;
    }

    .composer {
        grid-template-columns: 1fr;
    }

    .composer > * {
        grid-column: 1 !important;
    }
}
</style>
</head>

<body>

<header>
    <div class="logo">Crypto<span>Pulse</span></div>

    <nav>
        <button data-page="home" class="active">Overview</button>
        <button data-page="markets">Markets</button>
        <button data-page="watchlist">Watchlist</button>
        <button data-page="charts">Charts</button>
        <button data-page="community">Community</button>
        <button data-page="about">About</button>
    </nav>
</header>

<main id="app">Loading website...</main>

<footer>
    CryptoPulse · Market data provided by CoinGecko.
    Cryptocurrency information is not financial advice.
</footer>

<script>
const $ = id => document.getElementById(id);

const META = {
    bitcoin: ["BTC", "Bitcoin", "₿"],
    ethereum: ["ETH", "Ethereum", "◆"],
    solana: ["SOL", "Solana", "◎"],
    binancecoin: ["BNB", "BNB", "B"],
    ripple: ["XRP", "XRP", "X"],
    dogecoin: ["DOGE", "Dogecoin", "Ð"],
    "the-open-network": ["TON", "Toncoin", "T"],
    cardano: ["ADA", "Cardano", "A"]
};

let coins = [];
let currentPage = "home";
let chartRequest = 0;
let lastMessages = "";

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[c]));
}

function money(value) {
    if (value == null) return "Unavailable";

    return "$" + Number(value).toLocaleString("en-US", {
        maximumFractionDigits: value < 1 ? 6 : 2
    });
}

function saved() {
    try {
        return JSON.parse(localStorage.getItem("cp_watch") || "[]");
    } catch (_) {
        return [];
    }
}

function toggleWatch(id) {
    let list = saved();

    list = list.includes(id)
        ? list.filter(item => item !== id)
        : [...list, id];

    localStorage.setItem("cp_watch", JSON.stringify(list));
    render();
}

function coinCard(c) {
    const favorite = saved().includes(c.id);

    return `
    <article class="card">
        <b>${escapeHTML(c.name)}</b>
        <span class="muted">${escapeHTML(c.symbol)}</span>

        <div class="price">${money(c.price)}</div>

        <div class="${c.change >= 0 ? "green" : "red"}">
            ${c.change == null
                ? "Change unavailable"
                : (c.change >= 0 ? "+" : "") +
                  Number(c.change).toFixed(2) + "%"}
            <span class="muted">24h</span>
        </div>

        <p>
            <button class="secondary"
                data-watch="${escapeHTML(c.id)}">
                ${favorite ? "★ Saved" : "☆ Watch"}
            </button>

            <button class="secondary"
                data-detail="${escapeHTML(c.id)}">
                Details
            </button>
        </p>
    </article>`;
}

function marketTable(list) {
    if (!list.length) {
        return '<p class="muted">No matching assets found.</p>';
    }

    return `
    <div class="card tablewrap">
    <table>
        <thead>
            <tr>
                <th>Asset</th>
                <th>Price</th>
                <th>24h</th>
                <th>Watchlist</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
        ${list.map(c => `
            <tr>
                <td>
                    <b>${escapeHTML(c.name)}</b>
                    <br><span class="muted">${c.symbol}</span>
                </td>
                <td>${money(c.price)}</td>
                <td class="${c.change >= 0 ? "green" : "red"}">
                    ${c.change == null
                        ? "—"
                        : Number(c.change).toFixed(2) + "%"}
                </td>
                <td>
                    <button class="secondary"
                        data-watch="${escapeHTML(c.id)}">
                        ${saved().includes(c.id) ? "★" : "☆"}
                    </button>
                </td>
                <td>
                    <button class="secondary"
                        data-detail="${escapeHTML(c.id)}">
                        Open
                    </button>
                </td>
            </tr>
        `).join("")}
        </tbody>
    </table>
    </div>`;
}

function chatHTML() {
    return `
    <section class="card">
        <h2>💬 Live Crypto Chat</h2>
        <p class="muted">
            Messages are shared with visitors connected to this server.
        </p>

        <div id="chat" class="chat">Loading messages...</div>

        <form id="chatform" class="composer">
            <input class="username" id="username"
                maxlength="24" placeholder="Username" required>

            <input class="messagebox" id="message"
                maxlength="400" placeholder="Write a message..."
                autocomplete="off" required>

            <button class="action" type="submit">Send</button>
        </form>
    </section>`;
}

function heading(kicker, title, description) {
    return `
    <div class="muted">${kicker}</div>
    <h1>${title}</h1>
    <p class="muted">${description}</p>`;
}

function render() {
    const app = $("app");

    document.querySelectorAll("[data-page]").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.page === currentPage
        );
    });

    if (currentPage === "home") {
        app.innerHTML =
            heading(
                "CRYPTOCURRENCY MARKET TRACKER",
                'Crypto market <span>at a glance.</span>',
                "Follow crypto prices and join the community."
            ) +
            `<h2>Market overview</h2>` +
            `<div class="grid">${
                coins.length
                    ? coins.map(coinCard).join("")
                    : '<div class="card">Loading prices...</div>'
            }</div>` +
            `<h2>Community chat</h2>` +
            chatHTML();

    } else if (currentPage === "markets") {
        app.innerHTML =
            heading(
                "EXPLORE ASSETS",
                "Cryptocurrency markets",
                "Search and sort tracked cryptocurrencies."
            ) +
            `<div class="tools">
                <input id="search" placeholder="Search name or ticker...">
                <select id="sort">
                    <option value="default">Default</option>
                    <option value="gainers">Top gainers</option>
                    <option value="losers">Top losers</option>
                    <option value="price">Price high to low</option>
                    <option value="name">Name A-Z</option>
                </select>
            </div>
            <div id="markettable"></div>`;

        updateMarketTable();

        $("search").addEventListener("input", updateMarketTable);
        $("sort").addEventListener("change", updateMarketTable);

    } else if (currentPage === "watchlist") {
        const list = coins.filter(c => saved().includes(c.id));

        app.innerHTML =
            heading(
                "PERSONAL LIST",
                "Your watchlist",
                "Saved in this browser on your device."
            ) +
            `<div class="grid">${
                list.length
                    ? list.map(coinCard).join("")
                    : '<div class="card">Your watchlist is empty. Visit Markets to save coins.</div>'
            }</div>`;

    } else if (currentPage === "charts") {
        app.innerHTML =
            heading(
                "MARKET TRENDS",
                "Historical price charts",
                "View the last seven days of available price data."
            ) +
            `<section class="card">
                <select id="chartcoin">
                    ${coins.map(c =>
                        `<option value="${escapeHTML(c.id)}">${escapeHTML(c.name)}</option>`
                    ).join("")}
                </select>
                <p id="chartstatus" class="muted">Select a coin.</p>
                <canvas id="chart" class="chart"></canvas>
            </section>`;

        $("chartcoin").addEventListener("change", loadChart);

        if (coins.length) loadChart();

    } else if (currentPage === "community") {
        app.innerHTML =
            heading(
                "COMMUNITY",
                "Talk crypto together",
                "Discuss markets, projects, and ideas."
            ) +
            chatHTML();

    } else if (currentPage === "about") {
        app.innerHTML =
            heading(
                "ABOUT CRYPTOPULSE",
                "Markets and community",
                "A lightweight cryptocurrency dashboard."
            ) +
            `<div class="card">
                <h2>Market data</h2>
                <p class="muted">
                    Price information is requested from CoinGecko.
                </p>
                <h2>Chat</h2>
                <p class="muted">
                    Messages are stored in server memory and are lost
                    when the Python server restarts.
                </p>
                <h2>Security</h2>
                <p class="muted">
                    Do not share passwords, wallet seed phrases, or
                    private keys. This demo has no verified accounts.
                </p>
                <h2>Risk notice</h2>
                <p class="muted">
                    Cryptocurrency prices are volatile. This website
                    does not provide financial advice.
                </p>
            </div>`;
    }

    bindButtons();

    if ($("chatform")) {
        $("username").value = localStorage.getItem("cp_name") || "";

        $("username").addEventListener("change", () => {
            localStorage.setItem("cp_name", $("username").value.trim());
        });

        $("chatform").addEventListener("submit", sendMessage);
        loadMessages();
    }
}

function updateMarketTable() {
    if (!$("markettable")) return;

    const query = $("search").value.toLowerCase();
    const sort = $("sort").value;

    let list = coins.filter(c =>
        (c.name + " " + c.symbol).toLowerCase().includes(query)
    );

    if (sort === "gainers") {
        list.sort((a, b) => (b.change ?? -Infinity) - (a.change ?? -Infinity));
    } else if (sort === "losers") {
        list.sort((a, b) => (a.change ?? Infinity) - (b.change ?? Infinity));
    } else if (sort === "price") {
        list.sort((a, b) => (b.price ?? -Infinity) - (a.price ?? -Infinity));
    } else if (sort === "name") {
        list.sort((a, b) => a.name.localeCompare(b.name));
    }

    $("markettable").innerHTML = marketTable(list);
    bindButtons();
}

function bindButtons() {
    document.querySelectorAll("[data-watch]").forEach(button => {
        button.onclick = () => toggleWatch(button.dataset.watch);
    });

    document.querySelectorAll("[data-detail]").forEach(button => {
        button.onclick = () => showCoin(button.dataset.detail);
    });

    document.querySelectorAll("[data-page]").forEach(button => {
        button.onclick = () => {
            currentPage = button.dataset.page;
            render();
        };
    });
}

function showCoin(id) {
    const c = coins.find(item => item.id === id);
    if (!c) return;

    currentPage = "about";

    $("app").innerHTML = `
        ${heading(
            "ASSET DETAILS",
            escapeHTML(c.name) + " (" + c.symbol + ")",
            "Current market information."
        )}

        <div class="card">
            <div class="price">${money(c.price)}</div>

            <p class="${c.change >= 0 ? "green" : "red"}">
                ${c.change == null ? "—" : c.change.toFixed(2) + "%"} in 24h
            </p>

            <button class="action" id="detailwatch">
                ${saved().includes(c.id) ? "Remove from watchlist" : "Add to watchlist"}
            </button>

            <p>
                <button class="secondary" id="backmarkets">
                    Back to markets
                </button>
            </p>
        </div>`;

    $("detailwatch").onclick = () => toggleWatch(id);

    $("backmarkets").onclick = () => {
        currentPage = "markets";
        render();
    };
}

async function getJSON(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
        throw Error(data.error || "Request failed");
    }

    return data;
}

async function refreshPrices() {
    try {
        const data = await getJSON("/api/prices");

        if (data.data) {
            coins = data.data.map(c => ({
                ...c,
                symbol: META[c.id]?.[0] || c.symbol,
                name: META[c.id]?.[1] || c.name,
                icon: META[c.id]?.[2] || "●"
            }));

            render();
        }
    } catch (error) {
        console.log("Price refresh:", error.message);
    }
}

async function sendMessage(event) {
    event.preventDefault();

    const name = $("username").value.trim();
    const text = $("message").value.trim();

    if (!name || !text) return;

    const button = $("chatform").querySelector("button");
    button.disabled = true;

    try {
        await getJSON("/api/messages", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, text})
        });

        $("message").value = "";
        await loadMessages(true);

    } catch (error) {
        alert("Message failed: " + error.message);
    } finally {
        button.disabled = false;
    }
}

async function loadMessages(force = false) {
    if (!$("chat")) return;

    try {
        const data = await getJSON("/api/messages");
        const signature = JSON.stringify(data.messages);

        if (signature === lastMessages && !force) return;

        lastMessages = signature;

        const chat = $("chat");
        const nearBottom =
            chat.scrollHeight - chat.scrollTop - chat.clientHeight < 60;

        chat.innerHTML = data.messages.length
            ? data.messages.map(m => `
                <div class="message">
                    <b>${escapeHTML(m.name)}</b>
                    <small>${escapeHTML(m.time)}</small>
                    <div>${escapeHTML(m.text)}</div>
                </div>
            `).join("")
            : '<div class="muted">No messages yet. Start the conversation!</div>';

        if (nearBottom) chat.scrollTop = chat.scrollHeight;

    } catch (error) {
        console.log("Chat refresh:", error.message);
    }
}

async function loadChart() {
    const id = $("chartcoin")?.value;
    const canvas = $("chart");

    if (!id || !canvas) return;

    const requestId = ++chartRequest;

    $("chartstatus").textContent = "Loading historical prices...";

    try {
        const data = await getJSON(
            "/api/history?id=" + encodeURIComponent(id)
        );

        if (requestId !== chartRequest) return;

        drawChart(canvas, data.prices || []);

        $("chartstatus").textContent =
            "Seven-day history · " + data.prices.length + " data points";

    } catch (error) {
        $("chartstatus").textContent =
            "Historical data unavailable. Check your internet connection or try later.";
    }
}

function drawChart(canvas, points) {
    const width = canvas.clientWidth || 600;
    const height = 260;
    const ratio = window.devicePixelRatio || 1;

    canvas.width = width * ratio;
    canvas.height = height * ratio;

    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, height);

    const values = points.map(p => p[1]).filter(Number.isFinite);

    if (values.length < 2) return;

    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = 24;

    ctx.strokeStyle = "#27354b";
    ctx.lineWidth = 1;

    for (let i = 0; i < 4; i++) {
        const y = pad + i * (height - 2 * pad) / 3;

        ctx.beginPath();
        ctx.moveTo(pad, y);
        ctx.lineTo(width - pad, y);
        ctx.stroke();
    }

    ctx.strokeStyle = "#27d99a";
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    values.forEach((value, index) => {
        const x = pad + index * (width - 2 * pad) / (values.length - 1);
        const y = height - pad -
            (value - min) / (max - min || 1) * (height - 2 * pad);

        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();

    ctx.fillStyle = "#93a2ba";
    ctx.font = "12px Arial";
    ctx.fillText(money(max), pad, 14);
    ctx.fillText(money(min), pad, height - 4);
}

document.querySelectorAll("[data-page]").forEach(button => {
    button.addEventListener("click", () => {
        currentPage = button.dataset.page;
        render();
    });
});

render();
refreshPrices();

setInterval(refreshPrices, 60000);

setInterval(() => {
    if ($("chat")) loadMessages();
}, 2000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            body = HTML.encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/prices":
            with market_lock:
                result = dict(market)

            self.send_json(result)

        elif path == "/api/messages":
            with messages_lock:
                result = list(messages)

            self.send_json({"messages": result})

        elif path == "/api/history":
            params = urllib.parse.parse_qs(parsed.query)
            coin_id = params.get("id", ["bitcoin"])[0]

            if coin_id not in {c[0] for c in COINS}:
                self.send_json({"error": "Unsupported coin"}, 400)
                return

            url = (
                "https://api.coingecko.com/api/v3/coins/"
                + urllib.parse.quote(coin_id)
                + "/market_chart?vs_currency=usd&days=7"
            )

            try:
                request = urllib.request.Request(
                    url,
                    headers={"User-Agent": "CryptoPulse/1.0"}
                )

                with urllib.request.urlopen(
                    request, timeout=12
                ) as response:
                    data = json.loads(
                        response.read().decode("utf-8")
                    )

                self.send_json({
                    "prices": data.get("prices", [])
                })

            except Exception:
                self.send_json({
                    "error": "Historical price service unavailable"
                }, 502)

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/messages":
            self.send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 4096:
                self.send_json({"error": "Invalid request size"}, 400)
                return

            payload = json.loads(
                self.rfile.read(length).decode("utf-8")
            )

        except Exception:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        name = payload.get("name", "")
        text = payload.get("text", "")

        if not isinstance(name, str) or not isinstance(text, str):
            self.send_json({"error": "Invalid message"}, 400)
            return

        name = " ".join(name.split())[:24]
        text = " ".join(text.split())[:400]

        if not name or not text:
            self.send_json({"error": "Enter a name and message"}, 400)
            return

        message = {
            "name": name,
            "text": text,
            "time": time.strftime("%H:%M:%S")
        }

        with messages_lock:
            messages.append(message)

        self.send_json({"ok": True, "message": message}, 201)


def main():
    threading.Thread(
        target=market_worker,
        daemon=True
    ).start()

    server = ThreadingHTTPServer((HOST, PORT), Handler)

    print("=" * 45)
    print(" CryptoPulse started")
    print(" Open http://127.0.0.1:8080 in your browser")
    print(" Stop the server with Ctrl+C")
    print("=" * 45)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("Stopping CryptoPulse...")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()