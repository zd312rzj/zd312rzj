const state = {
  session: null,
  messages: [],
  stats: {
    total_messages: 0,
    last_minute_messages: 0,
    active_users: 0,
    keyword_hits: 0,
    trend: [],
    keywords: [],
  },
  users: [],
  events: [],
};

const $ = (id) => document.getElementById(id);

function setStatus(session) {
  state.session = session;
  const dot = $("statusDot");
  dot.className = "status-dot";
  if (session.status === "running" || session.status === "starting") dot.classList.add("running");
  if (session.status === "error") dot.classList.add("error");
  $("sessionInfo").textContent = session.room_id
    ? `房间 ${session.room_id} · ${session.status}${session.error_message ? ` · ${session.error_message}` : ""}`
    : "未连接";
}

function renderStats() {
  $("totalMessages").textContent = state.stats.total_messages ?? 0;
  $("lastMinute").textContent = state.stats.last_minute_messages ?? 0;
  $("activeUsers").textContent = state.stats.active_users ?? 0;
  $("keywordHits").textContent = state.stats.keyword_hits ?? 0;
  $("trendHint").textContent = `${(state.stats.trend ?? []).length}个采样点`;
  renderTrend(state.stats.trend ?? []);
  renderKeywords(state.stats.keywords ?? []);
  if (state.stats.db_error) {
    addEvent({ event: "mysql_error", message: state.stats.db_error });
  }
}

function renderTrend(points) {
  const svg = $("trendChart");
  svg.innerHTML = "";
  const width = 640;
  const height = 230;
  const pad = 18;
  const max = Math.max(1, ...points.map((item) => item.count));
  const coords = points.length
    ? points.map((item, index) => {
        const x = points.length === 1 ? width / 2 : pad + (index * (width - pad * 2)) / (points.length - 1);
        const y = height - pad - (item.count / max) * (height - pad * 2);
        return [x, y];
      })
    : [
        [pad, height - pad],
        [width - pad, height - pad],
      ];
  const path = coords.map(([x, y], index) => `${index === 0 ? "M" : "L"} ${x} ${y}`).join(" ");
  const fillPath = `${path} L ${coords.at(-1)[0]} ${height - pad} L ${coords[0][0]} ${height - pad} Z`;
  svg.insertAdjacentHTML(
    "beforeend",
    `
      <defs>
        <linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#20d9c3" stop-opacity="0.38" />
          <stop offset="100%" stop-color="#20d9c3" stop-opacity="0.02" />
        </linearGradient>
      </defs>
      <path d="${fillPath}" fill="url(#trendFill)"></path>
      <path d="${path}" fill="none" stroke="#20d9c3" stroke-width="3"></path>
      ${coords.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="3.5" fill="#20d9c3"></circle>`).join("")}
    `,
  );
}

function renderKeywords(keywords) {
  $("keywords").innerHTML =
    keywords
      .map(
        (item) => `
          <div class="keyword-item">
            <span>${escapeHtml(item.keyword)}</span>
            <strong class="count">${item.hit_count}</strong>
          </div>
        `,
      )
      .join("") || `<div class="event-item"><div class="event-text">等待关键词命中</div></div>`;
}

function renderMessages() {
  $("messageCount").textContent = state.messages.length;
  $("messageFeed").innerHTML =
    state.messages
      .slice(-200)
      .reverse()
      .map(
        (message) => `
          <div class="message-item">
            <div class="message-meta">
              <span class="badge">${formatTime(message.received_at)}</span>
              <span class="nickname">${escapeHtml(message.nickname || "匿名用户")}</span>
            </div>
            <div class="message-content">${escapeHtml(message.content)}</div>
          </div>
        `,
      )
      .join("") || `<div class="event-item"><div class="event-text">暂无弹幕</div></div>`;
}

function renderUsers() {
  $("userRanking").innerHTML =
    state.users
      .map(
        (user) => `
          <li>
            <span>${escapeHtml(user.nickname || "匿名用户")}</span>
            <strong class="count">${user.count}条</strong>
          </li>
        `,
      )
      .join("") || `<li><span>暂无发言</span><strong class="count">0条</strong></li>`;
}

function addEvent(event) {
  state.events.unshift(event);
  state.events = state.events.slice(0, 20);
  $("eventCount").textContent = `${state.events.length}条事件`;
  $("systemEvents").innerHTML = state.events
    .map(
      (item) => `
        <div class="event-item">
          <div class="event-title">${escapeHtml(item.event || "system")}</div>
          <div class="event-text">${escapeHtml(item.message || "")}</div>
        </div>
      `,
    )
    .join("");
}

async function refreshAll() {
  const [session, messages, stats, users] = await Promise.all([
    fetchJson("/api/session/current"),
    fetchJson("/api/messages?limit=200"),
    fetchJson("/api/stats"),
    fetchJson("/api/ranking/users"),
  ]);
  setStatus(session);
  state.messages = messages;
  state.stats = stats;
  state.users = users;
  renderStats();
  renderMessages();
  renderUsers();
}

function connectEvents() {
  const source = new EventSource("/api/events");
  source.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.session) setStatus(payload.session);
    if (payload.type === "chat") {
      state.messages.push(payload.message);
      state.messages = state.messages.slice(-300);
      renderMessages();
      refreshStatsAndUsers();
    }
    if (payload.type === "stats") {
      state.stats = payload.stats;
      renderStats();
    }
    if (payload.type === "system") {
      addEvent(payload.system);
    }
  };
  source.onerror = () => {
    addEvent({ event: "sse_error", message: "实时连接断开，浏览器会自动重连" });
  };
}

async function refreshStatsAndUsers() {
  const [stats, users] = await Promise.all([fetchJson("/api/stats"), fetchJson("/api/ranking/users")]);
  state.stats = stats;
  state.users = users;
  renderStats();
  renderUsers();
}

async function startSession() {
  const room = $("roomInput").value.trim();
  if (!room) {
    addEvent({ event: "input_required", message: "请输入房间号或直播间URL" });
    return;
  }
  const session = await fetchJson("/api/session/start", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ room, headless: $("headlessInput").checked }),
  });
  setStatus(session);
  addEvent({ event: "start", message: "已请求启动监听" });
  await refreshAll();
}

async function stopSession() {
  const session = await fetchJson("/api/session/stop", { method: "POST" });
  setStatus(session);
  addEvent({ event: "stop", message: "已停止监听" });
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail || JSON.stringify(body);
    } catch {
      message = await response.text();
    }
    throw new Error(message || response.statusText);
  }
  return response.json();
}

function formatTime(value) {
  if (!value) return "--:--";
  return value.slice(11, 19) || value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

$("startBtn").addEventListener("click", () => startSession().catch((error) => addEvent({ event: "error", message: error.message })));
$("stopBtn").addEventListener("click", () => stopSession().catch((error) => addEvent({ event: "error", message: error.message })));

refreshAll().catch((error) => addEvent({ event: "init_error", message: error.message }));
connectEvents();
