#!/usr/bin/env node
"use strict";

const { execSync } = require("child_process");

function try_install(cmd) {
  try {
    execSync(cmd, { stdio: "inherit" });
    return true;
  } catch {
    return false;
  }
}

const managers = [
  "uv tool install merlin-dbt",
  "pipx install merlin-dbt",
  "pip install merlin-dbt",
  "pip3 install merlin-dbt",
];

const installed = managers.some(try_install);

if (!installed) {
  console.warn(
    "\nWarning: Could not install the merlin Python package automatically."
  );
  console.warn(
    "Run one of the following manually:\n" +
      "  uv tool install merlin-dbt\n" +
      "  pip install merlin-dbt\n"
  );
}
