const concatFloat32 = (parts) => {
  const length = parts.reduce((total, part) => total + part.length, 0);
  const joined = new Float32Array(length);
  let offset = 0;
  for (const part of parts) {
    joined.set(part, offset);
    offset += part.length;
  }
  return joined;
};

export function preRollSamples(milliseconds, sampleRate) {
  if (!Number.isFinite(milliseconds) || milliseconds < 0 || milliseconds > 3000) {
    throw new RangeError("Der Vorlauf muss zwischen 0 und 3000 ms liegen.");
  }
  if (!Number.isFinite(sampleRate) || sampleRate <= 0) {
    throw new RangeError("Ungültige Abtastrate.");
  }
  return Math.round((milliseconds * sampleRate) / 1000);
}

/** A fixed-size PCM ring whose positions use the AudioWorklet frame clock. */
export class FrameRingBuffer {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 1) throw new RangeError("capacity");
    this.capacity = capacity;
    this.samples = new Float32Array(capacity);
    this.length = 0;
    this.writeIndex = 0;
    this.endFrame = null;
  }

  clear() {
    this.length = 0;
    this.writeIndex = 0;
    this.endFrame = null;
  }

  append(startFrame, input) {
    if (!(input instanceof Float32Array) || input.length === 0) return;
    if (!Number.isInteger(startFrame)) throw new TypeError("startFrame");

    let data = input;
    let frame = startFrame;
    if (this.endFrame !== null && frame !== this.endFrame) {
      if (frame < this.endFrame) {
        const overlap = this.endFrame - frame;
        if (overlap >= data.length) return;
        data = data.subarray(overlap);
        frame += overlap;
      } else {
        this.clear();
      }
    }
    if (data.length >= this.capacity) {
      data = data.subarray(data.length - this.capacity);
      frame = startFrame + input.length - data.length;
      this.samples.set(data, 0);
      this.length = this.capacity;
      this.writeIndex = 0;
      this.endFrame = frame + data.length;
      return;
    }
    const first = Math.min(data.length, this.capacity - this.writeIndex);
    this.samples.set(data.subarray(0, first), this.writeIndex);
    if (first < data.length) this.samples.set(data.subarray(first), 0);
    this.writeIndex = (this.writeIndex + data.length) % this.capacity;
    this.length = Math.min(this.capacity, this.length + data.length);
    this.endFrame = frame + data.length;
  }

  read(startFrame, endFrame) {
    if (this.endFrame === null || endFrame <= startFrame || this.length === 0) {
      return { startFrame: endFrame, samples: new Float32Array() };
    }
    const availableStart = this.endFrame - this.length;
    const from = Math.max(startFrame, availableStart);
    const to = Math.min(endFrame, this.endFrame);
    if (to <= from) return { startFrame: to, samples: new Float32Array() };

    const count = to - from;
    const result = new Float32Array(count);
    const oldestIndex = (this.writeIndex - this.length + this.capacity) % this.capacity;
    const readIndex = (oldestIndex + (from - availableStart)) % this.capacity;
    const first = Math.min(count, this.capacity - readIndex);
    result.set(this.samples.subarray(readIndex, readIndex + first), 0);
    if (first < count) result.set(this.samples.subarray(0, count - first), first);
    return { startFrame: from, samples: result };
  }
}

/** Collects frame-stamped blocks and slices both press and release boundaries. */
export class FrameCapture {
  constructor(ring, startFrame, preRollLength) {
    this.startFrame = Math.round(startFrame);
    this.windowStart = this.startFrame - preRollLength;
    this.cancelled = false;
    this.segments = [];
    // The port may already have delivered a block straddling the pointer boundary.
    // Keep that post-boundary portion too; finish() will still cut at release.
    const snapshotEnd = Math.max(this.startFrame, ring.endFrame ?? this.startFrame);
    const prefix = ring.read(this.windowStart, snapshotEnd);
    if (prefix.samples.length) this.segments.push(prefix);
  }

  ingest(startFrame, input) {
    if (this.cancelled || !(input instanceof Float32Array) || input.length === 0) return;
    const endFrame = startFrame + input.length;
    const from = Math.max(startFrame, this.windowStart);
    if (endFrame <= from) return;
    this.segments.push({
      startFrame: from,
      samples: input.slice(from - startFrame),
    });
  }

  cancel() {
    this.cancelled = true;
    this.segments.length = 0;
  }

  finish(endFrame) {
    if (this.cancelled) return null;
    const boundary = Math.max(this.startFrame, Math.round(endFrame));
    const ordered = this.segments
      .map((segment) => {
        const from = Math.max(this.windowStart, segment.startFrame);
        const to = Math.min(boundary, segment.startFrame + segment.samples.length);
        return to > from
          ? { startFrame: from, samples: segment.samples.subarray(from - segment.startFrame, to - segment.startFrame) }
          : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.startFrame - b.startFrame);

    const parts = [];
    let cursor = this.windowStart;
    for (const segment of ordered) {
      const skip = Math.max(0, cursor - segment.startFrame);
      if (skip >= segment.samples.length) continue;
      parts.push(segment.samples.subarray(skip));
      cursor = segment.startFrame + segment.samples.length;
    }
    return concatFloat32(parts);
  }
}

export function mapPerformanceTimeToFrame(eventTime, context, performanceNow) {
  let pointerTime = Number(eventTime);
  const now = performanceNow();
  // Older WebKit versions may expose an epoch-based Event.timeStamp.
  if (pointerTime > now + 60_000 && typeof performance.timeOrigin === "number") {
    pointerTime -= performance.timeOrigin;
  }
  let contextTime;
  const stamp = typeof context.getOutputTimestamp === "function" ? context.getOutputTimestamp() : null;
  if (stamp && Number.isFinite(stamp.contextTime) && Number.isFinite(stamp.performanceTime)) {
    contextTime = stamp.contextTime + (pointerTime - stamp.performanceTime) / 1000;
  } else {
    contextTime = context.currentTime + (pointerTime - now) / 1000;
  }
  return Math.max(0, Math.round(contextTime * context.sampleRate));
}

export function encodePcm16Wav(samples, sampleRate) {
  if (!(samples instanceof Float32Array)) throw new TypeError("samples");
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const ascii = (offset, value) => {
    for (let i = 0; i < value.length; i += 1) view.setUint8(offset + i, value.charCodeAt(i));
  };
  ascii(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  ascii(8, "WAVE");
  ascii(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  ascii(36, "data");
  view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}
