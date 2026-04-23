<<<<<<< HEAD
#!/usr/bin/env node

/**
 * Post-build verification script: checks that AcpConnection's public methods
 * exist in the compiled output. This catches JSDoc comment bugs where a missing
 * comment closure causes methods to be swallowed.
 *
 * Usage: node scripts/check-acp-api-surface.mjs [path-to-compiled-main]
 *
 * Default path: src/out/main/index.js (relative to project root)
 */

import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = resolve(__dirname, '..');

// Expected public methods on AcpConnection class
const REQUIRED_METHODS = [
  'connect',
  'newSession',
  'sendPrompt',
  'cancelPrompt',
  'disconnect',
  'authenticate',
  'loadSession',
  'setSessionMode',
  'setModel',
  'setConfigOption',
  'getConfigOptions',
  'getModels',
  'setPromptTimeout',
  'getInitializeResponse',
];

// Search patterns for each method in the compiled output
// Methods can appear as: async methodName( or methodName(
function buildMethodPattern(methodName) {
  // Escape special chars in method name
  const escaped = methodName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(?:async\\s+)?${escaped}\\s*\\(`, 'm');
}

function main() {
  const compiledPath = process.argv[2] || resolve(projectRoot, 'src', 'out', 'main', 'index.js');
  // electron-vite outputs to src/out/main/ by default

  let compiledCode;
  try {
    compiledCode = readFileSync(compiledPath, 'utf-8');
  } catch {
    console.error(`ERROR: Cannot read compiled output at: ${compiledPath}`);
    console.error('Make sure to run the build first.');
    process.exit(1);
  }

  console.log(`Checking AcpConnection API surface in: ${compiledPath}`);
  console.log(`File size: ${(compiledCode.length / 1024).toFixed(0)} KB\n`);

  let failed = false;

  for (const method of REQUIRED_METHODS) {
    const pattern = buildMethodPattern(method);
    if (pattern.test(compiledCode)) {
      console.log(`  OK: ${method}`);
    } else {
      console.error(`  MISSING: ${method}`);
      failed = true;
    }
  }

  // Also check for the class name itself
  if (/class\s+AcpConnection\b/.test(compiledCode)) {
    console.log('  OK: AcpConnection class definition');
  } else if (/AcpConnection/.test(compiledCode)) {
    console.log('  OK: AcpConnection reference found (may be minified)');
  } else {
    console.error('  MISSING: AcpConnection class not found in compiled output');
    failed = true;
  }

  console.log('');
  if (failed) {
    console.error('FAIL: Some methods are missing from the compiled output!');
    console.error('This likely indicates a JSDoc comment bug (missing closure).');
    process.exit(1);
  } else {
    console.log('PASS: All required AcpConnection methods found in compiled output.');
  }
}

main();
=======
#!/usr/bin/env node

/**
 * Post-build verification script: checks that AcpConnection's public methods
 * exist in the compiled output. This catches JSDoc comment bugs where a missing
 * comment closure causes methods to be swallowed.
 *
 * Usage: node scripts/check-acp-api-surface.mjs [path-to-compiled-main]
 *
 * Default path: src/out/main/index.js (relative to project root)
 */

import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = resolve(__dirname, '..');

// Expected public methods on AcpConnection class
const REQUIRED_METHODS = [
  'connect',
  'newSession',
  'sendPrompt',
  'cancelPrompt',
  'disconnect',
  'authenticate',
  'loadSession',
  'setSessionMode',
  'setModel',
  'setConfigOption',
  'getConfigOptions',
  'getModels',
  'setPromptTimeout',
  'getInitializeResponse',
];

// Search patterns for each method in the compiled output
// Methods can appear as: async methodName( or methodName(
function buildMethodPattern(methodName) {
  // Escape special chars in method name
  const escaped = methodName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(?:async\\s+)?${escaped}\\s*\\(`, 'm');
}

function main() {
  const compiledPath = process.argv[2] || resolve(projectRoot, 'src', 'out', 'main', 'index.js');
  // electron-vite outputs to src/out/main/ by default

  let compiledCode;
  try {
    compiledCode = readFileSync(compiledPath, 'utf-8');
  } catch {
    console.error(`ERROR: Cannot read compiled output at: ${compiledPath}`);
    console.error('Make sure to run the build first.');
    process.exit(1);
  }

  console.log(`Checking AcpConnection API surface in: ${compiledPath}`);
  console.log(`File size: ${(compiledCode.length / 1024).toFixed(0)} KB\n`);

  let failed = false;

  for (const method of REQUIRED_METHODS) {
    const pattern = buildMethodPattern(method);
    if (pattern.test(compiledCode)) {
      console.log(`  OK: ${method}`);
    } else {
      console.error(`  MISSING: ${method}`);
      failed = true;
    }
  }

  // Also check for the class name itself
  if (/class\s+AcpConnection\b/.test(compiledCode)) {
    console.log('  OK: AcpConnection class definition');
  } else if (/AcpConnection/.test(compiledCode)) {
    console.log('  OK: AcpConnection reference found (may be minified)');
  } else {
    console.error('  MISSING: AcpConnection class not found in compiled output');
    failed = true;
  }

  console.log('');
  if (failed) {
    console.error('FAIL: Some methods are missing from the compiled output!');
    console.error('This likely indicates a JSDoc comment bug (missing closure).');
    process.exit(1);
  } else {
    console.log('PASS: All required AcpConnection methods found in compiled output.');
  }
}

main();
>>>>>>> 1183b41 (chore: sync current project snapshot)
