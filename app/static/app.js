const clientSelect = document.getElementById("clientSelect");
const asOfInput = document.getElementById("asOfInput");
const refreshBtn = document.getElementById("refreshBtn");
const generateDraftBtn = document.getElementById("generateDraftBtn");
const draftStatus = document.getElementById("draftStatus");
const draftHistory = document.getElementById("draftHistory");
const tooltip = document.getElementById("tooltip");

const STATUS_ORDER = ["accepted", "awaiting_acceptance", "in_progress", "planned"];
const STATUS_META = {
  accepted: { label: "Accepted", color: "var(--good-pastel)" },
  awaiting_acceptance: { label: "Awaiting acceptance", color: "var(--warning-pastel)" },
  in_progress: { label: "In progress", color: "var(--series-pastel)" },
  planned: { label: "Planned", color: "var(--muted-pastel)" },
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function qs(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v) usp.set(k, v); });
  const s = usp.toString();
  return s ? `?${s}` : "";
}

function fmtRow(cells) {
  return `<tr>${cells.map(c => `<td>${c}</td>`).join("")}</tr>`;
}

function statusPill(status) {
  const meta = STATUS_META[status] || { label: status };
  return `<span class="status-pill st-${status}"><span class="dot" style="background:${meta.color}"></span>${meta.label}</span>`;
}

function legendHtml() {
  return STATUS_ORDER.map(s =>
    `<span class="legend-item"><span class="swatch" style="background:${STATUS_META[s].color}"></span>${STATUS_META[s].label}</span>`
  ).join("");
}

async function loadClients() {
  const res = await fetch("/api/clients");
  const data = await res.json();
  clientSelect.innerHTML = '<option value="">— All clients —</option>' +
    data.clients.map(c => `<option value="${c}">${c}</option>`).join("");
}

function donutSvg(statusCounts, { size, strokeWidth, label }) {
  const total = STATUS_ORDER.reduce((sum, s) => sum + statusCounts[s], 0) || 1;
  const r = (size - strokeWidth) / 2;
  const cx = size / 2, cy = size / 2;
  const circumference = 2 * Math.PI * r;
  let cumulative = 0;
  const circles = STATUS_ORDER.map(s => {
    const count = statusCounts[s];
    const pct = count / total;
    const dash = pct * circumference;
    const offset = -cumulative;
    cumulative += dash;
    const pctLabel = (pct * 100).toFixed(1);
    return `<circle cx="${cx}" cy="${cy}" r="${r}" stroke="${STATUS_META[s].color}"
              stroke-dasharray="${dash} ${circumference - dash}" stroke-dashoffset="${offset}"
              pointer-events="stroke"
              data-tooltip="${label ? label + ": " : ""}${STATUS_META[s].label} — ${count} (${pctLabel}%)"></circle>`;
  }).join("");
  return `<svg viewBox="0 0 ${size} ${size}">${circles}</svg>`;
}

function renderHero(overall) {
  const counts = overall.status_counts;
  const total = overall.total || 1;
  const acceptedPct = Math.round(100 * counts.accepted / total);
  document.getElementById("heroDonut").innerHTML =
    donutSvg(counts, { size: 180, strokeWidth: 26 }) +
    `<div class="donut-center">
       <div class="donut-center-value">${acceptedPct}%</div>
       <div class="donut-center-label">ลูกค้ารับรองแล้ว<br>(client accepted)</div>
     </div>`;
  document.getElementById("heroLegend").innerHTML = legendHtml();
}

function renderStatusChart(byClient) {
  document.getElementById("chartLegend").innerHTML = legendHtml();
  const title = document.getElementById("chartTitle");
  title.textContent = byClient.length === 1 ? "Status composition — selected client" : "Status composition by client";

  const rows = [...byClient].sort((a, b) => {
    const rateA = a.total ? a.client_accepted / a.total : 0;
    const rateB = b.total ? b.client_accepted / b.total : 0;
    return rateB - rateA;
  });

  const wrap = document.getElementById("statusChart");
  wrap.innerHTML = rows.map(c => {
    const total = c.total || 1;
    const acceptedPct = Math.round(100 * c.client_accepted / total);
    return `
      <div class="mini-donut-card">
        <div class="mini-donut-wrap" title="${c.client_name}">
          ${donutSvg(c.status_counts, { size: 104, strokeWidth: 15, label: c.client_name })}
          <div class="mini-donut-center">${acceptedPct}%</div>
        </div>
        <div class="mini-donut-name">${c.client_name}</div>
      </div>`;
  }).join("");
}

function wireTooltip(container) {
  container.addEventListener("mousemove", (e) => {
    const seg = e.target.closest("[data-tooltip]");
    if (!seg) { tooltip.hidden = true; return; }
    tooltip.textContent = seg.dataset.tooltip;
    tooltip.hidden = false;
    tooltip.style.left = `${e.clientX + 14}px`;
    tooltip.style.top = `${e.clientY + 14}px`;
  });
  container.addEventListener("mouseleave", () => { tooltip.hidden = true; });
}

async function loadSummary(client, asOf) {
  const res = await fetch("/api/summary" + qs({ client, as_of: asOf }));
  const data = await res.json();
  document.getElementById("cardTotal").textContent = data.overall.total;
  document.getElementById("cardCompleted").textContent = data.overall.team_completed;
  document.getElementById("cardAccepted").textContent = data.overall.client_accepted;
  document.getElementById("cardOverdue").textContent = data.overall.overdue;

  renderHero(data.overall);
  renderStatusChart(data.by_client);

  const tbody = document.querySelector("#perClientTable tbody");
  tbody.innerHTML = data.by_client.map(c =>
    fmtRow([c.client_name, c.total, c.team_completed, c.client_accepted, c.overdue])
  ).join("");
}

async function loadPending(client, asOf) {
  const res = await fetch("/api/deliverables/pending-acceptance" + qs({ client, as_of: asOf }));
  const data = await res.json();
  const tbody = document.querySelector("#pendingTable tbody");
  tbody.innerHTML = data.items.map(i =>
    fmtRow([i.deliverable_id, i.client_name, i.deliverable_name, i.owner, i.due_date])
  ).join("") || '<tr><td colspan="5">No items pending acceptance.</td></tr>';
}

async function loadOverdue(client, asOf) {
  const res = await fetch("/api/deliverables/overdue" + qs({ client, as_of: asOf }));
  const data = await res.json();
  const tbody = document.querySelector("#overdueTable tbody");
  tbody.innerHTML = data.items.map(i =>
    `<tr class="overdue-row">${[i.deliverable_id, i.client_name, i.deliverable_name, i.owner, i.due_date, statusPill(i.status)]
      .map(c => `<td>${c}</td>`).join("")}</tr>`
  ).join("") || '<tr><td colspan="6">No overdue items.</td></tr>';
}

async function loadDraftHistory(client) {
  if (!client) { draftHistory.innerHTML = ""; return; }
  const res = await fetch("/api/ai/drafts" + qs({ client }));
  const data = await res.json();
  draftHistory.innerHTML = data.drafts.map(d => `
    <div class="draft-card">
      <div class="draft-meta">${d.client_name} · as of ${d.as_of} · ${d.created_at} · model ${d.model || "n/a"}</div>
      ${d.content}
    </div>`).join("") || "<p class=\"hint\">No drafts yet for this client.</p>";
}

async function refreshAll() {
  const client = clientSelect.value;
  const asOf = asOfInput.value || todayIso();
  await Promise.all([
    loadSummary(client, asOf),
    loadPending(client, asOf),
    loadOverdue(client, asOf),
    loadDraftHistory(client),
  ]);
}

generateDraftBtn.addEventListener("click", async () => {
  const client = clientSelect.value;
  if (!client) {
    draftStatus.textContent = "Select a client first.";
    return;
  }
  const asOf = asOfInput.value || todayIso();
  draftStatus.textContent = "Generating draft...";
  try {
    const res = await fetch(`/api/ai/draft-update${qs({ client, as_of: asOf })}`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json();
      draftStatus.textContent = `Error: ${err.detail || res.statusText}`;
      return;
    }
    draftStatus.textContent = "Draft generated.";
    await loadDraftHistory(client);
  } catch (e) {
    draftStatus.textContent = `Error: ${e}`;
  }
});

clientSelect.addEventListener("change", refreshAll);
refreshBtn.addEventListener("click", refreshAll);
wireTooltip(document.body);

(async function init() {
  asOfInput.value = todayIso();
  await loadClients();
  await refreshAll();
})();
