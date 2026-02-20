import fs from 'node:fs/promises';

/**
 * Parsed constant value from adaptor.md.
 */
export type ConstantValue = string | number | boolean | unknown[] | Record<string, unknown>;

/**
 * Parsed format contract from adaptor.md.
 */
export interface FormatContract {
  id: string;
  name: string;
  purpose: string;
  body: string;
}

/**
 * Complete parsed adaptor.md data.
 */
export interface AdaptorData {
  instructions: string;
  constants: Record<string, ConstantValue>;
  formats: Record<string, FormatContract>;
}

const SECTION_RE = /<(instructions|constants|formats)>([\s\S]*?)<\/\1>/g;
const FORMAT_BLOCK_RE = /<format\b([^>]*)>([\s\S]*?)<\/format>/g;
const FORMAT_ATTR_RE = /\b(id|name|purpose)="([^"]*)"/g;
const NUMBER_RE = /^-?(?:\d+|\d*\.\d+)(?:[eE][+-]?\d+)?$/;

function splitLines(raw: string): string[] {
  return raw.split(/\r\n|\n|\r/);
}

function parseIdentifierArray(raw: string): string[] | null {
  const s = raw.trim();
  if (!s.startsWith('[') || !s.endsWith(']')) return null;

  const inner = s.slice(1, -1).trim();
  if (!inner) return [];

  const parts = inner
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean);

  const out: string[] = [];
  for (const part of parts) {
    const quoted =
      (part.startsWith('"') && part.endsWith('"')) ||
      (part.startsWith("'") && part.endsWith("'"));
    if (quoted) {
      out.push(part.slice(1, -1));
      continue;
    }

    if (!/^[A-Z][A-Z0-9_]*$/.test(part)) return null;
    out.push(part);
  }

  return out;
}

/**
 * Parse a CSV string into an array of objects keyed by header fields.
 */
function parseCsvBlock(csv: string): Record<string, string>[] {
  const lines = splitLines(csv.trim()).filter((l) => l.trim());
  if (lines.length < 1) return [];

  const headers = splitCsvRow(lines[0] ?? '');
  const rows: Record<string, string>[] = [];

  for (let i = 1; i < lines.length; i++) {
    const cells = splitCsvRow(lines[i] ?? '');
    const row: Record<string, string> = {};
    for (let j = 0; j < headers.length; j++) {
      row[headers[j] ?? ''] = cells[j] ?? '';
    }
    rows.push(row);
  }

  return rows;
}

/**
 * Split a CSV row respecting quoted fields.
 */
function splitCsvRow(line: string): string[] {
  const cells: string[] = [];
  let current = '';
  let inQuote = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuote) {
      if (ch === '"' && line[i + 1] === '"') {
        current += '"';
        i++;
      } else if (ch === '"') {
        inQuote = false;
      } else {
        current += ch;
      }
    } else {
      if (ch === '"') {
        inQuote = true;
      } else if (ch === ',') {
        cells.push(current);
        current = '';
      } else {
        current += ch;
      }
    }
  }

  cells.push(current);
  return cells;
}

/**
 * Parse the constants section of an adaptor.md file.
 */
function parseConstants(raw: string): Record<string, ConstantValue> {
  const constants: Record<string, ConstantValue> = {};
  const lines = splitLines(raw);
  let i = 0;

  while (i < lines.length) {
    const line = lines[i] ?? '';
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith('//') || trimmed.startsWith('#')) {
      i++;
      continue;
    }

    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) {
      i++;
      continue;
    }

    const key = trimmed.slice(0, colonIdx).trim();
    const rest = trimmed.slice(colonIdx + 1).trim();

    const blockMatch = rest.match(/^(JSON|TEXT|CSV|YAML)<<$/);
    if (blockMatch) {
      const blockType = blockMatch[1];
      const bodyLines: string[] = [];
      i++;
      while (i < lines.length) {
        const bLine = lines[i] ?? '';
        if (bLine.trim() === '>>') {
          i++;
          break;
        }
        bodyLines.push(bLine);
        i++;
      }

      const body = bodyLines.join('\n');

      if (blockType === 'JSON') {
        try {
          constants[key] = JSON.parse(body) as ConstantValue;
        } catch {
          constants[key] = body;
        }
      } else if (blockType === 'CSV') {
        constants[key] = parseCsvBlock(body);
      } else {
        constants[key] = body;
      }

      continue;
    }

    if (rest.startsWith('[')) {
      try {
        constants[key] = JSON.parse(rest) as ConstantValue;
      } catch {
        const parsed = parseIdentifierArray(rest);
        constants[key] = parsed ?? rest;
      }
      i++;
      continue;
    }

    if (
      (rest.startsWith('"') && rest.endsWith('"')) ||
      (rest.startsWith("'") && rest.endsWith("'"))
    ) {
      constants[key] = rest.slice(1, -1);
      i++;
      continue;
    }

    if (rest === 'true') {
      constants[key] = true;
      i++;
      continue;
    }
    if (rest === 'false') {
      constants[key] = false;
      i++;
      continue;
    }

    if (NUMBER_RE.test(rest)) {
      const num = Number(rest);
      if (!Number.isNaN(num)) {
        constants[key] = num;
        i++;
        continue;
      }
    }

    constants[key] = rest;
    i++;
  }

  return constants;
}

/**
 * Parse the formats section of an adaptor.md file.
 */
function parseFormats(raw: string): Record<string, FormatContract> {
  const formats: Record<string, FormatContract> = {};
  let match: RegExpExecArray | null;
  FORMAT_BLOCK_RE.lastIndex = 0;

  while ((match = FORMAT_BLOCK_RE.exec(raw)) !== null) {
    const attrsRaw = match[1] ?? '';
    const body = (match[2] ?? '').trim();

    const attrs: Record<string, string> = {};
    let a: RegExpExecArray | null;
    FORMAT_ATTR_RE.lastIndex = 0;
    while ((a = FORMAT_ATTR_RE.exec(attrsRaw)) !== null) {
      const k = a[1];
      if (!k) continue;
      attrs[k] = a[2] ?? '';
    }

    const id = attrs['id'];
    if (!id) continue;

    formats[id] = {
      id,
      name: attrs['name'] ?? '',
      purpose: attrs['purpose'] ?? '',
      body,
    };
  }

  return formats;
}

/**
 * Parse an adaptor.md file into structured data.
 */
export async function parseAdaptorMd(filePath: string): Promise<AdaptorData> {
  const raw = await fs.readFile(filePath, 'utf8');
  return parseAdaptorMdString(raw);
}

/**
 * Parse an adaptor.md string into structured data.
 */
export function parseAdaptorMdString(raw: string): AdaptorData {
  const data: AdaptorData = {
    instructions: '',
    constants: {},
    formats: {},
  };

  let match: RegExpExecArray | null;
  SECTION_RE.lastIndex = 0;

  while ((match = SECTION_RE.exec(raw)) !== null) {
    const section = match[1];
    const content = match[2] ?? '';

    switch (section) {
      case 'instructions':
        data.instructions = content.trim();
        break;
      case 'constants':
        data.constants = parseConstants(content);
        break;
      case 'formats':
        data.formats = parseFormats(content);
        break;
    }
  }

  return data;
}

/**
 * Extract a string constant or return a default.
 */
export function getString(
  constants: Record<string, ConstantValue>,
  key: string,
  fallback = ''
): string {
  const v = constants[key];
  return typeof v === 'string' ? v : fallback;
}

/**
 * Extract a string array constant or return empty array.
 */
export function getStringArray(constants: Record<string, ConstantValue>, key: string): string[] {
  const v = constants[key];
  if (Array.isArray(v)) {
    return v.filter((item): item is string => typeof item === 'string');
  }
  return [];
}