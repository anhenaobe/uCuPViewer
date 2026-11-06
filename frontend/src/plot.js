const SVG_NS = "http://www.w3.org/2000/svg";
const WIDTH = 780;
const HEIGHT = 290;
const MARGIN = { top: 18, right: 22, bottom: 51, left: 66 };
const ADC_MAX = 2 ** 12 - 1;

function svgElement(name, attributes = {}, label = null) {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  if (label !== null) element.textContent = label;
  return element;
}

export function formatTimeMilliseconds(value, sampleRateHz) {
  const millisecondsPerSample = 1000 / sampleRateHz;
  const precision = Math.min(6, Math.max(0, Math.ceil(-Math.log10(millisecondsPerSample)) + 1));
  return new Intl.NumberFormat("es-CO", {
    useGrouping: false,
    maximumFractionDigits: precision,
  }).format(value);
}

export function sampleTimeSeconds(index, sampleRateHz) {
  return index / sampleRateHz;
}

export function renderChannel(svg, samples, sampleRateHz, channelName, color) {
  svg.replaceChildren();
  svg.setAttribute("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  svg.setAttribute("aria-label", `Muestras de ${channelName}, cuentas ADC contra tiempo en milisegundos`);

  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const bottom = MARGIN.top + plotHeight;
  const right = MARGIN.left + plotWidth;
  const lastSampleIndex = samples.length - 1;

  const yForValue = (value) => MARGIN.top + plotHeight * (1 - value / ADC_MAX);
  const xForIndex = (index) => MARGIN.left + plotWidth * index / lastSampleIndex;

  for (const tick of [0, 1024, 2048, 3072, ADC_MAX]) {
    const y = yForValue(tick);
    svg.append(svgElement("line", { x1: MARGIN.left, y1: y, x2: right, y2: y, class: "plot-gridline" }));
    svg.append(svgElement("text", { x: MARGIN.left - 10, y: y + 4, "text-anchor": "end", class: "plot-tick" }, tick));
  }

  svg.append(svgElement("line", { x1: MARGIN.left, y1: MARGIN.top, x2: MARGIN.left, y2: bottom, class: "plot-axis" }));
  svg.append(svgElement("line", { x1: MARGIN.left, y1: bottom, x2: right, y2: bottom, class: "plot-axis" }));

  const xTickIndices = [...new Set([0, Math.round(lastSampleIndex / 3), Math.round(2 * lastSampleIndex / 3), lastSampleIndex])];
  for (const index of xTickIndices) {
    const x = xForIndex(index);
    const timeMs = sampleTimeSeconds(index, sampleRateHz) * 1000;
    svg.append(svgElement("line", { x1: x, y1: bottom, x2: x, y2: bottom + 4, class: "plot-axis" }));
    const anchor = index === 0 ? "start" : index === lastSampleIndex ? "end" : "middle";
    svg.append(svgElement("text", { x, y: bottom + 19, "text-anchor": anchor, class: "plot-tick" }, formatTimeMilliseconds(timeMs, sampleRateHz)));
  }

  const points = samples.map((sample, index) => `${xForIndex(index)},${yForValue(sample)}`).join(" ");
  svg.append(svgElement("polyline", { points, stroke: color, class: "plot-line" }));
  const pointGroup = svgElement("g", { "aria-hidden": "true" });
  samples.forEach((sample, index) => {
    pointGroup.append(svgElement("circle", { cx: xForIndex(index), cy: yForValue(sample), r: 2.35, fill: color, class: "plot-point" }));
  });
  svg.append(pointGroup);

  svg.append(svgElement("text", {
    x: 16,
    y: MARGIN.top + plotHeight / 2,
    transform: `rotate(-90 15 ${MARGIN.top + plotHeight / 2})`,
    "text-anchor": "middle",
    class: "plot-axis-label",
  }, "Cuentas ADC"));
  svg.append(svgElement("text", {
    x: MARGIN.left + plotWidth / 2,
    y: HEIGHT - 4,
    "text-anchor": "middle",
    class: "plot-axis-label",
  }, "Tiempo (ms)"));
}
