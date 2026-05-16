#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");

const result = spawnSync("merlin", process.argv.slice(2), { stdio: "inherit" });

if (result.error) {
  if (result.error.code === "ENOENT") {
    console.error(
      "Error: merlin not found in PATH.\n" +
        "The Python package may not have installed correctly.\n" +
        "Try: pip install merlin-dbt"
    );
    process.exit(2);
  }
  throw result.error;
}

process.exit(result.status ?? 0);
