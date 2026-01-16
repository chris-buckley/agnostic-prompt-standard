#!/usr/bin/env node
import { main } from '../src/cli.js';

main(process.argv).catch((err) => {
  const msg = err?.message ?? String(err);
  console.error(`Error: ${msg}`);
  process.exit(1);
});
