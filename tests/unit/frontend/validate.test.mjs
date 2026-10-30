import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { validateWindow } from "../../../frontend/src/validate.js";

const presetRates = [100, 1000, 10000];

async function readFixture(rate) {
  const url = new URL(`../../../frontend/fixtures/window-${rate}.json`, import.meta.url);
  return JSON.parse(await readFile(url, "utf8"));
}

test("cada fixture de preset tiene una ventana válida de 64 pares", async () => {
  for (const rate of presetRates) {
    const fixture = await readFixture(rate);
    assert.equal(validateWindow(fixture, rate), fixture);
    assert.equal(fixture.samples_per_channel, 64);
    assert.equal(fixture.channels.ch1.length, 64);
    assert.equal(fixture.channels.ch2.length, 64);
  }
});

test("acepta ambos orígenes válidos y conserva source", async () => {
  const fixture = await readFixture(1000);
  assert.equal(validateWindow(fixture).source, "simulated");
  assert.equal(validateWindow({ ...fixture, source: "hardware" }).source, "hardware");
});

test("rechaza JSON nulo, campos inválidos y muestras fuera de contrato", async (t) => {
  const fixture = await readFixture(1000);
  const cases = [
    ["null", null],
    ["origen desconocido", { ...fixture, source: "unknown" }],
    ["frecuencia cero", { ...fixture, sample_rate_hz: 0 }],
    ["frecuencia distinta al preset", fixture, 100],
    ["unidad distinta", { ...fixture, unit: "volts" }],
    ["resolución distinta", { ...fixture, adc_resolution_bits: 10 }],
    ["menos de 64 muestras", { ...fixture, samples_per_channel: 63 }],
    ["arreglo con longitud incorrecta", { ...fixture, channels: { ...fixture.channels, ch2: fixture.channels.ch2.slice(1) } }],
    ["muestra negativa", { ...fixture, channels: { ...fixture.channels, ch1: [-1, ...fixture.channels.ch1.slice(1)] } }],
    ["muestra sobre el máximo ADC", { ...fixture, channels: { ...fixture.channels, ch2: [4096, ...fixture.channels.ch2.slice(1)] } }],
    ["muestra no entera", { ...fixture, channels: { ...fixture.channels, ch1: [1.5, ...fixture.channels.ch1.slice(1)] } }],
  ];

  for (const [name, candidate, expectedRate] of cases) {
    await t.test(name, () => assert.throws(() => validateWindow(candidate, expectedRate)));
  }
});
