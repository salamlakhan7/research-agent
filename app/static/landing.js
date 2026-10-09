const $ = (id) => document.getElementById(id);

/* nav reflects login state */
fetch("/api/me").then((r) => {
  if (!r.ok) return;
  $("nav-login").classList.add("hidden");
  $("nav-signup").classList.add("hidden");
  const cta = $("nav-cta");
  cta.textContent = "Dashboard";
  cta.href = "/dashboard.html";
});

/* scroll reveal */
const io = new IntersectionObserver(
  (entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }),
  { threshold: 0.12 }
);
document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

/* animated tech flow */
const steps = [...document.querySelectorAll(".step")];
let i = 0;
setInterval(() => {
  steps.forEach((s) => s.classList.remove("lit"));
  steps[i % steps.length].classList.add("lit");
  i++;
}, 1200);

/* guest try-it */
$("try-run").onclick = async () => {
  const text = $("try-input").value.trim();
  if (!text) return;
  const mode = /https?:\/\//i.test(text) ? "links" : "topic";
  $("try-run").disabled = true;
  $("try-gate").classList.add("hidden");
  $("try-result").classList.add("hidden");
  $("try-status").textContent = "Agent running. This can take a few minutes.";

  try {
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, input: text, length: "short", style: "bullets" }),
    });
    if (res.status === 403) {
      $("try-gate").classList.remove("hidden");
      $("try-status").textContent = "";
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
      const [progress] = buffer.split("---REPORT---");
      const last = progress.trim().split("\n").pop();
      if (last) $("try-status").textContent = "Stage complete: " + last.replace(" done", "");
    }
    const report = (buffer.split("---REPORT---")[1] || "").trim();
    $("try-output").innerHTML = marked.parse(report);
    $("try-result").classList.remove("hidden");
    $("try-status").textContent = "Done";
    setTimeout(() => $("try-gate").classList.remove("hidden"), 600);
  } catch (e) {
    $("try-status").textContent = "Error: " + e.message;
  } finally {
    $("try-run").disabled = false;
  }
};