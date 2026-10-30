import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

class FakeElement {
  constructor() {
    this.value = "";
    this.textContent = "";
    this.dataset = {};
    this.hidden = false;
    this.children = [];
    this.listeners = new Map();
    this.classes = new Set();
    this.classList = {
      add: (name) => this.classes.add(name),
      remove: (name) => this.classes.delete(name),
      contains: (name) => this.classes.has(name),
    };
  }

  addEventListener(name, listener) { this.listeners.set(name, listener); }
  replaceChildren(...children) { this.children = children; }
  append(...children) { this.children.push(...children); }
  setAttribute() {}
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

const flushAsync = () => new Promise((resolve) => setImmediate(resolve));

test("la vista previa usa N real y descarta respuestas y errores de solicitudes anteriores", async () => {
  const previousDocument = globalThis.document;
  const previousFetch = globalThis.fetch;
  const ids = [
    "sample-rate", "window-state", "error-message", "plot-ch1", "plot-ch2",
    "source-badge", "source-label", "source-description", "sample-count",
    "sample-rate-value", "window-span", "adc-resolution", "plot-note", "window-message",
  ];
  const elements = new Map(ids.map((id) => ["#" + id, new FakeElement()]));
  const select = elements.get("#sample-rate");
  select.value = "1000";
  const pending = [];

  globalThis.document = {
    querySelector: (selector) => {
      assert.ok(elements.has(selector), "Selector no simulado: " + selector);
      return elements.get(selector);
    },
    createElementNS: () => new FakeElement(),
  };
  globalThis.fetch = (url) => {
    const request = { url: String(url), ...deferred() };
    pending.push(request);
    return request.promise;
  };

  try {
    const fixture1000 = JSON.parse(await readFile(new URL("../../../frontend/fixtures/window-1000.json", import.meta.url), "utf8"));
    const fixture10000 = JSON.parse(await readFile(new URL("../../../frontend/fixtures/window-10000.json", import.meta.url), "utf8"));

    await import("../../../frontend/src/main.js?preview-race-test");
    assert.equal(pending.length, 1);
    assert.equal(elements.get("#window-state").dataset.viewState, "loading");
    assert.equal(elements.get("#sample-count").textContent, "—");

    select.value = "10000";
    select.listeners.get("change")();
    assert.equal(pending.length, 2);
    assert.equal(elements.get("#window-state").dataset.viewState, "loading");
    assert.equal(elements.get("#plot-ch1").children.length, 0);
    assert.equal(elements.get("#window-span").textContent, "—");

    const extended = {
      ...fixture10000,
      window_id: 33,
      samples_per_channel: 128,
      channels: {
        ch1: [...fixture10000.channels.ch1, ...fixture10000.channels.ch1],
        ch2: [...fixture10000.channels.ch2, ...fixture10000.channels.ch2],
      },
    };
    pending[1].resolve({ ok: true, json: async () => extended });
    await flushAsync();

    assert.equal(elements.get("#sample-count").textContent, 128);
    assert.equal(elements.get("#window-state").dataset.viewState, "ready");
    assert.ok(elements.get("#plot-ch1").children.length > 0);
    assert.equal(elements.get("#window-span").textContent, "12,8 ms");
    assert.match(elements.get("#plot-note").textContent, /0 a 12,7 ms.*12,8 ms \(128 periodos\)/);
    assert.equal(elements.get("#window-state").textContent, "Ventana 33 · 128 muestras");

    pending[0].resolve({ ok: true, json: async () => fixture1000 });
    await flushAsync();
    assert.equal(elements.get("#window-state").textContent, "Ventana 33 · 128 muestras");
    assert.equal(elements.get("#window-span").textContent, "12,8 ms");
    assert.match(elements.get("#plot-note").textContent, /0 a 12,7 ms.*12,8 ms \(128 periodos\)/);

    select.value = "100";
    select.listeners.get("change")();
    select.value = "1000";
    select.listeners.get("change")();
    assert.equal(pending.length, 4);

    pending[3].resolve({ ok: true, json: async () => fixture1000 });
    await flushAsync();
    assert.equal(elements.get("#window-state").textContent, "Ventana " + fixture1000.window_id + " · 64 muestras");
    assert.match(elements.get("#plot-note").textContent, /0 a 63 ms.*64 ms \(64 periodos\)/);

    pending[2].reject(new Error("Fallo tardío de red"));
    await flushAsync();
    assert.equal(elements.get("#window-state").textContent, "Ventana " + fixture1000.window_id + " · 64 muestras");
    assert.match(elements.get("#plot-note").textContent, /0 a 63 ms.*64 ms \(64 periodos\)/);
    assert.equal(elements.get("#window-message").hidden, true);
    assert.equal(elements.get("#error-message").hidden, true);
    assert.equal(elements.get("#window-state").classList.contains("error-state"), false);

    // Un error de la solicitud vigente elimina la curva anterior y deja error visible.
    select.value = "100";
    select.listeners.get("change")();
    pending[4].reject(new Error("Fixture perdido"));
    await flushAsync();
    assert.equal(elements.get("#window-state").dataset.viewState, "error");
    assert.equal(elements.get("#error-message").hidden, false);
    assert.match(elements.get("#error-message").textContent, /Fixture perdido/);
    assert.equal(elements.get("#plot-ch1").children.length, 0);
    assert.equal(elements.get("#sample-count").textContent, "—");

    // Un reintento válido limpia el error y presenta la nueva ventana.
    select.value = "1000";
    select.listeners.get("change")();
    pending[5].resolve({ ok: true, json: async () => fixture1000 });
    await flushAsync();
    assert.equal(elements.get("#window-state").dataset.viewState, "ready");
    assert.equal(elements.get("#error-message").hidden, true);
  } finally {
    globalThis.document = previousDocument;
    globalThis.fetch = previousFetch;
  }
});
