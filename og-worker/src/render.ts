import type { OGParams } from "./types.js";
import { buildSVG } from "./svg-template.js";

export function renderSVG(params: OGParams): string {
  return buildSVG(params);
}
