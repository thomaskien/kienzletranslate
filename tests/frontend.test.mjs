import assert from "node:assert/strict";
import test from "node:test";

import { GenerationGate, languageDirection, secureUuid } from "../web/assets/frontend-core.js";

test("a response becomes stale as soon as a newer press starts", () => {
  const gate = new GenerationGate();
  const first = gate.next();
  assert.equal(gate.accepts(first), true);
  const second = gate.next();
  assert.equal(gate.accepts(first), false);
  assert.equal(gate.accepts(second), true);
});

test("language direction follows the actual speaker side", () => {
  assert.deepEqual(languageDirection("top", "ukr", "deu"), { source: "ukr", target: "deu" });
  assert.deepEqual(languageDirection("bottom", "ukr", "deu"), { source: "deu", target: "ukr" });
  assert.throws(() => languageDirection("middle", "ukr", "deu"), RangeError);
});

test("UUID fallback produces a version 4 identifier", () => {
  const fakeCrypto = {
    getRandomValues(bytes) {
      bytes.fill(0xab);
      return bytes;
    },
  };
  assert.match(secureUuid(fakeCrypto), /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
});

test("service worker only handles its explicit immutable asset allow-list", async () => {
  const source = await (await import("node:fs/promises")).readFile(new URL("../web/sw.js", import.meta.url), "utf8");
  assert.match(source, /ALLOWED\.has\(url\.pathname\)/);
  assert.doesNotMatch(source, /caches\.put/);
  assert.doesNotMatch(source, /api\.php/);
});

test("automatic language choice consumes one attempt until explicit refresh", async () => {
  const { AutomaticLanguageChoice } = await import("../web/assets/frontend-core.js");
  const choice = new AutomaticLanguageChoice();
  assert.equal(choice.select(), true);
  assert.equal(choice.select(), false);
  assert.equal(choice.canRecord("bottom"), false);
  assert.equal(choice.canRecord("top"), true);
  assert.equal(choice.submit(), true);
  assert.equal(choice.submit(), false);
  assert.equal(choice.canRecord("top"), false);
  choice.finish(); // success, manual override, or failure all consume the offer
  assert.equal(choice.select(), false);
  assert.equal(choice.canRecord("bottom"), true);
  choice.restart();
  assert.equal(choice.select(), true);
  assert.equal(new AutomaticLanguageChoice(false).select(), false);
});

test("pre-roll defaults to 250ms and preserves explicit valid preferences", async () => {
  const { storedPreRoll } = await import("../web/assets/frontend-core.js");
  assert.equal(storedPreRoll(null), 250);
  assert.equal(storedPreRoll("bad"), 250);
  assert.equal(storedPreRoll("1000"), 1000);
  assert.equal(storedPreRoll("0"), 0);
  assert.equal(storedPreRoll("3001"), 250);
});
