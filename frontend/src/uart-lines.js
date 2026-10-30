// Receptor incremental de líneas para una prueba UART local (NO es un contrato de equipo).
export class LineAccumulator {
  constructor(maxLineLength = 32768) {
    if (!Number.isSafeInteger(maxLineLength) || maxLineLength < 1) {
      throw new RangeError("La longitud máxima debe ser un entero positivo.");
    }
    this.maxLineLength = maxLineLength;
    this.pending = "";
  }

  push(chunk) {
    if (typeof chunk !== "string") throw new TypeError("Se esperaba texto decodificado.");
    const parts = (this.pending + chunk).split("\n");
    const pending = parts.pop();
    if (parts.some((line) => line.length > this.maxLineLength) || pending.length > this.maxLineLength) {
      this.pending = "";
      throw new Error("Línea UART demasiado larga; se descartó por seguridad.");
    }
    this.pending = pending;
    return parts.map((line) => line.replace(/\r$/, "")).filter((line) => line.trim().length > 0);
  }

  reset() {
    this.pending = "";
  }
}
