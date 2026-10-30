import test from "node:test";
import assert from "node:assert/strict";
import { renderViewState, VIEW_STATES } from "../../../frontend/src/ui-state.js";

function createElements() {
  const classes = new Set();
  return {
    stateLabel: {
      textContent: "", dataset: {},
      classList: {
        add: (value) => classes.add(value),
        remove: (value) => classes.delete(value),
        contains: (value) => classes.has(value),
      },
    },
    infoMessage: { textContent: "", hidden: false },
    errorMessage: { textContent: "", hidden: false },
  };
}

test("reconoce los cinco estados visuales sin usar HTTP", () => {
  assert.deepEqual(VIEW_STATES, ["loading", "ready", "empty", "stale", "error"]);
});

test("carga y disponibilidad limpian mensajes anteriores", () => {
  const el = createElements();
  renderViewState(el, "error", { message: "Error de fixture" });
  assert.equal(el.errorMessage.textContent, "Error de fixture");
  assert.equal(el.stateLabel.classList.contains("error-state"), true);

  renderViewState(el, "loading");
  assert.equal(el.stateLabel.dataset.viewState, "loading");
  assert.equal(el.errorMessage.hidden, true);
  assert.equal(el.errorMessage.textContent, "");
  assert.equal(el.stateLabel.classList.contains("error-state"), false);

  renderViewState(el, "ready", { windowLabel: "Ventana 7 · 128 muestras" });
  assert.equal(el.stateLabel.textContent, "Ventana 7 · 128 muestras");
  assert.equal(el.infoMessage.hidden, true);
});

test("ventana ausente es información, no error", () => {
  const el = createElements();
  renderViewState(el, "empty");
  assert.equal(el.stateLabel.dataset.viewState, "empty");
  assert.equal(el.infoMessage.hidden, false);
  assert.match(el.infoMessage.textContent, /Todavía no hay muestras/);
  assert.equal(el.errorMessage.hidden, true);
});

test("ventana antigua advierte que no son datos en vivo", () => {
  const el = createElements();
  renderViewState(el, "stale", { windowLabel: "Ventana 3 · 64 muestras" });
  assert.equal(el.stateLabel.textContent, "Ventana 3 · 64 muestras · Antigua");
  assert.match(el.infoMessage.textContent, /no debe interpretarse como una captura en vivo/);
  assert.equal(el.errorMessage.hidden, true);
});

test("error distingue advertencia de fallo y permite reintentar", () => {
  const el = createElements();
  renderViewState(el, "stale");
  renderViewState(el, "error", { message: "Fixture no disponible" });
  assert.equal(el.infoMessage.hidden, true);
  assert.equal(el.infoMessage.textContent, "");
  assert.equal(el.errorMessage.hidden, false);
  assert.equal(el.errorMessage.textContent, "Fixture no disponible");
  renderViewState(el, "ready");
  assert.equal(el.errorMessage.hidden, true);
  assert.equal(el.stateLabel.classList.contains("error-state"), false);
});

test("rechaza estados desconocidos sin mutar la interfaz", () => {
  const el = createElements();
  assert.throws(() => renderViewState(el, "configuring"), /Estado visual desconocido/);
  assert.equal(el.stateLabel.textContent, "");
});
