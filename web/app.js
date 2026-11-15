/* Web page of the hand-over prototype.
   The page only displays what the server returns. It decides nothing about a case.
   All texts that come from the server or the user are inserted as plain text
   (textContent), never as HTML. */
(() => {
  "use strict";

  // ---------------------------------------------------------------- icons
  const ICONS = {
    message: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M8 9h8"/><path d="M8 13h5"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    "arrow-up": '<path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v5h5"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    restart: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    link: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    route: '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  };

  // ---------------------------------------------------------------- texts of the page
  const I18N = {
    de: {
      brand_tag: "Challenge-Prototyp",
      nav_how: "Wie funktioniert es?", nav_topics: "Wobei wir helfen", nav_know: "Was Sie wissen sollten",
      lang_label: "Sprache",
      pill1: "Zugang zum Recht", pill2: "Für Hilfesuchende",
      h1a: "Klarheit bei Schulden.", h1b: "Digital & Persönlich.",
      lead: "Mahnung, Inkassogebühren, Zahlungsbefehl, ein Eintrag im Betreibungsregister oder Schulden aus einer Erbschaft: Schildern Sie Ihr Anliegen in eigenen Worten. Sie erhalten eine erste Einordnung. Einfach zugänglich, zuvorkommend und unkompliziert.",
      how_title: "So funktioniert es",
      how: [
        ["Anliegen schildern", "In Ihren eigenen Worten. Fachbegriffe brauchen Sie keine."],
        ["Rückfragen statt Annahmen", "Fehlt eine Angabe, fragt das System im Gespräch nach, eine Frage nach der anderen. Sie antworten in eigenen Worten oder tippen auf eine vorgeschlagene Antwort; Fachbegriffe sind erklärt."],
        ["Einordnung oder Übergabe", "Sie erhalten eine allgemeine Einordnung mit Quellen. Drängt eine Frist oder ist der Fall heikel, schlägt das System die Übergabe an eine:n Rechtsberater:in vor. Übergeben wird nur mit Ihrer Zustimmung."],
      ],
      start_title: "Sie wissen nicht, wo Sie anfangen sollen?",
      start_text: "Beschreiben Sie Ihr Anliegen. Das System fragt nach, was fehlt, und sagt Ihnen offen, wann ein Mensch übernehmen sollte.",
      start_btn: "Anliegen schildern",
      start_note: "Unverbindlich. Das Gespräch begründet kein Mandat und wahrt keine Fristen.",
      topics_lead: "Vier Themen rund um Schulden. Klar abgegrenzt.",
      know_lead: "Transparent und fair. Keine versteckten Annahmen.",
      chat_title: "Ersteinschätzung", chat_sub: "KI-System, kein Mensch",
      btn_human: "Mit einem Menschen sprechen", btn_restart: "Neu beginnen",
      human_bubble: "Ich möchte mit einer Rechtsberaterin oder einem Rechtsberater sprechen.",
      placeholder: "Ihre Antwort oder Nachricht …",
      hint: "Enter sendet. Shift + Enter für eine neue Zeile.",
      typing: "Ich lese Ihre Nachricht und prüfe, was noch fehlt …",
      examples_label: "Beispiele zum Ausprobieren",
      demo_examples_label: "Beispiel wählen",
      demo_banner: "Demo-Modus: Die Antworten des Sprachmodells sind aufgezeichnet, die Nachrichten und das Datum ({today}) sind vorgegeben. Regeln, Fristen und Briefing werden echt berechnet.",
      script_label: "Vorgegebene Nachricht (Demo)",
      demo_done: "Dieses Beispiel ist zu Ende.",
      form_pending: "Bitte tippen Sie oben auf eine Antwort.",
      closed_note: "Dieses Gespräch ist abgeschlossen. Ihr Anliegen wurde an unser Team übergeben.",
      panel_toggle: "Entscheidweg",
      panel_eyebrow: "Transparenz",
      panel_title: "So hat das System entschieden",
      panel_note: "Die Route bestimmt ein fester Regelkatalog. Das Sprachmodell liest nur die Angaben aus Ihren Nachrichten.",
      panel_empty: "Sobald eine Nachricht gesendet ist, sehen Sie hier, welche Regeln greifen und worauf sie sich stützen.",
      sec_route: "Route", sec_rules: "Ausgelöste Regeln", sec_deadlines: "Fristen",
      sec_facts: "Gesicherte Angaben", sec_open: "Noch offen", sec_contra: "Widersprüche",
      sec_audit: "Protokoll der Prüfschritte", sec_briefing: "Briefing für die Rechtsberater:innen",
      briefing_note: "Diese Zusammenfassung geht an das Postfach von LexTec. Hilfesuchende sehen sie nicht; hier ist sie zur Demonstration eingeblendet.",
      today: "Stichtag", areas: "Themen", rounds: "Rückfragerunden",
      screening_on: "Belastungsprüfung: eingeschaltet", screening_off: "Belastungsprüfung: ausgeschaltet",
      urgent: "Dringend", your_words: "Ihre Worte",
      days_left: "{n} Arbeitstag(e) verbleibend", passed: "möglicherweise abgelaufen", done: "erledigt",
      earliest: "frühestes Ende",
      refer_title: "An unser Team übergeben", refer_title_urgent: "Dringend an unser Team übergeben",
      offer_title: "Vorschlag: Übergabe an unser Team", offer_title_urgent: "Dringend: Übergabe an unser Team empfohlen",
      declined_title: "Nichts weitergegeben",
      offer_pending: "Bitte wählen Sie oben «Ja» oder «Nein».",
      view_briefing: "Briefing ansehen", view_decision: "Entscheidweg ansehen",
      source: "Quelle",
      footer: "Studentischer Prototyp für die LexTec AI Challenge. Kein offizielles Angebot von LexTec Rechtsberatung und keine Rechtsberatung.",
      error: "Das hat leider nicht funktioniert. Bitte versuchen Sie es noch einmal.",
      send: "Senden", close: "Schliessen", skip: "Zum Inhalt",
    },
    en: {
      brand_tag: "Challenge prototype",
      nav_how: "How does it work?", nav_topics: "What we help with", nav_know: "What you should know",
      lang_label: "Language",
      pill1: "Access to justice", pill2: "For those seeking help",
      h1a: "Clarity on debt.", h1b: "Digital & personal.",
      lead: "A reminder, collection fees, a payment order, an entry in the debt enforcement register or debts from an inheritance: describe your situation in your own words. You receive a first classification. Accessible, attentive, and straightforward.",
      how_title: "How it works",
      how: [
        ["Describe your case", "In your own words. You do not need any legal terms."],
        ["Questions, not assumptions", "If something is missing, the system asks in the conversation, one question at a time. You answer in your own words or tap a suggested answer; legal terms are explained."],
        ["Classification or hand-over", "You receive a general classification with sources. If a deadline is pressing or the case is delicate, the system suggests the hand-over to a legal advisor. Nothing is handed over without your agreement."],
      ],
      start_title: "Not sure where to start?",
      start_text: "Describe your situation. The system asks for what is missing and tells you openly when a human should take over.",
      start_btn: "Describe your case",
      start_note: "No obligation. The conversation does not establish a mandate and does not preserve any deadlines.",
      topics_lead: "Four topics around debt. Clearly defined.",
      know_lead: "Transparent and fair. No hidden assumptions.",
      chat_title: "First assessment", chat_sub: "AI system, not a human",
      btn_human: "Speak to a human", btn_restart: "Start again",
      human_bubble: "I would like to speak to a legal advisor.",
      placeholder: "Your answer or message …",
      hint: "Enter sends. Shift + Enter for a new line.",
      typing: "I am reading your message and checking what is still missing …",
      examples_label: "Examples to try",
      demo_examples_label: "Choose an example",
      demo_banner: "Demo mode: the answers of the language model are recorded, and the messages and the date ({today}) are fixed. Rules, deadlines and the briefing are computed for real.",
      script_label: "Prepared message (demo)",
      demo_done: "This example has ended.",
      form_pending: "Please tap an answer above.",
      closed_note: "This conversation is closed. Your matter has been handed to our team.",
      panel_toggle: "Decision path",
      panel_eyebrow: "Transparency",
      panel_title: "How the system decided",
      panel_note: "The route is set by a fixed catalogue of rules. The language model only reads the facts from your messages.",
      panel_empty: "Once a message is sent, you see here which rules apply and what they rest on.",
      sec_route: "Route", sec_rules: "Rules that fired", sec_deadlines: "Deadlines",
      sec_facts: "Established facts", sec_open: "Still open", sec_contra: "Contradictions",
      sec_audit: "Log of the checks", sec_briefing: "Briefing for the legal advisors",
      briefing_note: "This summary goes to the LexTec inbox. People seeking help do not see it; it is shown here for demonstration.",
      today: "Reference date", areas: "Topics", rounds: "Question rounds",
      screening_on: "Distress check: on", screening_off: "Distress check: off",
      urgent: "Urgent", your_words: "Your words",
      days_left: "{n} working day(s) left", passed: "may already have passed", done: "done",
      earliest: "earliest end",
      refer_title: "Handed to our team", refer_title_urgent: "Urgently handed to our team",
      offer_title: "Suggestion: hand-over to our team", offer_title_urgent: "Urgent: hand-over to our team recommended",
      declined_title: "Nothing was passed on",
      offer_pending: "Please choose 'Yes' or 'No' above.",
      view_briefing: "View briefing", view_decision: "View decision path",
      source: "Source",
      footer: "Student prototype for the LexTec AI Challenge. Not an official service of LexTec Rechtsberatung and not legal advice.",
      error: "Unfortunately that did not work. Please try again.",
      send: "Send", close: "Close", skip: "Skip to content",
    },
  };

  // ---------------------------------------------------------------- state and helpers
  const S = {
    lang: "de", config: null, id: null, busy: false, closed: false, panel: false,
    script: [], scriptIndex: 0, sent: 0, decision: null, briefing: "",
    handover: "", offer: null,
    scripted: false,      // demo: the typed messages are prepared
    form: null,           // the open questions that are answered from a list
  };
  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(location.search);

  function t(key, vars) {
    let s = I18N[S.lang][key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v);
    return s;
  }

  /** Create an element. Children that are strings become text nodes. */
  function el(tag, cls, ...children) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    for (const c of children.flat()) {
      if (c === null || c === undefined || c === false) continue;
      n.append(c instanceof Node ? c : document.createTextNode(String(c)));
    }
    return n;
  }
  function icon(name) {
    const s = el("span", "icon");
    s.setAttribute("aria-hidden", "true");
    s.innerHTML = `<svg viewBox="0 0 24 24">${ICONS[name] || ""}</svg>`; // fixed strings only
    return s;
  }
  function withIcon(name, text, cls) { return el("li", cls, icon(name), el("span", null, text)); }

  async function api(path, body) {
    const res = await fetch(path, body === undefined ? undefined : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // ---------------------------------------------------------------- start page
  function applyTexts() {
    document.documentElement.lang = S.lang;
    document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = t(n.dataset.i18n); });
    document.querySelectorAll("[data-icon]").forEach((n) => {
      n.innerHTML = `<svg viewBox="0 0 24 24">${ICONS[n.dataset.icon] || ""}</svg>`;
      n.setAttribute("aria-hidden", "true");
    });
    document.querySelectorAll(".lang-btn").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.lang === S.lang)));
    $("input").placeholder = t("placeholder");
    $("send-btn").setAttribute("aria-label", t("send"));
    $("panel-close").setAttribute("aria-label", t("close"));
    $("restart-btn").setAttribute("aria-label", t("btn_restart"));
    $("restart-btn").title = t("btn_restart");
    document.querySelector(".skip-link").textContent = t("skip");

    const steps = $("how-steps");
    steps.replaceChildren(...t("how").map(([a, b]) => el("li", null, el("strong", null, a), el("span", null, b))));
  }

  function exampleButton(ex, onClick) {
    const b = el("button", "example", el("strong", null, ex.title), el("span", null, ex.summary));
    b.type = "button";
    b.addEventListener("click", () => onClick(ex));
    return b;
  }

  function renderLanding() {
    const c = S.config, d = c.disclosure;
    $("topics-title").textContent = d.topics_title;
    $("topic-list").replaceChildren(...d.topics.map((x) =>
      el("li", null, el("strong", null, x.title), el("span", null, x.text))));
    $("topics-other").textContent = d.other;
    $("know-title").textContent = d.know_title;
    $("know-list").replaceChildren(...d.know.map((x) => withIcon("check", x)));
    $("consent-label").textContent = c.consent_label;
    $("emergency-note").textContent = d.emergency;

    // Demo mode: a conversation starts from an example; the settings are fixed.
    const banner = t("demo_banner", { today: c.today });
    $("demo-banner").hidden = !c.demo;
    $("demo-banner").textContent = banner;
    $("chat-demo-banner").hidden = !c.demo;
    $("chat-demo-banner").textContent = banner;
    $("consent-row").hidden = c.demo;
    $("start-btn").hidden = c.demo;
    $("start-examples").hidden = !c.demo;
    $("start-examples").replaceChildren(
      el("span", "example-label", t("demo_examples_label")),
      ...c.examples.map((ex) => exampleButton(ex, (e) => startChat(e.id))));
  }

  async function loadConfig() {
    S.config = await api(`/api/config?lang=${S.lang}`);
    applyTexts();
    renderLanding();
  }

  // ---------------------------------------------------------------- conversation
  const messages = () => $("messages");

  function addNode(node) {
    const box = messages();
    box.append(node);
    box.scrollTop = Math.max(0, node.offsetTop - 12);   // start of the new message
    return node;
  }
  function addUser(text) { addNode(el("div", "msg msg-user", text)); }
  function addSystem(...children) { return addNode(el("div", "msg msg-system", ...children)); }
  function bubble(...paragraphs) {
    return el("div", "bubble", ...paragraphs.filter(Boolean).map((p) => (p instanceof Node ? p : el("p", null, p))));
  }

  function showTyping(on) {
    const old = $("typing");
    if (old) old.remove();
    if (!on) return;
    const n = el("div", "typing", el("span", "dots", el("i"), el("i"), el("i")), t("typing"));
    n.id = "typing";
    messages().append(n);
    messages().scrollTop = messages().scrollHeight;
  }

  async function startChat(scenarioId) {
    if (S.busy) return;
    S.busy = true;
    try {
      const r = await api("/api/session", {
        lang: S.lang, consent: $("consent").checked, scenario: scenarioId || null,
      });
      Object.assign(S, { id: r.id, closed: false, script: r.script || [], scriptIndex: 0,
                         sent: 0, decision: null, briefing: "", handover: "", offer: null,
                         scripted: (r.script || []).length > 0, form: null });
      $("landing").hidden = true;
      $("chat-view").hidden = false;
      $("panel-toggle").hidden = false;
      $("header-cta").hidden = true;
      document.querySelector(".lang").hidden = true;
      document.querySelector(".nav").hidden = true;
      document.body.classList.add("in-chat");
      messages().replaceChildren();
      $("route-chip").hidden = true;
      addSystem(bubble(r.welcome, r.start_prompt,
        S.config.demo ? null : el("p", "note", r.consent_ack)));
      renderPanel();
      setPanel(S.panel);
      updateComposer();
      window.scrollTo(0, 0);
      if (!S.script.length) $("input").focus();
    } catch (e) {
      alertError();
    } finally {
      S.busy = false;
      // The composer was drawn while the start was still busy; without this the send
      // button of a prepared example stayed disabled and only the Enter key worked.
      updateComposer();
    }
  }

  function restart() {
    Object.assign(S, { id: null, closed: false, script: [], scriptIndex: 0, sent: 0,
                       decision: null, briefing: "", busy: false, handover: "", offer: null,
                       scripted: false, form: null });
    $("chat-view").hidden = true;
    $("landing").hidden = false;
    $("panel-toggle").hidden = true;
    $("header-cta").hidden = false;
    document.querySelector(".lang").hidden = false;
    document.querySelector(".nav").hidden = false;
    document.body.classList.remove("in-chat");
    window.scrollTo(0, 0);
  }

  function updateComposer() {
    const input = $("input"), form = $("composer");
    const scripted = S.scripted;
    const scriptLeft = scripted && S.scriptIndex < S.script.length;
    form.classList.toggle("closed", S.closed);
    let note = form.querySelector(".closed-note");
    if (note) note.remove();
    if (S.closed) {
      form.append(el("p", "closed-note", t("closed_note")));
    }
    $("script-label").hidden = !(scriptLeft && !S.closed);
    $("script-label").textContent = t("script_label");
    input.readOnly = scripted;
    if (scripted) input.value = scriptLeft ? S.script[S.scriptIndex] : "";
    input.placeholder = scripted && !scriptLeft
      ? t(S.handover === "offered" ? "offer_pending" : S.form ? "form_pending" : "demo_done")
      : t("placeholder");
    autosize();
    $("send-btn").disabled = S.busy || S.closed || !input.value.trim();
    $("human-btn").disabled = S.busy;
    $("human-btn").hidden = S.closed;
    $("composer-hint").hidden = scripted;

    // Live mode: offer the examples until the first message is sent.
    const ex = $("examples");
    const showExamples = !scripted && !S.closed && S.sent === 0 && !S.config.demo;
    ex.hidden = !showExamples;
    if (showExamples) {
      ex.replaceChildren(el("span", "example-label", t("examples_label")),
        ...S.config.examples.map((x) => exampleButton(x, (e) => {
          input.value = e.text; autosize(); updateComposer(); input.focus();
        })));
    }
  }

  function autosize() {
    const input = $("input");
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 144) + "px";
  }

  function alertError() { addSystem(el("div", "box box-red", el("p", null, t("error")))); }

  async function exchange(path, body, userText) {
    if (S.busy || S.closed || !S.id) return;
    S.busy = true;
    // An earlier hand-over proposal can no longer be answered once the conversation moves on.
    document.querySelectorAll(".offer-actions button, .offer-contact input, .recovery-actions button, .answer-form button, .change-btn")
      .forEach((n) => { n.disabled = true; });
    S.form = null;
    addUser(userText);
    S.sent += 1;
    $("input").value = "";
    updateComposer();
    showTyping(true);
    try {
      const r = await api(path, body);
      showTyping(false);
      S.decision = r.decision;
      if (r.briefing) S.briefing = r.briefing;
      S.closed = r.closed;
      S.handover = (r.decision && r.decision.handover) || "";
      if (S.script.length && path === "/api/message") S.scriptIndex += 1;
      renderReply(r);
      renderPanel();
      updateChip();
    } catch (e) {
      showTyping(false);
      alertError();
    } finally {
      S.busy = false;
      updateComposer();
    }
  }
  const send = (text) => exchange("/api/message", { id: S.id, text }, text);
  /** Answers chosen from the lists: {question: value}. No model reads them. */
  const sendAnswers = (answers, shown) => exchange("/api/answers", { id: S.id, answers }, shown);
  /** "That is not right": reopen one list answer. No model reads this. */
  const reviseAnswer = (name, shown) => exchange("/api/revise", { id: S.id, name }, shown);
  const requestHuman = () => exchange("/api/human", { id: S.id }, t("human_bubble"));
  /** contact: first name, surname, e-mail, phone. It goes to our team only, never to a model. */
  const answerHandover = (accept, contact, label) =>
    exchange("/api/handover", { id: S.id, accept, contact: contact || {} }, label);

  function updateChip() {
    const d = S.decision, chip = $("route-chip");
    if (!d || !d.route) { chip.hidden = true; return; }
    chip.hidden = false;
    chip.textContent = (d.urgent ? t("urgent") + " · " : "") + d.route_label;
    chip.className = "chip" + (d.urgent ? " chip-urgent" : d.route === "REFER" ? " chip-refer" : "");
  }

  // ---------------------------------------------------------------- replies
  function renderReply(r) {
    const d = r.data || {};
    if (r.kind === "ask") return renderAsk(d);
    if (r.kind === "proceed") return renderProceed(d, r.text);
    if (r.kind === "refer_offer") return renderOffer(d);
    if (r.kind === "refer") return renderRefer(d);
    if (r.kind === "handover_contact") return renderContactNeeded(d);
    if (r.kind === "refer_declined") return renderDeclined(d);
    if (r.kind === "handover_error") {
      return addSystem(bubble(d.emergency, d.message), ...renderNextSteps(d));
    }
    // "proceed_repeat" and anything unexpected: the model's checked reply, or plain text
    const segments = renderSegments(d);
    const plain = d.message || (segments.length ? "" : r.text || "");
    addSystem(...renderNextSteps(d), ...renderAnswers(d), ...segments,
      plain || d.ack ? bubble(d.ack, ...String(plain).split("\n").filter(Boolean)) : null,
      humanAction());
  }

  /** Answers to questions the user asked: fixed texts chosen by topic, with their source. */
  function renderAnswers(d) {
    return (d.answers || []).map((a) => {
      const box = el("div", "answer", el("h4", null, a.title), el("p", null, a.text));
      if (a.citation) {
        const label = `${t("source")}: ${a.citation}`;
        if (a.url) {
          const link = el("a", "source", icon("link"), el("span", null, label));
          link.href = a.url; link.target = "_blank"; link.rel = "noopener noreferrer";
          box.append(link);
        } else {
          box.append(el("span", "source", label));
        }
      }
      if (a.note) box.append(el("p", "note", a.note));
      return box;
    });
  }

  function renderNextSteps(d) {
    return (d.next_steps || []).map((item) => {
      const box = el("div", "box box-amber", el("h4", null, item.title),
        ...item.paragraphs.map((p) => el("p", null, p)));
      const source = el("a", "source", item.citation);
      source.href = item.url; source.target = "_blank"; source.rel = "noopener noreferrer";
      box.append(source);
      return box;
    });
  }

  function recoveryActions(d) {
    const box = el("div", "recovery-actions");
    if (d.retry_hint) box.append(el("p", null, d.retry_hint));
    if (d.recovery_hint) box.append(el("p", "note", d.recovery_hint));
    [[false, d.resume_label], [true, d.retry_label]].forEach(([retry, label]) => {
      if (!label) return;
      const button = el("button", "btn btn-outline", label);
      button.type = "button";
      button.addEventListener("click", () => exchange("/api/recover", { id: S.id, retry }, label));
      box.append(button);
    });
    return box;
  }

  function humanAction() {
    const b = el("button", "btn btn-outline", icon("user"), el("span", null, t("btn_human")));
    b.type = "button";
    b.addEventListener("click", requestHuman);
    return el("div", "card-actions", b);
  }

  /** A link to the article a text rests on. */
  function sourceLink(citation, url, label) {
    const text = `${label || t("source")}: ${citation}`;
    if (!url) return el("span", "source", text);
    const a = el("a", "source", icon("link"), el("span", null, text));
    a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer";
    return a;
  }

  /** Terms that appear in a question or a result, explained in plain words (fixed texts). */
  function termList(terms, sourceLabel) {
    if (!(terms || []).length) return null;
    const list = el("dl", "term-list");
    terms.forEach((x) => {
      const dd = el("dd", null, el("p", null, x.text));
      if (x.citation) dd.append(sourceLink(x.citation, x.url, sourceLabel));
      list.append(el("dt", null, x.title), dd);
    });
    return list;
  }
  function renderTerms(terms, label, sourceLabel) {
    const list = termList(terms, sourceLabel);
    if (!list) return null;
    return el("details", "terms", el("summary", null, icon("info"), el("span", null, label)), list);
  }

  /** The model-written part of a reply. Every legal statement carries its source; the
      server has already dropped whatever failed the checks. */
  function renderSegments(d) {
    const segments = d.segments || [];
    if (!segments.length) return [];
    const box = el("div", "bubble");
    segments.forEach((s) => {
      if (s.type === "legal") {
        box.append(el("div", "statement", el("p", null, s.text), sourceLink(s.citation, s.url)));
      } else {
        box.append(el("p", null, s.text));
      }
    });
    return [box];
  }

  /** The answers recorded so far, each list answer with a button to change it. */
  function understoodList(u) {
    return el("ul", "understood-list", ...u.items.map((x) => {
      const li = el("li", null, el("span", null, el("b", null, x.label + ": "), x.value));
      if (x.revisable) {
        const b = el("button", "change-btn", u.change);
        b.type = "button";
        b.setAttribute("aria-label", `${u.change}: ${x.label}`);
        b.addEventListener("click", () => reviseAnswer(x.name, `${u.change}: ${x.label}`));
        li.append(b);
      }
      return li;
    }));
  }
  function renderUnderstood(u) {
    if (!u || !(u.items || []).length) return null;
    return el("details", "terms understood",
      el("summary", null, icon("check"), el("span", null, u.label)), understoodList(u));
  }

  /** A question of the intake, as part of the chat. The message asks it (in the model's
      words or the fixed wording). Below it the listed answers are offered as quick
      replies: one tap answers, and nothing has to be tapped, because the person can
      also answer in their own words. No model reads a tapped answer. */
  function renderAsk(d) {
    const nodes = [...renderNextSteps(d), ...renderAnswers(d), ...renderSegments(d)];
    let ready = null;
    (d.questions || []).forEach((q, i) => {
      const lead = i === 0 ? [d.ack, d.intro] : [];
      nodes.push(bubble(...lead, el("p", "asked", q.asked || q.question)));
      const extras = [];
      if ((q.options || []).length) {
        // Chosen in advance: a prepared answer (demo), or what the system understood
        // from the message and asks the person to confirm or correct.
        const marked = q.prepared || q.understood;
        if (q.confirm_note) extras.push(el("p", "confirm-note", q.confirm_note));
        const row = el("div", "quick-replies");
        row.setAttribute("role", "group");
        row.setAttribute("aria-label", q.question);
        q.options.forEach((o) => {
          const chip = el("button", "quick-reply" + (o.value === marked ? " marked" : ""), o.label);
          chip.type = "button";
          const pick = () => sendAnswers({ [q.name]: o.value }, o.label);
          chip.addEventListener("click", pick);
          if (o.value === marked && !ready) ready = pick;
          row.append(chip);
        });
        extras.push(row);
      }
      // Why the question is asked and what its terms mean: folded, one tap away.
      const help = el("details", "terms",
        el("summary", null, icon("info"), el("span", null, d.terms_label || d.why_label)),
        el("div", "help-body",
          el("p", null, el("b", null, d.why_label + " "), q.why),
          termList(q.terms, d.source_label)));
      extras.push(help);
      nodes.push(el("div", "answer-form", ...extras));
    });
    if (ready) S.form = { submit: ready, ready: () => true };
    else if ((d.questions || []).some((q) => (q.options || []).length)) {
      S.form = { submit: () => {}, ready: () => false };
    }
    addSystem(...nodes, renderUnderstood(d.understood));
  }

  function renderProceed(d, fallbackText) {
    if (!d.class_title) {           // no structured data available
      return addSystem(...renderAnswers(d),
        bubble(...String(fallbackText || "").split("\n").filter(Boolean)));
    }
    const card = el("div", "card");
    const facts = d.understood && (d.understood.items || []).length
      ? understoodList(d.understood)
      : el("ul", "fact-list", ...(d.facts || []).map((f) => withIcon("check", f)));
    card.append(el("div", null, el("h4", null, d.facts_title), facts,
      el("p", "note", d.correct_me)));

    const results = d.assessments || (d.assessment ? [d.assessment] : []);
    results.forEach((a) => card.append(renderAssessment(a)));

    const cls = el("div", null, el("h4", null, d.class_title));
    if (d.assessment && !(d.statements || []).length) {
      // Late fees only: the result above is complete; the model drafted nothing.
    } else if ((d.statements || []).length) {
      const list = el("ul");
      d.statements.forEach((s) => {
        const item = el("li", "statement", el("p", null, s.text));
        if (s.url) {
          const a = el("a", "source", icon("link"), el("span", null, `${t("source")}: ${s.citation}`));
          a.href = s.url; a.target = "_blank"; a.rel = "noopener noreferrer";
          item.append(a);
        } else {
          item.append(el("span", "source", `${t("source")}: ${s.citation}`));
        }
        list.append(item);
      });
      cls.append(list);
    } else {
      cls.append(el("div", "box box-plain", el("p", null, d.no_sources)));
    }
    if (!(d.assessment && !(d.statements || []).length)) card.append(cls);

    if ((d.deadlines || []).length) {
      card.append(el("div", "box box-amber",
        el("strong", null, d.deadlines_title),
        ...d.deadlines.map((x) => el("p", null, `${x.label}, ${x.basis}: ${x.due} (${x.state})`))));
    }
    if ((d.open || []).length) {
      card.append(el("div", "box box-plain",
        el("strong", null, d.open_title), ...d.open.map((x) => el("p", null, x))));
    }
    card.append(el("p", "disclaimer", d.disclaimer), humanAction());
    addSystem(...renderNextSteps(d), ...renderAnswers(d), ...renderSegments(d),
      bubble(d.ack, d.intro), card);
  }

  /** Late fees: the result per charge, from fixed rules and fixed texts. */
  function renderAssessment(a) {
    const box = el("div", "assessment", el("h4", null, a.title));
    if (a.summary) box.append(el("p", null, a.summary));
    const item = (p, cls) => {
      const head = el("div", "position-head", el("strong", null, p.title));
      if (p.verdict_label) head.append(el("span", `verdict verdict-${p.verdict}`, p.verdict_label));
      const node = el("div", cls, head, el("p", null, p.text));
      if ((p.citations || []).length) {
        node.append(el("div", "source-row",
          ...p.citations.map((c) => sourceLink(c.citation, c.url, a.source_label))));
      }
      const terms = renderTerms(p.terms, a.terms_label, a.source_label);
      if (terms) node.append(terms);
      return node;
    };
    (a.positions || []).forEach((p) => box.append(item(p, "position")));
    if ((a.notes || []).length) {
      box.append(el("h4", "notes-title", a.notes_title));
      a.notes.forEach((n) => box.append(item(n, "position position-note")));
    }
    box.append(el("p", "note", a.basis));
    return box;
  }

  /** The system proposes the hand-over. Nothing is sent until the user says yes. */
  function renderOffer(d) {
    S.offer = d;
    const card = el("div", "card handover" + (d.urgent ? " urgent" : ""));
    card.append(el("div", "handover-head",
      el("span", "icon-badge", icon(d.urgent ? "alert" : "user")),
      el("h3", null, t(d.urgent ? "offer_title_urgent" : "offer_title"))));
    if (d.emergency) card.append(el("div", "box box-red", el("p", null, d.emergency)));
    card.append(...renderNextSteps(d));
    card.append(el("p", null, d.message));
    if ((d.reasons || []).length) {
      card.append(el("div", null, el("h4", null, d.why_label),
        el("ul", "reason-list", ...d.reasons.map((x) => withIcon(d.urgent ? "clock" : "check", x)))));
    }
    card.append(el("p", "note", d.sent_note));
    if (d.conditions) card.append(conditionsBox(d));
    const understood = renderUnderstood(d.understood);
    if (understood) card.append(understood);

    const form = contactForm(d.contact);
    S.offerForm = form;
    card.append(form.node);

    const yes = el("button", "btn btn-green", icon("check"), el("span", null, d.yes));
    const no = el("button", "btn btn-outline", el("span", null, d.no));
    yes.type = no.type = "button";
    // A yes without name and e-mail address is not sent; the engine checks again.
    yes.addEventListener("click", () => { if (form.check()) answerHandover(true, form.values(), d.yes); });
    no.addEventListener("click", () => answerHandover(false, null, d.no));
    card.append(el("p", "offer-question", d.question), el("div", "card-actions offer-actions", yes, no));
    card.append(recoveryActions(d));
    addSystem(...renderAnswers(d), card);
  }

  /** LexTec's prices, the main rules of its terms in plain words, and the link to the full text. */
  function conditionsBox(d) {
    const box = el("div", "box box-plain conditions",
      el("strong", null, d.conditions_title), el("p", null, d.conditions));
    if ((d.rules || []).length) {
      box.append(el("strong", null, d.rules_title),
        el("ul", "rule-list", ...d.rules.map((x) => el("li", null, x))));
    }
    if (d.terms_url) {
      const a = el("a", "source", icon("link"), el("span", null, d.terms_label));
      a.href = d.terms_url; a.target = "_blank"; a.rel = "noopener noreferrer";
      box.append(a);
    }
    return box;
  }

  const EMAIL = /^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$/;
  const AUTOCOMPLETE = { first_name: "given-name", last_name: "family-name", email: "email", phone: "tel" };

  /** First name, surname and e-mail address (required) and phone (optional), asked with
      the hand-over. The values go to our team only. */
  function contactForm(c) {
    const inputs = [];
    const grid = el("div", "contact-grid");
    ((c && c.fields) || []).forEach((f, i) => {
      const input = el("input");
      input.type = f.name === "email" ? "email" : f.name === "phone" ? "tel" : "text";
      input.maxLength = f.max || 200;
      input.autocomplete = AUTOCOMPLETE[f.name] || "off";
      input.id = `contact-${f.name}-${Date.now()}-${i}`;
      const label = el("label", null, f.label);
      label.htmlFor = input.id;
      const error = el("p", "field-error", f.error || "");
      error.id = input.id + "-error";
      error.hidden = !((c.missing || []).includes(f.name));
      if (f.required) input.setAttribute("aria-required", "true");
      input.setAttribute("aria-describedby", error.id);
      input.addEventListener("input", () => { error.hidden = true; input.removeAttribute("aria-invalid"); });
      inputs.push({ f, input, error });
      grid.append(el("div", "contact-field" + (f.name === "email" ? " wide" : ""), label, input, error));
    });
    const node = el("div", "offer-contact", el("h4", null, c ? c.title : ""), grid,
      el("p", "note", c ? c.note : ""));
    const values = () => Object.fromEntries(inputs.map((x) => [x.f.name, x.input.value.trim()]));
    /** Marks what is missing. True if the required details can be sent. */
    const check = () => {
      let first = null;
      inputs.forEach(({ f, input, error }) => {
        const v = input.value.trim();
        const bad = f.required && (f.name === "email" ? !EMAIL.test(v) : !/\p{L}/u.test(v));
        error.hidden = !bad;
        if (bad) { input.setAttribute("aria-invalid", "true"); first = first || input; }
        else input.removeAttribute("aria-invalid");
      });
      if (first) first.focus();
      return !first;
    };
    const fill = (person) => inputs.forEach((x) => { if (person[x.f.name]) x.input.value = person[x.f.name]; });
    return { node, values, check, fill };
  }

  /** The person typed yes, but name or e-mail address is missing. Nothing was passed on. */
  function renderContactNeeded(d) {
    const card = el("div", "card handover" + (d.urgent ? " urgent" : ""));
    if (d.emergency) card.append(el("div", "box box-red", el("p", null, d.emergency)));
    card.append(...renderNextSteps(d));
    card.append(el("p", null, d.message),
      el("ul", "rule-list", ...(d.problems || []).map((x) => el("li", null, x))));
    const form = contactForm(d.contact);
    S.offerForm = form;
    card.append(form.node);
    const yes = el("button", "btn btn-green", icon("check"), el("span", null, d.yes));
    const no = el("button", "btn btn-outline", el("span", null, d.no));
    yes.type = no.type = "button";
    yes.addEventListener("click", () => { if (form.check()) answerHandover(true, form.values(), d.yes); });
    no.addEventListener("click", () => answerHandover(false, null, d.no));
    card.append(el("div", "card-actions offer-actions", yes, no));
    addSystem(card);
  }

  function renderDeclined(d) {
    const card = el("div", "card");
    card.append(el("h3", null, t("declined_title")));
    if (d.emergency) card.append(el("div", "box box-red", el("p", null, d.emergency)));
    card.append(...renderNextSteps(d));
    card.append(el("p", null, d.message));
    (d.deadline_notes || []).forEach((x) => card.append(el("div", "box box-amber", el("p", null, x))));
    card.append(recoveryActions(d), humanAction());
    addSystem(...renderAnswers(d), card);
  }

  function renderRefer(d) {
    const card = el("div", "card handover" + (d.urgent ? " urgent" : ""));
    card.append(el("div", "handover-head",
      el("span", "icon-badge", icon(d.urgent ? "alert" : "user")),
      el("h3", null, t(d.urgent ? "refer_title_urgent" : "refer_title"))));
    card.append(...renderNextSteps(d));
    card.append(el("p", null, d.message));
    if (d.case_number) {
      // The number the person quotes when they ask LexTec about their matter.
      card.append(el("div", "box box-plain case-number",
        el("span", "case-number-label", d.case_number_label),
        el("strong", "case-number-value", d.case_number),
        el("p", "note", d.case_number_note)));
    }
    if ((d.reasons || []).length) {
      card.append(el("div", null, el("h4", null, d.why_label),
        el("ul", "reason-list", ...d.reasons.map((x) => withIcon(d.urgent ? "clock" : "check", x)))));
    }
    if (d.emergency) card.append(el("div", "box box-red", el("p", null, d.emergency)));
    const b = el("button", "btn btn-green", icon("file"), el("span", null, t("view_briefing")));
    b.type = "button";
    b.addEventListener("click", () => {
      setPanel(true);
      const target = $("briefing-section");
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    card.append(el("div", "card-actions", b));
    addSystem(card);
  }

  // ---------------------------------------------------------------- how the system decided
  function setPanel(open) {
    S.panel = open;
    $("panel").hidden = !open;
    $("chat-view").classList.toggle("with-panel", open);
    $("panel-toggle").setAttribute("aria-pressed", String(open));
  }

  function section(title, ...children) {
    return el("div", "psec", el("h3", null, title), ...children);
  }

  function renderPanel() {
    const body = $("panel-body"), d = S.decision;
    if (!d || !d.route) {
      body.replaceChildren(el("p", "panel-empty", t("panel_empty")));
      return;
    }
    const out = [];

    const chips = [el("span", "route-big", d.route_label)];
    if (d.urgent) chips.push(el("span", "chip chip-urgent", t("urgent")));
    const meta = [`${t("today")}: ${d.today}`];
    if (d.areas.length) meta.push(`${t("areas")}: ${d.areas.join(", ")}`);
    meta.push(`${t("rounds")}: ${d.rounds}`);
    meta.push(t(d.consent ? "screening_on" : "screening_off"));
    out.push(section(t("sec_route"), el("div", "route-row", ...chips),
      ...meta.map((m) => el("p", "meta", m))));

    out.push(section(t("sec_rules"), el("ul", null, ...d.reasons.map((r) =>
      el("li", "rule",
        el("div", "route-row", el("span", "chip chip-rule", r.rule), el("span", "rule-title", r.label)),
        r.detail ? el("p", "rule-detail", r.detail) : null,
        r.evidence ? el("p", "quote", `${t("your_words")}: «${r.evidence}»`) : null)))));

    if (d.deadlines.length) {
      out.push(section(t("sec_deadlines"), el("ul", null, ...d.deadlines.map((x) => {
        const state = x.done ? t("done") : x.days_left < 0 ? t("passed") : t("days_left", { n: x.days_left });
        return el("li", "kv",
          el("div", "kv-top", el("span", null, `${x.label} (${x.basis})`), el("span", null, x.due)),
          el("p", "meta", `${t("earliest")} · ${state}`));
      }))));
    }
    if (d.facts.length) {
      out.push(section(t("sec_facts"), el("ul", null, ...d.facts.map((f) =>
        el("li", "kv",
          el("div", "kv-top", el("span", null, f.label), el("span", null, f.value)),
          f.evidence ? el("p", "quote", `«${f.evidence}»`) : null)))));
    }
    if (d.open.length) {
      out.push(section(t("sec_open"), el("ul", null, ...d.open.map((o) =>
        el("li", "kv", el("div", "kv-top", el("span", null, o.label), el("span", null, o.status)))))));
    }
    if (d.contradictions.length) {
      out.push(section(t("sec_contra"), el("ul", null, ...d.contradictions.map((c) => el("li", "quote", c)))));
    }
    if (d.audit.length) {
      const det = el("details", "audit", el("summary", null, `${t("sec_audit")} (${d.audit.length})`),
        el("ul", null, ...d.audit.map((a) => el("li", null, a))));
      out.push(el("div", "psec", det));
    }
    if (S.briefing) {
      const sec = section(t("sec_briefing"), el("p", "meta", t("briefing_note")), renderBriefing(S.briefing));
      sec.id = "briefing-section";
      out.push(sec);
    }
    body.replaceChildren(...out);
  }

  /** Inline bold (**text**) as <strong>; everything else as text. */
  function inline(text) {
    const parts = String(text).split(/\*\*(.+?)\*\*/g);
    return parts.map((p, i) => (i % 2 ? el("strong", null, p) : p)).filter((p) => p !== "");
  }

  /** The briefing is simple Markdown: headings, bullets with indented notes, paragraphs. */
  function renderBriefing(md) {
    const root = el("div", "briefing");
    let list = null, lastItem = null;
    for (const raw of md.split("\n")) {
      const line = raw.replace(/\s+$/, "");
      if (!line.trim()) { list = null; continue; }
      if (line.startsWith("# ")) { list = null; root.append(el("h4", null, line.slice(2))); continue; }
      if (line.startsWith("## ")) { list = null; root.append(el("h5", null, line.slice(3))); continue; }
      if (line.startsWith("- ")) {
        if (!list) { list = el("ul"); root.append(list); }
        lastItem = el("li", null, ...inline(line.slice(2)));
        list.append(lastItem);
        continue;
      }
      if (/^\s{2,}\S/.test(line) && lastItem && list) {
        lastItem.append(el("span", "sub", ...inline(line.trim())));
        continue;
      }
      list = null;
      const text = line.replace(/^_(.*)_$/, "$1");
      root.append(el("p", text !== line ? "meta" : null, ...inline(text)));
    }
    return root;
  }

  // ---------------------------------------------------------------- events
  function bind() {
    $("start-btn").addEventListener("click", () => startChat(null));
    $("header-cta").addEventListener("click", () => {
      if (S.config && S.config.demo) {
        document.querySelector(".start").scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        startChat(null);
      }
    });
    $("restart-btn").addEventListener("click", restart);
    $("human-btn").addEventListener("click", requestHuman);
    $("panel-toggle").addEventListener("click", () => setPanel(!S.panel));
    $("panel-close").addEventListener("click", () => setPanel(false));
    document.querySelectorAll(".lang-btn").forEach((b) => b.addEventListener("click", async () => {
      if (b.dataset.lang === S.lang) return;
      S.lang = b.dataset.lang;
      await loadConfig();
    }));

    const input = $("input");
    input.addEventListener("input", () => { autosize(); updateComposer(); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        $("composer").requestSubmit();
      }
    });
    $("composer").addEventListener("submit", (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (text) send(text);
    });
    window.addEventListener("scroll", () =>
      $("main-header").classList.toggle("scrolled", window.scrollY > 8), { passive: true });
  }

  const DEMO_PERSON = { first_name: "Max", last_name: "Muster", email: "max.muster@example.org" };

  async function autoplay(scenarioId) {
    await startChat(scenarioId);
    for (let i = 0; i < 12 && !S.closed; i += 1) {
      await sleep(900);
      if (S.scriptIndex < S.script.length) await send(S.script[S.scriptIndex]);
      else if (S.form && S.form.ready()) await S.form.submit();
      else break;
    }
    if (S.handover === "offered" && S.offer && S.offerForm) {
      // The automatic demo fills in an invented person so that the hand-over can be shown.
      S.offerForm.fill(DEMO_PERSON);
      await sleep(1800);
      await answerHandover(true, S.offerForm.values(), S.offer.yes);
    }
  }

  async function init() {
    const want = params.get("lang");
    S.lang = want === "en" || want === "de" ? want
      : (navigator.language || "de").toLowerCase().startsWith("de") ? "de" : "en";
    S.panel = params.get("panel") === "1";
    bind();
    applyTexts();
    try {
      await loadConfig();
    } catch (e) {
      document.querySelector(".start-text").textContent = t("error");
      return;
    }
    if (params.get("autoplay")) autoplay(params.get("autoplay"));
  }

  init();
})();
