const STORE_KEY = "palm92-content-studio-v1";
const $ = (id) => document.getElementById(id);
let cards = loadCards();

function loadCards() {
  try { return JSON.parse(localStorage.getItem(STORE_KEY) || "[]"); }
  catch { return []; }
}
function saveCards() { localStorage.setItem(STORE_KEY, JSON.stringify(cards)); render(); }
function esc(value) { return String(value || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c])); }

function makePrompt() {
  const title = $("title").value.trim() || "Untitled idea";
  const idea = $("idea").value.trim() || "[Add your rough idea or voice-note transcript]";
  const platform = $("platform").value;
  const purpose = $("purpose").value;
  return `Act as Faith Wright's Palm92 content editor. Turn the raw idea below into one ${platform} draft whose purpose is to ${purpose.toLowerCase()}.\n\nVOICE: warm, direct, thoughtful, practical, human. Use clear everyday English and short paragraphs. Preserve Faith's meaning and first-person details. Keep the user's original insight; do not imitate another creator's exact wording or claim their results. Avoid generic hype, invented facts, em dashes, and promises of viral growth.\n\nSTRUCTURE: begin with a specific human moment or clear hook; develop one useful point; end with a concise question or action relevant to the audience. If a fact needs checking, mark it [VERIFY] instead of guessing. Do not add private family, health, immigration, employment, or beneficiary details unless the user included them for this draft.\n\nReturn: (1) polished post, (2) 3 alternative hooks, (3) visual/video direction, (4) factual or personal details Faith should verify. Do not publish or schedule.\n\nWORKING TITLE: ${title}\nPURPOSE: ${purpose}\nRAW IDEA:\n${idea}`;
}

$("promptButton").addEventListener("click", () => {
  $("promptText").textContent = makePrompt();
  $("promptBox").hidden = false;
});
$("copyPrompt").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("promptText").textContent); $("copyPrompt").textContent = "Copied"; }
  catch { $("copyPrompt").textContent = "Select and copy the prompt"; }
});
$("contentForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const title = $("title").value.trim();
  if (!title) return;
  cards.unshift({ id: crypto.randomUUID(), title, platform: $("platform").value, purpose: $("purpose").value, targetDate: $("targetDate").value, idea: $("idea").value.trim(), draft: "", status: "Captured", createdAt: new Date().toISOString() });
  saveCards(); event.target.reset(); $("promptBox").hidden = true;
});
$("exportButton").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(cards, null, 2)], {type:"application/json"});
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "palm92-content-backup.json"; link.click(); URL.revokeObjectURL(link.href);
});

function render() {
  $("draftCount").textContent = `${cards.length} ${cards.length === 1 ? "draft" : "drafts"}`;
  $("emptyState").hidden = cards.length > 0;
  $("board").innerHTML = cards.map(card => `<article class="card" data-id="${esc(card.id)}">
    <h3>${esc(card.title)}</h3><div class="meta"><span>${esc(card.platform)}</span><span>${esc(card.purpose)}</span>${card.targetDate ? `<span>${esc(card.targetDate)}</span>` : ""}</div>
    <span class="status ${card.status === "Approved" ? "approved" : card.status === "Needs edit" ? "needs-edit" : ""}">${esc(card.status)}</span>
    <label>Draft text<textarea class="draft-text" aria-label="Draft text for ${esc(card.title)}" placeholder="Paste the returned draft here, then review it.">${esc(card.draft)}</textarea></label>
    <div class="card-actions"><button data-action="save">Save edits</button><button class="approve" data-action="approve">Mark approved</button><button data-action="edit" data-value="Needs edit">Needs edit</button><button class="delete" data-action="delete">Delete</button></div>
  </article>`).join("");
}
$("board").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]"); if (!button) return;
  const article = button.closest(".card"); const card = cards.find(item => item.id === article.dataset.id); if (!card) return;
  if (button.dataset.action === "delete") cards = cards.filter(item => item.id !== card.id);
  if (button.dataset.action === "save") { card.draft = article.querySelector(".draft-text").value; card.status = "Draft"; }
  if (button.dataset.action === "approve") { card.draft = article.querySelector(".draft-text").value; card.status = card.draft.trim() ? "Approved" : "Needs draft text"; }
  if (button.dataset.action === "edit") { card.draft = article.querySelector(".draft-text").value; card.status = "Needs edit"; }
  saveCards();
});
render();
