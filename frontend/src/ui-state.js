// Estados de presentación. No representan estados de conexión ni operaciones del backend.
export const VIEW_STATES = Object.freeze(["loading", "ready", "empty", "stale", "error"]);

const DEFAULT_LABELS = {
  loading: "Cargando datos de prueba…",
  ready: "Ventana disponible",
  empty: "Sin ventana disponible",
  stale: "Ventana antigua",
  error: "Error al cargar datos",
};

const DEFAULT_MESSAGES = {
  empty: "Todavía no hay muestras disponibles para mostrar.",
  stale: "Esta ventana es antigua y no debe interpretarse como una captura en vivo.",
  error: "No se pudieron obtener los datos de prueba.",
};

// elements son nodos ya obtenidos por el llamador: la lógica no depende de la API HTTP.
export function renderViewState(elements, state, { windowLabel = "", message = "" } = {}) {
  if (!VIEW_STATES.includes(state)) throw new Error(`Estado visual desconocido: ${state}`);

  const { stateLabel, infoMessage, errorMessage } = elements;
  stateLabel.dataset.viewState = state;
  stateLabel.textContent = windowLabel && (state === "ready" || state === "stale")
    ? `${windowLabel}${state === "stale" ? " · Antigua" : ""}`
    : DEFAULT_LABELS[state];
  stateLabel.classList.remove("error-state");
  if (state === "error") stateLabel.classList.add("error-state");

  const isInfo = state === "empty" || state === "stale";
  infoMessage.hidden = !isInfo;
  infoMessage.textContent = isInfo ? (message || DEFAULT_MESSAGES[state]) : "";

  errorMessage.hidden = state !== "error";
  errorMessage.textContent = state === "error" ? (message || DEFAULT_MESSAGES.error) : "";
}
