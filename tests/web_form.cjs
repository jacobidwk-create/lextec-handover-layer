// Unit-test the real renderer of web/app.js with a small DOM double: questions as chat
// messages with quick replies, the model-written reply, the urgent notice, the list of
// recorded answers with its change buttons, the hand-over proposal and the late-fee
// result. This does not launch a browser.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Element {
  constructor(tag, text = '') {
    this.tag = tag; this.value = ''; this.text = text; this.children = [];
    this.listeners = {}; this.attributes = {}; this.disabled = false; this.className = '';
  }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  focus() { this.focused = true; }
  addEventListener(event, fn) { this.listeners[event] = fn; }
  get textContent() { return this.text + this.children.map(n => n.textContent || '').join(' '); }
  set textContent(value) { this.text = String(value); this.children = []; }
}
const root = new Element('main');
const document = {
  createElement: tag => new Element(tag),
  createTextNode: text => new Element('#text', text),
  getElementById: () => root,
};
const context = { document, Node: Element, URLSearchParams, location: { search: '' }, Date };
context.globalThis = context;
vm.createContext(context);
const original = fs.readFileSync('web/app.js', 'utf8');
const source = original.replace('  init();', `
  globalThis.render = renderReply;
  globalThis.state = S;
  globalThis.calls = [];
  S.id = "test-session";
  exchange = (...args) => globalThis.calls.push(args);
`);
assert.notEqual(source, original, 'test must intercept startup, not fetch real data');
vm.runInContext(source, context);
const walk = n => [n, ...n.children.flatMap(walk)];
const plain = value => JSON.parse(JSON.stringify(value));
const replies = JSON.parse(fs.readFileSync(0, 'utf8'));
let asked = 0, results = 0, changes = 0, offers = 0, details = 0, numbers = 0;
// The form for name, e-mail address and phone: a yes without the required details is
// not sent; with them, the four values go to the server together with the yes.
const checkContactForm = (reply, now) => {
  const fields = reply.data.contact.fields;
  const inputs = now.filter(n => n.tag === 'input');
  assert.deepEqual(fields.map(f => f.name), ['first_name', 'last_name', 'email', 'phone']);
  assert.equal(inputs.length, fields.length, 'one input per detail');
  for (const f of fields) assert.ok(root.textContent.includes(f.label), f.name);
  assert.ok(root.textContent.includes(reply.data.contact.note), 'who receives the details');
  const yes = now.find(n => n.tag === 'button' && n.textContent.includes(reply.data.yes));
  const before = context.calls.length;
  yes.listeners.click();
  assert.equal(context.calls.length, before, 'a yes without name and e-mail address is not sent');
  const errors = now.filter(n => n.className === 'field-error' && !n.hidden);
  assert.equal(errors.length, 3, 'the three required details are marked');
  inputs.forEach((n, i) => { n.value = ['Max', 'Muster', 'not an address', ''][i]; });
  yes.listeners.click();
  assert.equal(context.calls.length, before, 'an unusable e-mail address is not sent');
  inputs[2].value = ' max.muster@example.org ';
  yes.listeners.click();
  const [path, body] = context.calls.at(-1);
  assert.equal(path, '/api/handover');
  assert.deepEqual(plain(body), { id: 'test-session', accept: true, contact: {
    first_name: 'Max', last_name: 'Muster', email: 'max.muster@example.org', phone: '' } });
  details += 1;
};
for (const reply of replies) {
  root.children = [];
  context.state.form = null;
  context.render(reply);
  const nodes = walk(root);
  const text = root.textContent;

  if (reply.kind === 'ask') {
    assert.equal(nodes.filter(n => n.tag === 'select').length, 0, 'a chat, not a form');
    const chips = nodes.filter(n => n.tag === 'button' && n.className.startsWith('quick-reply'));
    let offset = 0;
    for (const q of reply.data.questions) {
      // The message asks the question: in the model's words, or the fixed wording.
      assert.ok(text.includes(q.asked || q.question), 'the question is part of the message');
      assert.ok(text.includes(q.why), 'why the question is asked');
      for (const term of q.terms || []) {
        assert.ok(text.includes(term.title) && text.includes(term.text), `term ${term.topic}`);
        if (term.url) assert.ok(nodes.some(n => n.tag === 'a' && n.href === term.url), 'term source');
      }
      if (!q.options) continue;
      // One quick reply per listed answer, "I do not know" last, in the listed order.
      const mine = chips.slice(offset, offset + q.options.length);
      offset += q.options.length;
      assert.deepEqual(mine.map(c => c.textContent), q.options.map(o => o.label));
      // Marked in advance only if the system understood it and asks for confirmation.
      const marked = mine.filter(c => c.className.includes('marked'));
      assert.equal(marked.length, q.understood ? 1 : 0);
      if (q.understood) {
        assert.equal(marked[0].textContent, q.options.find(o => o.value === q.understood).label);
        assert.ok(text.includes(q.confirm_note), 'confirmation note');
      }
      // One tap answers: the value goes to the server, the wording into the bubble.
      mine[1].listeners.click();
      const [path, body, shown] = context.calls.at(-1);
      assert.equal(path, '/api/answers');
      assert.deepEqual(plain(body), { id: 'test-session', answers: { [q.name]: q.options[1].value } });
      assert.equal(shown, q.options[1].label);
      asked += 1;
    }
    assert.equal(offset, chips.length, 'no other quick replies');
    assert.ok(nodes.some(n => n.tag === 'details'), 'help is folded');
    // Demo: the prepared answer is marked and can be played automatically.
    const first = reply.data.questions.find(q => q.options);
    if (first) {
      root.children = [];
      first.prepared = first.options[0].value;      // as the server marks it in demo mode
      context.state.busy = true;            // a reply is drawn while the request is busy
      context.render(reply);
      context.state.busy = false;
      const prepared = walk(root).filter(n => n.tag === 'button' && n.className.includes('marked'));
      assert.equal(prepared[0].textContent, first.options[0].label);
      assert.equal(prepared[0].disabled, false);
      assert.ok(context.state.form.ready());
      context.state.form.submit();
      assert.deepEqual(plain(context.calls.at(-1)[1].answers), { [first.name]: first.options[0].value });
      root.children = [];
      delete first.prepared;
      context.render(reply);
    }
  }

  // Parts that every kind of reply can carry.
  const now = walk(root), nowText = root.textContent;
  for (const seg of reply.data.segments || []) {
    assert.ok(nowText.includes(seg.text), 'model-written segment');
    if (seg.type === 'legal') {
      assert.ok(now.some(n => n.tag === 'a' && n.href === seg.url), 'source of a legal statement');
    }
  }
  for (const step of reply.data.next_steps || []) {
    assert.ok(nowText.includes(step.title), 'urgent notice');
    for (const paragraph of step.paragraphs) assert.ok(nowText.includes(paragraph));
  }
  const understood = reply.data.understood;
  if (understood && understood.items.length) {
    for (const item of understood.items) assert.ok(nowText.includes(item.value), 'recorded answer');
    const revisable = understood.items.filter(x => x.revisable);
    const buttons = now.filter(n => n.tag === 'button' && n.textContent === understood.change);
    assert.equal(buttons.length, revisable.length, 'one change button per list answer');
    if (buttons.length) {
      buttons[0].listeners.click();
      const [path, body] = context.calls.at(-1);
      assert.equal(path, '/api/revise');
      assert.deepEqual(plain(body), { id: 'test-session', name: revisable[0].name });
      changes += 1;
    }
  }
  if (reply.kind === 'refer_offer') {
    assert.ok(nowText.includes(reply.data.conditions) && nowText.includes(reply.data.conditions_title),
      'conditions of LexTec');
    for (const reason of reply.data.reasons) assert.ok(nowText.includes(reason));
    // The main rules of LexTec's terms in plain words, and the link to the full text.
    assert.equal(reply.data.rules.length, 6);
    for (const rule of reply.data.rules) assert.ok(nowText.includes(rule), 'rule of the terms');
    assert.ok(now.some(n => n.tag === 'a' && n.href === reply.data.terms_url), 'link to the terms');
    checkContactForm(reply, now);
    offers += 1;
  }
  if (reply.kind === 'handover_contact') {
    assert.ok(nowText.includes(reply.data.message), 'nothing was passed on yet');
    for (const problem of reply.data.problems) assert.ok(nowText.includes(problem));
    checkContactForm(reply, now);
  }
  if (reply.kind === 'refer' && reply.data.case_number) {
    assert.ok(nowText.includes(reply.data.case_number), 'the case number is shown');
    assert.ok(nowText.includes(reply.data.case_number_label));
    assert.ok(nowText.includes(reply.data.case_number_note));
    numbers += 1;
  }
  if (reply.kind === 'proceed') {
    const a = reply.data.assessment;
    assert.ok(a && a.positions.length, 'the reply carries the result');
    assert.ok(nowText.includes(a.title) && nowText.includes(a.basis));
    for (const p of [...a.positions, ...a.notes]) {
      assert.ok(nowText.includes(p.title) && nowText.includes(p.text), p.key);
      if (p.verdict_label) assert.ok(nowText.includes(p.verdict_label), p.key);
      for (const c of p.citations) {
        assert.ok(now.some(n => n.tag === 'a' && n.href === c.url), `source of ${p.key}`);
      }
    }
    assert.ok(!nowText.includes(reply.data.class_title), 'no empty model section for late fees');
    results += 1;
  }
}
assert.ok(asked >= 2 && (results >= 1 || offers >= 1));
console.log(`Rendered ${asked} questions with quick replies, ${results} late-fee results, ` +
  `${offers} hand-over proposals; ${changes} change buttons clicked; all handlers passed.`);
console.log(JSON.stringify({ offers, details, numbers }));
