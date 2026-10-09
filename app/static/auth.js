const $ = (id) => document.getElementById(id);
const form = $("form");
const msg = $("msg");
const mode = form.dataset.mode;   // "signup" or "login"

function show(text, ok) {
  msg.textContent = text;
  msg.className = "text-sm mb-4 " + (ok ? "text-cyan-300" : "text-red-400");
}

// already logged in? skip straight to dashboard
fetch("/api/me").then((r) => { if (r.ok) location.href = "/dashboard.html"; });

if (new URLSearchParams(location.search).get("registered")) show("Account created. Please log in.", true);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("submit");
  btn.disabled = true;
  const body = mode === "signup"
    ? { name: $("name").value, email: $("email").value, password: $("password").value }
    : { email: $("email").value, password: $("password").value };
  try {
    const r = await fetch("/api/" + mode, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Please check your details.");
    location.href = mode === "signup" ? "/login.html?registered=1" : "/dashboard.html";
  } catch (err) {
    show(err.message, false);
    btn.disabled = false;
  }
});