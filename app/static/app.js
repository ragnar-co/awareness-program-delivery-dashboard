const clientSelect = document.getElementById("clientSelect");
const asOfInput = document.getElementById("asOfInput");
const refreshBtn = document.getElementById("refreshBtn");
const generateDraftBtn = document.getElementById("generateDraftBtn");
const draftStatus = document.getElementById("draftStatus");
const draftHistory = document.getElementById("draftHistory");

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function qs(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v) usp.set(k, v); });
  const s = usp.toString();
  return s ? `?${s}` : "";
}

async function loadClients() {
  const res = await fetch("/api/clients");
  const data = await res.json();
  clientSelect.innerHTML = '<option value="">— All clients —</option>' +
    data.clients.map(c => `<option value="${c}">${c}</option>`).join("");
}

function fmtRow(cells) {
  return `<tr>${cells.map(c => `<td>${c}</td>`).join("")}</tr>`;
}

async function loadSummary(client, asOf) {
  const res = await fetch("/api/summary" + qs({ client, as_of: asOf }));
  const data = await res.json();
  document.getElementById("cardTotal").textContent = data.overall.total;
  document.getElementById("cardCompleted").textContent = data.overall.team_completed;
  document.getElementById("cardAccepted").textContent = data.overall.client_accepted;
  document.getElementById("cardOverdue").textContent = data.overall.overdue;

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
    `<tr class="overdue-row">${[i.deliverable_id, i.client_name, i.deliverable_name, i.owner, i.due_date, i.status]
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

(async function init() {
  asOfInput.value = todayIso();
  await loadClients();
  await refreshAll();
})();
