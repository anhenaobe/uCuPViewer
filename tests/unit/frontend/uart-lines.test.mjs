import test from "node:test";
import assert from "node:assert/strict";
import { LineAccumulator } from "../../../frontend/src/uart-lines.js";

test("reconstruye líneas fragmentadas de UART sin crear muestras", () => {
  const parser = new LineAccumulator();
  assert.deepEqual(parser.push('{"window_id":'), []);
  assert.deepEqual(parser.push('1}\n'), ['{"window_id":1}']);
  assert.equal(parser.pending, "");
});

test("tolera CRLF, líneas vacías y varias tramas en un bloque", () => {
  const parser = new LineAccumulator();
  assert.deepEqual(parser.push('\r\n {"x":1}\r\n{"x":2}\n'), [' {"x":1}', '{"x":2}']);
});

test("rechaza líneas demasiado largas y recupera el búfer", () => {
  const parser = new LineAccumulator(5);
  assert.throws(() => parser.push("demasiado-largo"), /demasiado larga/);
  assert.deepEqual(parser.push("OK\n"), ["OK"]);
});

test("descarta datos incompletos al reiniciar la conexión", () => {
  const parser = new LineAccumulator();
  parser.push("incompleto");
  parser.reset();
  assert.deepEqual(parser.push("otro\n"), ["otro"]);
});
