import { rmSync } from "node:fs";
import { resolve } from "node:path";

for (const name of ["core", "react", "forms", "next"]) {
  rmSync(resolve("packages", name, "dist"), { recursive: true, force: true });
  rmSync(resolve("packages", name, "tsconfig.tsbuildinfo"), { force: true });
}
