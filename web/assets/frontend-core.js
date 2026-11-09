export class GenerationGate {
  constructor() {
    this.current = 0;
  }

  next() {
    this.current += 1;
    return this.current;
  }

  accepts(generation) {
    return generation === this.current;
  }
}

export function languageDirection(side, topLanguage, bottomLanguage) {
  if (side === "top") return { source: topLanguage, target: bottomLanguage };
  if (side === "bottom") return { source: bottomLanguage, target: topLanguage };
  throw new RangeError("Unbekannte Sprecherseite.");
}

export function secureUuid(cryptoObject = globalThis.crypto) {
  if (typeof cryptoObject?.randomUUID === "function") return cryptoObject.randomUUID();
  const bytes = new Uint8Array(16);
  cryptoObject.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, "0"));
  return `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-${hex.slice(6, 8).join("")}-${hex.slice(8, 10).join("")}-${hex.slice(10).join("")}`;
}

// One choice arms one recording. Only an explicit restart restores the offer.
export class AutomaticLanguageChoice {
  constructor(available = true) {
    this.available = available;
    this.armed = false;
    this.pending = false;
  }
  select() {
    if (!this.available) return false;
    this.available = false;
    this.armed = true;
    this.pending = false;
    return true;
  }
  canRecord(side) {
    return !this.pending && (!this.armed || side === "top");
  }
  submit() {
    if (!this.armed) return false;
    this.armed = false;
    this.pending = true;
    return true;
  }
  finish() { this.armed = false; this.pending = false; }
  restart() { this.finish(); this.available = true; }
}

export function storedPreRoll(raw) {
  if (raw === null) return 250;
  const value = Number(raw);
  return Number.isInteger(value) && value >= 0 && value <= 3000 && value % 250 === 0 ? value : 250;
}
