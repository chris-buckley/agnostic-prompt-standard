import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..', '..', '..');
const skillRoot = path.join(repoRoot, 'skill', 'agnostic-prompt-standard');
const platformsDir = path.join(skillRoot, 'platforms');
const schemaPath = path.join(platformsDir, '_schemas', 'platform-manifest.schema.json');

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

test('platform-manifest.schema.json requires fileConventions', () => {
  const schema = readJson(schemaPath);
  assert.ok(Array.isArray(schema.required), 'schema.required must be an array');
  assert.ok(
    schema.required.includes('fileConventions'),
    'schema.required must include "fileConventions"'
  );
});

test('every platform manifest includes fileConventions with instructions', () => {
  const dirs = fs
    .readdirSync(platformsDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && d.name !== '_schemas')
    .map((d) => d.name);

  for (const dirName of dirs) {
    const manifestPath = path.join(platformsDir, dirName, 'manifest.json');
    assert.ok(fs.existsSync(manifestPath), `Missing manifest.json in ${dirName}`);

    const manifest = readJson(manifestPath);
    assert.ok(
      manifest.fileConventions && typeof manifest.fileConventions === 'object',
      `Platform "${dirName}" must define fileConventions object`
    );
    assert.ok(
      Array.isArray(manifest.fileConventions.instructions) &&
        manifest.fileConventions.instructions.length > 0,
      `Platform "${dirName}" must define fileConventions.instructions array`
    );
  }
});

test('schema enforces minItems >= 1 on fileConventions.instructions', () => {
  const schema = readJson(schemaPath);
  const ins = schema?.properties?.fileConventions?.properties?.instructions;
  assert.ok(ins, 'Schema must define fileConventions.instructions');
  assert.ok(
    typeof ins.minItems === 'number' && ins.minItems >= 1,
    'Schema must enforce minItems >= 1 on instructions'
  );
});
