#!/usr/bin/env node
// Project-local Hallmark override. No agent settings are read or changed.
console.error('Hallmark hooks are disabled in this project.');
process.exitCode = 2;
