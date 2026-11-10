// AgentForge Dashboard: membaca data/runs.json dan menampilkan
// daftar run, jejak langkah per agent, skor reviewer, dan biaya.

const state = { runs: [], selected: null };

function fmtUsd(v) {
  return "$" + Number(v).toFixed(6);
}

function scoreClass(score) {
  return score >= 70 ? "ok" : "bad";
}

function renderSummary() {
  const el = document.getElementById("summary-cards");
  const runs = state.runs;
  const totalCost = runs.reduce((a, r) => a + r.total_cost_usd, 0);
  const totalTokens = runs.reduce((a, r) => a + r.total_tokens, 0);
  const avgScore = runs.length ? runs.reduce((a, r) => a + r.reviewer_score, 0) / runs.length : 0;
  const cards = [
    ["Total Run", runs.length, ""],
    ["Rata-rata Skor Reviewer", avgScore.toFixed(1), "/ 100"],
    ["Total Token", totalTokens.toLocaleString("id-ID"), ""],
    ["Total Biaya (estimasi demo)", fmtUsd(totalCost), ""],
  ];
  el.innerHTML = cards
    .map(c => `<div class="card"><div class="label">${c[0]}</div><div class="value">${c[1]} <small>${c[2]}</small></div></div>`)
    .join("");
  if (runs.length) {
    document.getElementById("mode-badge").textContent = "mode: " + runs[0].mode;
  }
}

function renderList() {
  const el = document.getElementById("run-list");
  el.innerHTML = "";
  state.runs.forEach((run, idx) => {
    const div = document.createElement("div");
    div.className = "run-item" + (state.selected === idx ? " active" : "");
    div.innerHTML = `
      <div class="title">${run.title}</div>
      <div class="meta">
        <span>${run.workflow_label}</span>
        <span class="score ${scoreClass(run.reviewer_score)}">skor ${run.reviewer_score}</span>
        <span>${run.step_count} langkah</span>
        <span>${fmtUsd(run.total_cost_usd)}</span>
      </div>`;
    div.addEventListener("click", () => {
      state.selected = idx;
      renderList();
      renderDetail(run);
    });
    el.appendChild(div);
  });
}

function renderDetail(run) {
  const el = document.getElementById("run-detail");
  const comp = run.reviewer_components || {};
  const rows = run.steps
    .map(
      s => `<tr>
        <td>${s.step_id}</td><td>${s.agent}</td><td>${s.action}</td>
        <td>${s.model}</td>
        <td class="num">${s.prompt_tokens}</td>
        <td class="num">${s.completion_tokens}</td>
        <td class="num">${fmtUsd(s.cost_usd)}</td>
        <td>${s.status}</td>
      </tr>`
    )
    .join("");
  const compRows = Object.entries(comp)
    .map(([k, v]) => `<tr><td>${k}</td><td class="num">${v}</td></tr>`)
    .join("");
  el.innerHTML = `
    <h3 style="margin-top:0">${run.title}</h3>
    <div class="kv">
      <div><div class="k">Workflow</div><div class="v">${run.workflow_label}</div></div>
      <div><div class="k">Skor Reviewer</div><div class="v">${run.reviewer_score} / 100</div></div>
      <div><div class="k">Putaran Revisi</div><div class="v">${run.revision_rounds}</div></div>
      <div><div class="k">Total Biaya</div><div class="v">${fmtUsd(run.total_cost_usd)}</div></div>
    </div>
    <h4>Jejak Langkah</h4>
    <table>
      <thead><tr><th>Langkah</th><th>Agent</th><th>Aksi</th><th>Model</th>
      <th class="num">Token Prompt</th><th class="num">Token Selesai</th>
      <th class="num">Biaya</th><th>Status</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <h4>Komponen Skor Reviewer</h4>
    <table><tbody>${compRows}</tbody></table>
    <h4>Output Final</h4>
    <div class="output-box">${run.final_output}</div>`;
}

async function init() {
  try {
    const resp = await fetch("data/runs.json");
    state.runs = await resp.json();
  } catch (err) {
    document.getElementById("run-list").innerHTML =
      '<p class="muted">Gagal memuat data/runs.json. Sajikan dashboard lewat server statis, bukan file langsung.</p>';
    return;
  }
  renderSummary();
  renderList();
  if (state.runs.length) {
    state.selected = 0;
    renderList();
    renderDetail(state.runs[0]);
  }
}

document.addEventListener("DOMContentLoaded", init);
