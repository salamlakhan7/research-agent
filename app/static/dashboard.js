const $ = (id) => document.getElementById(id);
const STAGES = ["intake", "planner", "searcher", "reader", "organizer", "summarizer", "writer", "critic"];
const CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="#4fd1ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7"/></svg>';
let mode = "topic", reportText = "", openId = null, openText = "";

/* auth guard + logout */
fetch("/api/me").then(async (r) => {
  if (!r.ok) return (location.href = "/login.html");
  $("uname").textContent = (await r.json()).name;
});
$("logout").onclick = async () => {
  await fetch("/api/logout", { method: "POST" });
  location.href = "/login.html";
};

/* sidebar navigation */
function showPanel(name) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
  $("panel-" + name).classList.remove("hidden");
  document.querySelectorAll("[data-panel]").forEach((b) => b.classList.toggle("on", b.dataset.panel === name));
  if (name === "history") loadHistory();
  if (name === "suggested") loadSuggested();
  if (name === "trending") loadTrending();
  if (name === "saved") loadSaved();
  if (name === "usage") loadUsage();
  if (name === "settings") loadSettings();
}
document.querySelectorAll("[data-panel]").forEach((b) => (b.onclick = () => showPanel(b.dataset.panel)));

function download(text, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/markdown" }));
  a.download = name;
  a.click();
}

/* pipeline tracker */
$("pipeline").innerHTML = STAGES.map(
  (s) => `<div class="stage" id="st-${s}"><div class="ring">${CHECK}</div><span>${s}</span></div>`
).join("");
const activeStages = () => (mode === "links" ? STAGES.filter((s) => s !== "planner" && s !== "searcher") : STAGES);
function resetPipeline() {
  STAGES.forEach((s) => ($("st-" + s).className = "stage" + (activeStages().includes(s) ? "" : " skip")));
  $("st-intake").classList.add("active");
}
function applyProgress(text) {
  const done = new Set([...text.matchAll(/(\w+) done/g)].map((m) => m[1]));
  let activeSet = false;
  activeStages().forEach((s) => {
    const el = $("st-" + s);
    if (done.has(s)) el.className = "stage done";
    else if (!activeSet) { el.className = "stage active"; activeSet = true; }
    else el.className = "stage";
  });
}
resetPipeline();

/* mode toggle */
function setMode(m) {
  mode = m;
  $("mode-topic").classList.toggle("on", m === "topic");
  $("mode-links").classList.toggle("on", m === "links");
  $("input").placeholder = m === "topic" ? "e.g. Risks of AI in healthcare" : "Paste 1-10 links, one per line";
  resetPipeline();
}
$("mode-topic").onclick = () => setMode("topic");
$("mode-links").onclick = () => setMode("links");

/* run research */
$("run").onclick = async () => {
  if (!$("input").value.trim()) return;
  $("run").disabled = true;
  $("card").classList.add("hidden");
  loadRelated(reportText);
  resetPipeline();
  $("status").textContent = "Agent running. This can take a few minutes on CPU.";
  try {
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, input: $("input").value, length: $("length").value, style: $("style").value }),
    });
    if (res.status === 401) return (location.href = "/login.html");
    if (res.status === 429) {
      $("status").textContent = "Daily limit reached (5 briefs per 24 hours). Come back tomorrow.";
      return;
    }
    if (!res.ok) throw new Error("Server error " + res.status);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const [progress, report] = buffer.split("---REPORT---");
      applyProgress(progress);
      if (report !== undefined) reportText = report.trim();
    }
    activeStages().forEach((s) => ($("st-" + s).className = "stage done"));
    $("output").innerHTML = marked.parse(reportText);
    $("card").classList.remove("hidden");
    $("status").textContent = "Complete. Saved to History.";
  } catch (e) {
    $("status").textContent = "Error: " + e.message;
  } finally {
    $("run").disabled = false;
  }
};
$("download").onclick = () => download(reportText, "research-brief.md");

/* history */
async function loadHistory() {
  const list = $("hist-list");
  list.innerHTML = "";
  $("viewer").classList.add("hidden");
  const r = await fetch("/api/history");
  if (!r.ok) return;
  const items = await r.json();
  if (!items.length) {
    list.innerHTML = '<p class="text-slate-400 text-sm">No briefs yet. Generate your first one.</p>';
    return;
  }
  items.forEach((it) => {
    const b = document.createElement("button");
    b.className = "hist-item";
    const t = document.createElement("div");
    t.textContent = it.input.slice(0, 90);
    const m = document.createElement("div");
    m.className = "text-xs text-slate-500 mt-1";
    m.textContent = `${it.mode} | ${it.length} | ${it.created_at}`;
    b.append(t, m);
    b.onclick = () => openItem(it.id);
    list.append(b);
  });
}
async function openItem(id) {
  const r = await fetch("/api/history/" + id);
  if (!r.ok) return;
  const d = await r.json();
  openId = id;
  openText = d.report;
  $("v-save").textContent = d.saved ? "Unsave" : "Save";
  $("viewer-body").innerHTML = marked.parse(d.report);
  $("viewer").classList.remove("hidden");
  $("viewer").scrollIntoView({ behavior: "smooth" });
}
$("v-download").onclick = () => download(openText, "research-brief.md");
$("v-delete").onclick = async () => {
  await fetch("/api/history/" + openId, { method: "DELETE" });
  loadHistory();
};

/* suggested + trending */
function useTopic(t) {
  setMode("topic");
  $("input").value = t;
  showPanel("research");
  $("input").focus();
}
function topicButton(text, sub) {
  const b = document.createElement("button");
  b.className = "hist-item";
  const t = document.createElement("div");
  t.textContent = text;
  b.append(t);
  if (sub) {
    const s = document.createElement("div");
    s.className = "text-xs text-slate-500 mt-1";
    s.textContent = sub;
    b.append(s);
  }
  b.onclick = () => useTopic(text);
  return b;
}
async function loadSuggested() {
  const list = $("sugg-list");
  list.innerHTML = "";
  $("sugg-note").textContent = "Generating ideas...";
  const r = await fetch("/api/suggestions");
  if (!r.ok) return;
  const d = await r.json();
  $("sugg-note").textContent = d.personal
    ? "Based on your recent briefs. Click one to research it."
    : "Starter ideas. Run a few briefs and these become personal.";
  d.topics.forEach((t) => list.append(topicButton(t)));
}
async function loadTrending() {
  const r = await fetch("/api/trending");
  if (!r.ok) return;
  const d = await r.json();
  const pop = $("pop-list");
  pop.innerHTML = "";
  if (!d.popular.length) {
    pop.innerHTML = '<p class="text-slate-400 text-sm">Nothing yet. Topics researched by 2 or more users appear here.</p>';
  }
  d.popular.forEach((p) => pop.append(topicButton(p.topic, p.users + " users")));
  const cur = $("cur-list");
  cur.innerHTML = "";
  let cat = "";
  d.curated.forEach((c) => {
    if (c.category !== cat) {
      cat = c.category;
      const h = document.createElement("p");
      h.className = "text-xs uppercase tracking-widest text-sky-300 mt-4 mb-2";
      h.textContent = cat;
      cur.append(h);
    }
    cur.append(topicButton(c.topic));
  });
}

/* related questions */
async function loadRelated(text) {
  try {
    const r = await fetch("/api/related", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!r.ok) return;
    const d = await r.json();
    if (!d.questions.length) return;
    const list = $("related-list");
    list.innerHTML = "";
    d.questions.forEach((q) => list.append(topicButton(q)));
    $("related").classList.remove("hidden");
  } catch (e) {}
}

/* save / unsave from history viewer */
$("v-save").onclick = async () => {
  const r = await fetch("/api/history/" + openId + "/save", { method: "POST" });
  if (r.ok) $("v-save").textContent = (await r.json()).saved ? "Unsave" : "Save";
};

/* saved */
async function loadSaved() {
  const list = $("sav-list");
  list.innerHTML = "";
  const r = await fetch("/api/saved");
  if (!r.ok) return;
  const items = await r.json();
  if (!items.length) {
    list.innerHTML = '<p class="text-slate-400 text-sm">Nothing saved yet. Open a brief in History and press Save.</p>';
    return;
  }
  items.forEach((it) => {
    const b = topicButton(it.input.slice(0, 90), `${it.mode} | ${it.created_at}`);
    b.onclick = async () => { showPanel("history"); await openItem(it.id); };
    list.append(b);
  });
}

/* usage */
async function loadUsage() {
  const r = await fetch("/api/usage");
  if (!r.ok) return;
  const d = await r.json();
  $("u-today").textContent = d.today;
  $("u-total").textContent = d.total;
  $("u-saved").textContent = d.saved;
  $("u-bar").style.width = Math.min(100, (d.today / d.limit) * 100) + "%";
  $("u-note").textContent = `${d.today} of ${d.limit} briefs used in the last 24 hours.`;
}

/* settings */
function sMsg(t, ok) {
  $("s-msg").textContent = t;
  $("s-msg").className = "text-sm " + (ok ? "text-cyan-300" : "text-red-400");
}
async function sPost(url, body) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : "Something went wrong.");
  return d;
}
async function loadSettings() {
  $("s-msg").textContent = "";
  const r = await fetch("/api/me");
  if (r.ok) $("s-name").value = (await r.json()).name;
}
$("s-name-save").onclick = async () => {
  try {
    const d = await sPost("/api/settings/name", { name: $("s-name").value });
    $("uname").textContent = d.name;
    sMsg("Name updated.", true);
  } catch (e) { sMsg(e.message, false); }
};
$("s-pw-save").onclick = async () => {
  try {
    await sPost("/api/settings/password", { current: $("s-cur").value, new: $("s-new").value });
    $("s-cur").value = ""; $("s-new").value = "";
    sMsg("Password updated.", true);
  } catch (e) { sMsg(e.message, false); }
};
$("s-del-go").onclick = async () => {
  if (!confirm("Delete your account and all briefs permanently?")) return;
  try {
    await sPost("/api/account/delete", { password: $("s-del").value });
    location.href = "/";
  } catch (e) { sMsg(e.message, false); }
};