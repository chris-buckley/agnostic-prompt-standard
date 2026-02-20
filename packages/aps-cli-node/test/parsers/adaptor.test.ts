import test from 'node:test';
import assert from 'node:assert/strict';

import { parseAdaptorMdString, getString, getStringArray } from '../../dist/parsers/adaptor.js';

const SAMPLE_ADAPTOR = `
<instructions>
Generate artifacts for Test Platform.
Tool names are PascalCase.
</instructions>

<constants>
PLATFORM_ID: "test-platform"
DISPLAY_NAME: "Test Platform"
ADAPTER_VERSION: "2.0.0"
LAST_UPDATED: "2026-02-19"
ENABLED: true
MAX_RETRIES: 3
SCIENTIFIC: 1e3
CONST_REFS: [PLATFORM_ID, DISPLAY_NAME]

INSTRUCTION_FILE_PATHS: ["./README.md", "./docs/*.md"]
DETECTION_MARKERS: [".test", "test.json"]

DESCRIPTION: TEXT<<
This is a multi-line
text block constant.
>>

CONFIG: JSON<<
{
  "key": "value",
  "nested": { "a": 1 }
}
>>

TOOLS: CSV<<
name,risk,description
Read,low,"Read files"
Write,medium,"Write files"
>>
</constants>

<formats>
<format id="TEST_FORMAT_V1" name="Test Format" purpose="A test format contract.">
## Title: <TITLE>

Content here.

WHERE:
- <TITLE> is String; the title.
</format>

<format name="Alt Format" purpose="Attr order test." id="ALT_FORMAT_V1">
Alt content.
</format>
</formats>
`;

test('parseAdaptorMdString extracts instructions', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.ok(data.instructions.includes('Generate artifacts for Test Platform'));
  assert.ok(data.instructions.includes('PascalCase'));
});

test('parseAdaptorMdString parses string constants', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.equal(data.constants['PLATFORM_ID'], 'test-platform');
  assert.equal(data.constants['DISPLAY_NAME'], 'Test Platform');
  assert.equal(data.constants['ADAPTER_VERSION'], '2.0.0');
});

test('parseAdaptorMdString parses boolean constants', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.equal(data.constants['ENABLED'], true);
});

test('parseAdaptorMdString parses number constants', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.equal(data.constants['MAX_RETRIES'], 3);
});

test('parseAdaptorMdString parses scientific numbers', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.equal(data.constants['SCIENTIFIC'], 1000);
});

test('parseAdaptorMdString parses inline arrays', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.deepEqual(data.constants['INSTRUCTION_FILE_PATHS'], ['./README.md', './docs/*.md']);
  assert.deepEqual(data.constants['DETECTION_MARKERS'], ['.test', 'test.json']);
});

test('parseAdaptorMdString parses identifier arrays', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.deepEqual(data.constants['CONST_REFS'], ['PLATFORM_ID', 'DISPLAY_NAME']);
});

test('parseAdaptorMdString parses TEXT blocks', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  const desc = data.constants['DESCRIPTION'] as string;
  assert.ok(desc.includes('multi-line'));
  assert.ok(desc.includes('text block constant'));
});

test('parseAdaptorMdString parses JSON blocks', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  const config = data.constants['CONFIG'] as Record<string, unknown>;
  assert.equal(config['key'], 'value');
  assert.deepEqual(config['nested'], { a: 1 });
});

test('parseAdaptorMdString parses CSV blocks', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  const tools = data.constants['TOOLS'] as Record<string, string>[];
  assert.equal(tools.length, 2);
  assert.equal(tools[0]?.['name'], 'Read');
  assert.equal(tools[0]?.['risk'], 'low');
  assert.equal(tools[1]?.['name'], 'Write');
});

test('parseAdaptorMdString handles CRLF in CSV blocks', () => {
  const data = parseAdaptorMdString(
    '<constants>\r\nTOOLS: CSV<<\r\nname,risk\r\nRead,low\r\n>>\r\n</constants>'
  );
  const tools = data.constants['TOOLS'] as Record<string, string>[];
  assert.equal(tools[0]?.['name'], 'Read');
  assert.equal(tools[0]?.['risk'], 'low');
});

test('parseAdaptorMdString parses formats', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.ok(data.formats['TEST_FORMAT_V1']);
  assert.equal(data.formats['TEST_FORMAT_V1']?.name, 'Test Format');
  assert.equal(data.formats['TEST_FORMAT_V1']?.purpose, 'A test format contract.');
  assert.ok(data.formats['TEST_FORMAT_V1']?.body.includes('WHERE:'));
});

test('parseAdaptorMdString parses format attributes in any order', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.ok(data.formats['ALT_FORMAT_V1']);
  assert.equal(data.formats['ALT_FORMAT_V1']?.name, 'Alt Format');
  assert.equal(data.formats['ALT_FORMAT_V1']?.purpose, 'Attr order test.');
  assert.ok(data.formats['ALT_FORMAT_V1']?.body.includes('Alt content.'));
});

test('getString returns constant string value', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  assert.equal(getString(data.constants, 'PLATFORM_ID'), 'test-platform');
  assert.equal(getString(data.constants, 'MISSING', 'default'), 'default');
});

test('getStringArray returns array constant', () => {
  const data = parseAdaptorMdString(SAMPLE_ADAPTOR);
  const paths = getStringArray(data.constants, 'DETECTION_MARKERS');
  assert.deepEqual(paths, ['.test', 'test.json']);
  assert.deepEqual(getStringArray(data.constants, 'MISSING'), []);
});

test('parseAdaptorMdString handles empty input', () => {
  const data = parseAdaptorMdString('');
  assert.equal(data.instructions, '');
  assert.deepEqual(data.constants, {});
  assert.deepEqual(data.formats, {});
});