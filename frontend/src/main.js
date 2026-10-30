import { renderChannel } from "./plot.js";
import { validateWindow } from "./validate.js";

const presetSelect = document.querySelector("#sample-rate");
const stateLabel = document.querySelector("#window-state");
const errorMessage = document.querySelector("#error-message");
const plotCh1 = document.querySelector("#plot-ch1");
const plotCh2 = document.querySelector("#plot-ch2");
const sourceBadge = document.querySelector("#source-badge");
const sourceLabel = document.querySelector("#source-label");
const sourceDescription = document.querySelector("#source-description");

const formatInteger = (value) => value.toLocaleString("es-CO");
const formatDurationMs = (value) => `${value.toLocaleString("es-CO", { maximumFractionDigits: 3 })} ms`;

function displayWindow(windowData) {
  const rate = windowData.sample_rate_hz;
  const spanMs = windowData.samples_per_channel / rate * 1000;
  document.querySelector("#sample-count").textContent = windowData.samples_per_channel;
  document.querySelector("#sample-rate-value").textContent = `${formatInteger(rate)} Sa/s`;
  document.querySelector("#window-span").textContent = formatDurationMs(spanMs);
  document.querySelector("#adc-resolution").textContent = windowData.adc_resolution_bits;
  sourceBadge.dataset.source = windowData.source;
  sourceLabel.textContent = windowData.source === "simulated" ? "Simulación local" : "Hardware";
  sourceDescription.textContent = windowData.source === "simulated"
    ? "Datos de fixtures locales; no hay conexión con hardware real. No son evidencia experimental."
    : "Datos recibidos del hardware.";
  renderChannel(plotCh1, windowData.channels.ch1, rate, "canal 1", "#57c7ee");
  renderChannel(plotCh2, windowData.channels.ch2, rate, "canal 2", "#ffb765");
  stateLabel.textContent = `Ventana ${windowData.window_id} · ${windowData.samples_per_channel} muestras`;
  stateLabel.classList.remove("error-state");
  errorMessage.hidden = true;
  errorMessage.textContent = "";
}

let latestFixtureRequestId = 0;

async function loadFixture(sampleRateHz) {
  const requestId = ++latestFixtureRequestId;
  stateLabel.textContent = "Cargando fixture…";
  errorMessage.hidden = true;
  try {
    const fixtureUrl = new URL(`../fixtures/window-${sampleRateHz}.json`, import.meta.url);
    const response = await fetch(fixtureUrl);
    if (!response.ok) throw new Error(`No se pudo cargar el fixture (HTTP ${response.status}).`);
    const windowData = validateWindow(await response.json(), sampleRateHz);
    if (windowData.source !== "simulated") throw new Error("El selector local solo carga fixtures simulados.");
    if (requestId !== latestFixtureRequestId) return;
    displayWindow(windowData);
  } catch (error) {
    if (requestId !== latestFixtureRequestId) return;
    stateLabel.textContent = "Fixture no disponible";
    stateLabel.classList.add("error-state");
    errorMessage.textContent = error instanceof Error ? error.message : "Ocurrió un error desconocido al cargar la vista previa.";
    errorMessage.hidden = false;
  }
}

presetSelect.addEventListener("change", () => {
  const selectedRate = Number(presetSelect.value);
  void loadFixture(selectedRate);
});

void loadFixture(Number(presetSelect.value));
