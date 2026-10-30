import test from "node:test";
import assert from "node:assert/strict";
import { formatTimeMilliseconds, sampleTimeSeconds } from "../../../frontend/src/plot.js";

test("t[i] se calcula como i/fs y distingue último punto de duración nominal", () => {
  for (const [rate, nominalMs] of [[100, 640], [1000, 64], [10000, 6.4]]) {
    assert.equal(sampleTimeSeconds(0, rate), 0);
    assert.equal(sampleTimeSeconds(63, rate), 63 / rate);
    assert.equal(64 / rate * 1000, nominalMs);
    assert.notEqual(sampleTimeSeconds(63, rate) * 1000, nominalMs);
  }
});

test("el eje X muestra etiquetas compactas para los tres presets", () => {
  const tickIndices = [0, 21, 42, 63];
  const cases = [
    [100, ["0", "210", "420", "630"]],
    [1000, ["0", "21", "42", "63"]],
    [10000, ["0", "2,1", "4,2", "6,3"]],
  ];

  for (const [rate, expected] of cases) {
    const labels = tickIndices.map((index) => formatTimeMilliseconds(sampleTimeSeconds(index, rate) * 1000, rate));
    assert.deepEqual(labels, expected);
  }
});

test("el formato retiene precisión para una frecuencia futura de 40 kSa/s", () => {
  const labels = [0, 21, 42, 63].map((index) => formatTimeMilliseconds(sampleTimeSeconds(index, 40000) * 1000, 40000));
  assert.deepEqual(labels, ["0", "0,525", "1,05", "1,575"]);
});
