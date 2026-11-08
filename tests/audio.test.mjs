import assert from "node:assert/strict";
import test from "node:test";

import {
  FrameCapture,
  FrameRingBuffer,
  encodePcm16Wav,
  mapPerformanceTimeToFrame,
  preRollSamples,
} from "../web/assets/audio-core.js";

const sequence = (length, offset = 0) => Float32Array.from({ length }, (_, index) => offset + index);

test("pre-roll boundaries 0/250/1000/3000 ms are exact in samples", () => {
  const sampleRate = 1000;
  for (const milliseconds of [0, 250, 1000, 3000]) {
    const ring = new FrameRingBuffer(4000);
    ring.append(1000, sequence(4000, 1000));
    const capture = new FrameCapture(ring, 5000, preRollSamples(milliseconds, sampleRate));
    capture.ingest(5000, sequence(100, 5000));
    const result = capture.finish(5100);
    assert.equal(result.length, milliseconds + 100, `${milliseconds} ms`);
    assert.equal(result.at(-1), 5099);
    if (milliseconds) assert.equal(result[0], 5000 - milliseconds);
  }
});

test("release boundary slices a worklet block and cancel discards it", () => {
  const ring = new FrameRingBuffer(100);
  ring.append(0, sequence(100));
  const capture = new FrameCapture(ring, 100, 20);
  capture.ingest(96, sequence(32, 96));
  assert.deepEqual([...capture.finish(113)], [...sequence(33, 80)]);

  const cancelled = new FrameCapture(ring, 100, 20);
  cancelled.ingest(100, sequence(10, 100));
  cancelled.cancel();
  assert.equal(cancelled.finish(110), null);
});

test("press boundary slices a block that arrived before the pointer event", () => {
  const ring = new FrameRingBuffer(200);
  ring.append(900, sequence(200, 900));
  const capture = new FrameCapture(ring, 1050, 25);
  capture.ingest(1100, sequence(25, 1100));
  assert.deepEqual([...capture.finish(1110)], [...sequence(85, 1025)]);
});

test("ring buffer preserves the newest samples across wrap-around", () => {
  const ring = new FrameRingBuffer(8);
  ring.append(10, sequence(5, 10));
  ring.append(15, sequence(7, 15));
  const window = ring.read(0, 30);
  assert.equal(window.startFrame, 14);
  assert.deepEqual([...window.samples], [14, 15, 16, 17, 18, 19, 20, 21]);
});

test("frame mapping uses AudioContext/performance clock correlation", () => {
  const context = {
    currentTime: 12,
    sampleRate: 48000,
    getOutputTimestamp: () => ({ contextTime: 10, performanceTime: 1000 }),
  };
  assert.equal(mapPerformanceTimeToFrame(1250, context, () => 1250), 492000);
});

test("WAV header keeps the native sample rate and PCM16 payload length", async () => {
  const blob = encodePcm16Wav(new Float32Array([-1, 0, 1]), 48000);
  const view = new DataView(await blob.arrayBuffer());
  assert.equal(blob.type, "audio/wav");
  assert.equal(view.getUint32(24, true), 48000);
  assert.equal(view.getUint16(22, true), 1);
  assert.equal(view.getUint16(34, true), 16);
  assert.equal(view.getUint32(40, true), 6);
  assert.equal(view.getInt16(44, true), -32768);
  assert.equal(view.getInt16(48, true), 32767);
});
