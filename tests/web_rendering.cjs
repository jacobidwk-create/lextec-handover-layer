// Unit-test the real renderer and click handlers with a small DOM double.
// This does not launch or control a browser.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Element {
  constructor(tag, text = '') { this.tag = tag; this.value = ''; this.text = text; this.children = []; this.listeners = {}; }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute() {}
  addEventListener(event, fn) { this.listeners[event] = fn; }
  get textContent() { return this.text + this.children.map(n => n.textContent || '').join(' '); }
}
const root = new Element('main');
const document = {
  createElement: tag => new Element(tag),
  createTextNode: text => new Element('#text', text),
  getElementById: () => root,
};
const context = { document, Node: Element, URLSearchParams, location: {search: ''}, Date };
context.globalThis = context;
vm.createContext(context);
const original = fs.readFileSync('web/app.js', 'utf8');
const source = original.replace('  init();', `
  globalThis.render = renderReply;
  globalThis.calls = [];
  S.id = "test-session";
  exchange = (...args) => globalThis.calls.push(args);
`);
assert.notEqual(source, original, 'test must intercept startup, not fetch real data');
vm.runInContext(source, context);
const walk = n => [n, ...n.children.flatMap(walk)];
const replies = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const reply of replies) {
  root.children = [];
  context.render(reply);
  for (const section of reply.data.next_steps || []) {
    for (const paragraph of section.paragraphs) assert.ok(root.textContent.includes(paragraph), reply.kind);
    assert.ok(walk(root).some(n => n.tag === 'a' && n.href === section.url), 'source link');
  }
  for (const [key, retry] of [['resume_label', false], ['retry_label', true]]) {
    if (!reply.data[key]) continue;
    const button = walk(root).find(n => n.tag === 'button' && n.textContent === reply.data[key]);
    assert.ok(button, `missing ${key}`);
    button.listeners.click();
    const [path, body] = context.calls.at(-1);
    assert.equal(path, '/api/recover');
    assert.equal(body.id, 'test-session');
    assert.equal(body.retry, retry);
  }
}
console.log(`Rendered ${replies.length} real replies; guidance, source links and recovery handlers passed.`);
