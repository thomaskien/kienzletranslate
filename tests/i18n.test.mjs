import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  COMMON_IN_GERMANY,
  MESSAGES,
  MODEL_TO_BCP47,
  groupLanguages,
} from "../web/assets/i18n.js";

const languages = JSON.parse(await readFile(new URL("../backend/languages.json", import.meta.url), "utf8"));

test("German and English dictionaries contain exactly the same UI keys", () => {
  assert.deepEqual(Object.keys(MESSAGES.en).sort(), Object.keys(MESSAGES.de).sort());
  assert.ok(Object.keys(MESSAGES.de).length > 50);
});

test("localized language groups retain every supplied model code exactly once", () => {
  const suppliedCodes = languages.map(({ code }) => code).sort();
  for (const locale of ["de", "en"]) {
    const groups = groupLanguages(languages, locale);
    const groupedCodes = [...groups.common, ...groups.other].map(({ code }) => code).sort();
    assert.deepEqual(groupedCodes, suppliedCodes);
    assert.deepEqual(groups.common.map(({ code }) => code).sort(), COMMON_IN_GERMANY.filter((code) => suppliedCodes.includes(code)).sort());
    assert.ok(groups.common.length > 0);
    assert.ok(groups.other.length > 0);
    for (const language of languages) assert.ok(MODEL_TO_BCP47[language.code], `missing BCP47 mapping for ${language.code}`);
  }
});
