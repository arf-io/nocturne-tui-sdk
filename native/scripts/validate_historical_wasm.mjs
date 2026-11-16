#!/usr/bin/env node
/* Validate content-addressed historical modules with the actual Node WebAssembly API. */
import fs from 'node:fs';
import crypto from 'node:crypto';
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = [];
for (const item of input.modules ?? []) {
  try {
    const bytes = fs.readFileSync(item.path);
    const actualSha256 = crypto.createHash('sha256').update(bytes).digest('hex');
    const module = new WebAssembly.Module(bytes);
    const hashMatches = typeof item.sha256 === 'string' && item.sha256.toLowerCase() === actualSha256;
    results.push({
      sha256: item.sha256,
      actualSha256,
      sizeBytes: bytes.length,
      valid: hashMatches,
      validator: 'Node WebAssembly.Module',
      imports: WebAssembly.Module.imports(module).map(x => ({module:x.module,name:x.name,kind:x.kind})),
      exports: WebAssembly.Module.exports(module).map(x => ({name:x.name,kind:x.kind})),
      ...(hashMatches ? {} : {errorCode:'sha256-mismatch', error:`expected ${item.sha256}; read ${actualSha256}`}),
    });
  } catch (error) {
    let actualSha256 = null;
    try { actualSha256 = crypto.createHash('sha256').update(fs.readFileSync(item.path)).digest('hex'); } catch {}
    results.push({
      sha256: item.sha256,
      actualSha256,
      sizeBytes: fs.existsSync(item.path) ? fs.statSync(item.path).size : null,
      valid: false,
      validator: 'Node WebAssembly.Module',
      errorCode: 'invalid-wasm-module',
      error: `${error.name}: ${error.message}`,
      imports: [], exports: [],
    });
  }
}
process.stdout.write(JSON.stringify({nodeVersion:process.version,results}));
