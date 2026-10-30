export function validateWindow(windowData, expectedRate = null) {
  if (!windowData || typeof windowData !== "object") throw new Error("La ventana debe ser un objeto JSON.");
  if (windowData.source !== "simulated" && windowData.source !== "hardware") {
    throw new Error("El origen debe ser simulated o hardware.");
  }
  if (!Number.isFinite(windowData.sample_rate_hz) || windowData.sample_rate_hz <= 0) {
    throw new Error("La frecuencia de muestreo debe ser un número positivo.");
  }
  if (expectedRate !== null && windowData.sample_rate_hz !== expectedRate) {
    throw new Error("La frecuencia del fixture no coincide con el preset de vista previa.");
  }
  if (windowData.unit !== "adc_counts") throw new Error("La unidad recibida no es adc_counts.");
  if (windowData.adc_resolution_bits !== 12) {
    throw new Error("La vista previa requiere muestras ADC de 12 bits.");
  }

  const { samples_per_channel: count, channels } = windowData;
  if (!Number.isInteger(count) || count < 64) throw new Error("La ventana debe declarar al menos 64 muestras por canal.");
  if (!channels || !Array.isArray(channels.ch1) || !Array.isArray(channels.ch2)) {
    throw new Error("La ventana debe incluir los arreglos channels.ch1 y channels.ch2.");
  }
  if (channels.ch1.length !== count || channels.ch2.length !== count) {
    throw new Error("La cantidad de valores no coincide con samples_per_channel.");
  }
  for (const channel of [channels.ch1, channels.ch2]) {
    if (channel.some((sample) => !Number.isInteger(sample) || sample < 0 || sample > 4095)) {
      throw new Error("Cada muestra debe ser un entero entre 0 y 4095.");
    }
  }
  return windowData;
}
