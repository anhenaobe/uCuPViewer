const API = location.protocol === "file:" ? "http://127.0.0.1:5000/api/v1" : "/api/v1";
const rateLabel = (rate) => rate >= 1000 ? `${rate / 1000} kSa/s por canal` : `${rate} Sa/s por canal`;
const canvas = document.getElementById("waveform");
const message = document.getElementById("message");
const statusText = document.getElementById("status");
let chart;
let timer;
let busy = false;

function draw(windowData) {
  const labels = windowData.channels.ch1.map((_, i) => (i / windowData.sample_rate_hz).toFixed(3));
  if (!window.Chart) throw new Error("Chart.js no está disponible; revisa la conexión a Internet.");
  if (!chart) {
    chart = new Chart(canvas, {
      type: "line",
      data: { labels, datasets: [
        { label: "CH1 · ADC", data: windowData.channels.ch1, borderColor: "#22d3ee", pointRadius: 0, borderWidth: 2 },
        { label: "CH2 · ADC", data: windowData.channels.ch2, borderColor: "#a78bfa", pointRadius: 0, borderWidth: 2 },
      ] },
      options: { color: "#cbd5e1", responsive: true, maintainAspectRatio: false, animation: false,
        interaction: { intersect: false, mode: "index" },
        scales: { x: { title: { display: true, text: "Tiempo (s)" }, ticks: { maxTicksLimit: 8 } },
          y: { min: 0, max: 4095, title: { display: true, text: "Cuenta ADC (12 bits)" } } } },
    });
  } else {
    chart.data.labels = labels;
    chart.data.datasets[0].data = windowData.channels.ch1;
    chart.data.datasets[1].data = windowData.channels.ch2;
    chart.update("none");
  }
  statusText.textContent = `Ventana ${windowData.window_id} · ${windowData.samples_per_channel} muestras/canal · ${windowData.source}`;
}

async function refresh() {
  if (busy) return;
  busy = true;
  try {
    const response = await fetch(`${API}/window/latest`, { cache: "no-store" });
    if (!response.ok) throw new Error(`API respondió HTTP ${response.status}`);
    draw(await response.json());
    message.textContent = "";
  } catch (error) {
    statusText.textContent = "Sin conexión al backend";
    message.textContent = `${error.message}. Confirma que el backend esté iniciado y que la API sea accesible.`;
  } finally { busy = false; }
}

function schedule() {
  clearInterval(timer);
  timer = setInterval(refresh, Number(document.getElementById("refresh").value));
  refresh();
}

document.querySelectorAll("#presets button").forEach((button) => button.addEventListener("click", async () => {
  const rate = Number(button.dataset.rate);
  try {
    const response = await fetch(`${API}/acquisition/preset`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sample_rate_hz: rate }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
    document.getElementById("rate-label").textContent = rateLabel(rate);
    document.querySelectorAll("#presets button").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    message.textContent = result.applied ? "Preset aplicado por hardware." : "Preset seleccionado para la simulación; no se aplicó al hardware.";
    await refresh();
  } catch (error) { message.textContent = error.message; }
}));

document.getElementById("refresh").addEventListener("change", schedule);
fetch(`${API}/status`).then((response) => response.json()).then((state) => {
  document.getElementById("source-badge").textContent = state.source === "simulated" ? "SIMULACIÓN" : "HARDWARE";
  schedule();
}).catch(() => schedule());
