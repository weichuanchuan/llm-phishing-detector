const uploadForm = document.getElementById("upload-form");
const retrieveForm = document.getElementById("retrieve-form");
const fileInput = document.getElementById("file-input");
const persistToggle = document.getElementById("persist-toggle");
const statusEl = document.getElementById("status");
const reportCard = document.getElementById("report");
const summaryEl = document.getElementById("summary");
const scoreEl = document.getElementById("score");
const metadataEl = document.getElementById("metadata");
const keywordsEl = document.getElementById("keywords");
const headersEl = document.getElementById("headers");
const attachmentsEl = document.getElementById("attachments");
const urlsEl = document.getElementById("urls");
const warningsEl = document.getElementById("warnings");
const rawHeadersEl = document.getElementById("raw-headers");
const riskPill = document.getElementById("risk-pill");
const reportTitle = document.getElementById("report-title");
const uuidInput = document.getElementById("uuid-input");
const feedbackForm = document.getElementById("feedback-form");
const feedbackStatus = document.getElementById("feedback-status");
const ratingEl = document.getElementById("rating");
const commentEl = document.getElementById("comment");
const termSelect = document.getElementById("term-select");
const loadTermBtn = document.getElementById("load-term");
const glossaryBody = document.getElementById("glossary-body");

const API = {
  analyze: (persist) => `/analyze?persist=${persist}`,
  fetch: (uuid) => `/persist/${uuid}`,
  feedback: () => `/feedback`,
  explain: (term) => `/explain/${encodeURIComponent(term)}`,
};

function setStatus(el, message, isError = false) {
  el.textContent = message || "";
  el.style.color = isError ? "var(--danger)" : "var(--muted)";
}

function listToHtml(list, mapItem) {
  return list.length
    ? list.map(mapItem).join("")
    : '<li class="muted">No findings</li>';
}

function renderAnalysis(data) {
  const { uuid, analysis } = data;
  reportTitle.textContent = `Analysis summary (${uuid})`;
  summaryEl.textContent = analysis.summary;
  scoreEl.textContent = `${analysis.score} (${analysis.risk_level})`;
  riskPill.textContent = analysis.risk_level;
  riskPill.style.background = analysis.risk_level === "high" ? "var(--danger)" : "var(--border)";

  metadataEl.innerHTML = "";
  const meta = analysis.metadata || {};
  const metaEntries = {
    Sender: meta.sender,
    Subject: meta.subject,
    "Reply-to": meta.reply_to,
    To: (meta.to || []).join(", "),
    Date: meta.date,
    SPF: meta.spf_record,
    "Nested EML": meta.nested_eml_count,
  };
  Object.entries(metaEntries).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}`.length) {
      metadataEl.insertAdjacentHTML("beforeend", `<dt>${key}</dt><dd>${value}</dd>`);
    }
  });

  keywordsEl.innerHTML = (analysis.keywords || [])
    .map((kw) => `<li>${kw}</li>`)
    .join("");

  headersEl.innerHTML = listToHtml(analysis.header_findings || [], (item) => `<li><strong>${item.header}</strong>: ${item.detail}</li>`);
  attachmentsEl.innerHTML = listToHtml(
    analysis.attachment_findings || [],
    (item) => `<li><strong>${item.filename}</strong>: ${item.detail}</li>`
  );
  urlsEl.innerHTML = listToHtml(
    analysis.urls || [],
    (item) => `<li><strong>${item.url}</strong> — ${item.reason}</li>`
  );
  warningsEl.innerHTML = listToHtml(analysis.warnings || [], (item) => `<li>${item}</li>`);

  rawHeadersEl.textContent = Object.entries(analysis.raw_headers || {})
    .map(([key, value]) => `${key}: ${value}`)
    .join("\n");

  reportCard.classList.remove("hidden");
  feedbackForm.dataset.uuid = uuid;
  feedbackStatus.textContent = "";
}

async function analyzeFile(event) {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) {
    setStatus(statusEl, "Please choose an .eml file", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  setStatus(statusEl, "Uploading and analyzing...");
  try {
    const resp = await fetch(API.analyze(persistToggle.checked), {
      method: "POST",
      body: formData,
    });
    if (!resp.ok) {
      throw new Error(`Analysis failed: ${resp.status}`);
    }
    const payload = await resp.json();
    renderAnalysis(payload);
    setStatus(statusEl, persistToggle.checked ? "Report persisted" : "Analysis complete");
    uuidInput.value = payload.uuid;
  } catch (err) {
    console.error(err);
    setStatus(statusEl, err.message || "Unable to analyze", true);
  }
}

async function retrieveReport(event) {
  event.preventDefault();
  const uuid = uuidInput.value.trim();
  if (!uuid) {
    setStatus(statusEl, "Enter a UUID to fetch a report", true);
    return;
  }
  setStatus(statusEl, "Fetching report...");
  try {
    const resp = await fetch(API.fetch(uuid));
    if (!resp.ok) {
      throw new Error(`Report not found (${resp.status})`);
    }
    const payload = await resp.json();
    renderAnalysis(payload);
    setStatus(statusEl, "Loaded persisted report");
  } catch (err) {
    console.error(err);
    setStatus(statusEl, err.message || "Unable to fetch report", true);
  }
}

function renderRating(max = 5) {
  ratingEl.innerHTML = "";
  for (let i = 1; i <= max; i++) {
    const btn = document.createElement("button");
    btn.textContent = i;
    btn.type = "button";
    btn.addEventListener("click", () => {
      document.querySelectorAll(".rating button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      feedbackForm.dataset.rating = String(i);
    });
    ratingEl.appendChild(btn);
  }
}

async function submitFeedback(event) {
  event.preventDefault();
  const rating = Number(feedbackForm.dataset.rating || 0);
  if (!rating) {
    setStatus(feedbackStatus, "Select a rating first", true);
    return;
  }
  const uuid = feedbackForm.dataset.uuid;
  if (!uuid) {
    setStatus(feedbackStatus, "Run an analysis before sending feedback", true);
    return;
  }
  setStatus(feedbackStatus, "Sending feedback...");
  try {
    const resp = await fetch(API.feedback(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uuid, rating, comment: commentEl.value }),
    });
    if (!resp.ok) {
      throw new Error(`Failed to store feedback (${resp.status})`);
    }
    setStatus(feedbackStatus, "Thanks for the feedback!");
  } catch (err) {
    console.error(err);
    setStatus(feedbackStatus, err.message || "Unable to submit feedback", true);
  }
}

async function loadGlossary(term) {
  glossaryBody.textContent = "Loading...";
  try {
    const resp = await fetch(API.explain(term));
    if (!resp.ok) {
      throw new Error("Unknown term");
    }
    const entry = await resp.json();
    glossaryBody.innerHTML = `
      <article>
        <h4>${entry.term}</h4>
        <p>${entry.explanation}</p>
        <ul class="list">${entry.tips.map((tip) => `<li>${tip}</li>`).join("")}</ul>
      </article>
    `;
  } catch (err) {
    glossaryBody.textContent = err.message || "Unable to load term";
  }
}

renderRating();
loadGlossary(termSelect.value);

uploadForm.addEventListener("submit", analyzeFile);
retrieveForm.addEventListener("submit", retrieveReport);
feedbackForm.addEventListener("submit", submitFeedback);
loadTermBtn.addEventListener("click", () => loadGlossary(termSelect.value));
