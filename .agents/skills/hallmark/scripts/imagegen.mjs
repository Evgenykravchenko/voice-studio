#!/usr/bin/env node
// Project-local Hallmark override. No environment reads or network requests.
console.error('Together AI image generation is disabled in this project.');
process.exitCode = 2;
