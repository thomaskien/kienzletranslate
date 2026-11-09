import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  COMMON_IN_GERMANY,
  MESSAGES,
  MODEL_TO_BCP47,
  UI_LANGUAGES,
  UI_LOCALES,
  groupLanguages,
  interfaceChoice,
  isRtlLocale,
  languageFlag,
} from "../web/assets/i18n.js";

const languages = JSON.parse(await readFile(new URL("../backend/languages.json", import.meta.url), "utf8"));

test("all 18 interface dictionaries contain every message and preserve placeholders", () => {
  assert.equal(UI_LOCALES.length, 18);
  assert.deepEqual(Object.keys(MESSAGES).sort(), [...UI_LOCALES].sort());
  const placeholders = (text) => [...text.matchAll(/\{\w+\}/g)].map(([match]) => match).sort();
  for (const locale of UI_LOCALES) {
    assert.deepEqual(Object.keys(MESSAGES[locale]).sort(), Object.keys(MESSAGES.de).sort());
    for (const [key, value] of Object.entries(MESSAGES[locale])) {
      assert.equal(typeof value, "string", `${locale}.${key}`);
      assert.ok(value.trim(), `${locale}.${key}`);
      assert.deepEqual(placeholders(value), placeholders(MESSAGES.en[key]), `${locale}.${key}`);
    }
  }
  assert.ok(Object.keys(MESSAGES.de).length > 50);
});

test("localized language groups retain every supplied model code exactly once", () => {
  const suppliedCodes = languages.map(({ code }) => code).sort();
  for (const locale of UI_LOCALES) {
    const groups = groupLanguages(languages, locale);
    const groupedCodes = [...groups.common, ...groups.other].map(({ code }) => code).sort();
    assert.deepEqual(groupedCodes, suppliedCodes);
    assert.deepEqual(groups.common.map(({ code }) => code).sort(), COMMON_IN_GERMANY.filter((code) => suppliedCodes.includes(code)).sort());
    assert.ok(groups.common.length > 0);
    assert.ok(groups.other.length > 0);
    for (const language of languages) assert.ok(MODEL_TO_BCP47[language.code], `missing BCP47 mapping for ${language.code}`);
  }
});

test("each interface flag selects one supported user language", () => {
  assert.deepEqual(UI_LANGUAGES.map(({ code }) => code).sort(), [...COMMON_IN_GERMANY].sort());
  for (const language of UI_LANGUAGES) {
    assert.ok(languages.some(({ code }) => code === language.code));
    assert.equal(interfaceChoice(language.locale).code, language.code);
    assert.equal(languageFlag(language.code), language.flag);
    assert.ok(language.name);
  }
  assert.equal(interfaceChoice("unsupported").code, "deu");
  assert.deepEqual(UI_LOCALES.filter(isRtlLocale), ["ar", "ckb", "fa"]);
  for (const language of languages) assert.notEqual(languageFlag(language.code), "🌐", language.code);
});
