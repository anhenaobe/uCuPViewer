import { LineAccumulator } from "./uart-lines.js";
import { validateWindow } from "./validate.js";
import { renderChannel } from "./plot.js";

// Velocidad indicada para la prueba local; no implica un enlace UART verificado.
const BAUD_RATE = 115200;
const connectButton = document.querySelector("#uart-connect");
const disconnectButton = document.querySelector("#uart-disconnect");
const stateLabel = document.querySelector("#uart-state");
const detailLabel = document.querySelector("#uart-detail");
const errorLabel = document.querySelector("#uart-error");
const bytesLabel = document.querySelector("#uart-bytes");
const framesLabel = document.querySelector("#uart-frames");
const sampleLabel = document.querySelector("#uart-samples");
const sourceLabel = document.querySelector("#uart-source");
const chartRegion = document.querySelector("#uart-charts");
const placeholder = document.querySelector("#uart-placeholder");

const accumulator = new LineAccumulator();
let port = null;
let reader = null;
let closing = false;
let receivedBytes = 0;
let validWindows = 0;

function showState(title, detail) {
  stateLabel.textContent = title;
  detailLabel.textContent = detail;
}

function showError(message) {
  errorLabel.textContent = message;
  errorLabel.hidden = false;
}

function clearError() {
  errorLabel.textContent = "";
  errorLabel.hidden = true;
}

function renderWindow(data) {
  renderChannel(document.querySelector("#uart-plot-ch1"), data.channels.ch1, data.sample_rate_hz, "CH1", "#57c7ee");
  renderChannel(document.querySelector("#uart-plot-ch2"), data.channels.ch2, data.sample_rate_hz, "CH2", "#ffb765");
  validWindows += 1;
  framesLabel.textContent = String(validWindows);
  sampleLabel.textContent = `Ventana ${data.window_id} · ${data.channels.ch1.length} muestras/canal · ${data.sample_rate_hz.toLocaleString("es-CO")} Sa/s`;
  sourceLabel.textContent = data.source === "simulated"
    ? "Origen declarado: SIMULATED. No son mediciones reales."
    : "Origen declarado: HARDWARE. Su procedencia no está verificada por esta prueba.";
  chartRegion.hidden = false;
  placeholder.hidden = true;
  showState("Ventana válida recibida", "Puerto abierto. Esta es una prueba UART local, no integración HTTP.");
}

function parseLine(line) {
  try {
    const payload = JSON.parse(line);
    if (!Number.isSafeInteger(payload?.window_id) || payload.window_id < 1) {
      throw new Error("window_id debe ser un entero positivo.");
    }
    const data = validateWindow(payload);
    renderWindow(data);
    clearError();
  } catch (error) {
    showError(`Se recibieron bytes, pero no una ventana JSON válida: ${error instanceof Error ? error.message : "error de formato"}`);
    showState("Trama no reconocida", "El formato de línea JSON es experimental; no se ha acordado con Pipe.");
  }
}

async function readPort(openPort) {
  const decoder = new TextDecoder();
  try {
    while (openPort.readable && !closing) {
      const activeReader = openPort.readable.getReader();
      reader = activeReader;
      try {
        while (!closing) {
          const { value, done } = await activeReader.read();
          if (done) break;
          if (!value?.length) continue;
          receivedBytes += value.length;
          bytesLabel.textContent = String(receivedBytes);
          const lines = accumulator.push(decoder.decode(value, { stream: true }));
          if (validWindows === 0) showState("Bytes recibidos", "Esperando una ventana válida; no se generarán muestras artificiales.");
          for (const line of lines) parseLine(line);
        }
      } finally {
        activeReader.releaseLock();
        reader = null;
      }
      if (!closing) break; // La reconexión se hará explícitamente; nunca ocultar una desconexión.
    }
  } catch (error) {
    if (!closing) showError(`Error de lectura UART: ${error instanceof Error ? error.message : String(error)}`);
  } finally {
    closing = true;
    try { await openPort.close(); } catch { /* puede estar desconectado físicamente */ }
    if (port === openPort) port = null;
    reader = null;
    accumulator.reset();
    connectButton.disabled = !("serial" in navigator);
    disconnectButton.disabled = true;
    showState("Puerto cerrado", "No se ha verificado ningún flujo de datos activo.");
  }
}

async function connect() {
  if (port || !("serial" in navigator)) return;
  clearError();
  connectButton.disabled = true;
  showState("Seleccionando puerto…", "El navegador solicitará permiso para acceder a un puerto serial local.");
  let selectedPort;
  try {
    // Debe invocarse a partir del clic del usuario (permiso explícito de Web Serial).
    selectedPort = await navigator.serial.requestPort();
    await selectedPort.open({ baudRate: BAUD_RATE, dataBits: 8, stopBits: 1, parity: "none" });
    port = selectedPort;
    closing = false;
    receivedBytes = 0;
    validWindows = 0;
    bytesLabel.textContent = "0";
    framesLabel.textContent = "0";
    chartRegion.hidden = true;
    placeholder.hidden = false;
    placeholder.textContent = "Puerto abierto; todavía no se ha recibido ninguna ventana válida.";
    showState("Puerto abierto · esperando datos", "Se abrió un puerto serial local, no se ha comprobado el emisor Raspberry Pi.");
    disconnectButton.disabled = false;
    void readPort(selectedPort);
  } catch (error) {
    if (selectedPort) {
      try { await selectedPort.close(); } catch { /* no se abrió */ }
    }
    connectButton.disabled = false;
    showState("Sin puerto abierto", "Hipótesis: Raspberry Pi preparada, sin conexión física verificada.");
    if (error?.name !== "NotFoundError") {
      showError(`No se abrió el puerto: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}

async function disconnect() {
  if (!port) return;
  closing = true;
  disconnectButton.disabled = true;
  if (reader) {
    try { await reader.cancel(); } catch { /* el puerto pudo desconectarse */ }
  }
}

if (!("serial" in navigator)) {
  connectButton.disabled = true;
  showState("Web Serial no disponible", "Utiliza un navegador compatible en localhost o HTTPS. No implica un fallo de la Raspberry Pi.");
} else {
  showState("UART configurado como hipótesis", "115200 baudios, 8N1. Sin enlace ni datos verificados.");
}

connectButton.addEventListener("click", () => { void connect(); });
disconnectButton.addEventListener("click", () => { void disconnect(); });
