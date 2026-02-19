import fs from 'node:fs/promises';

/**
 * Parsed constant value: string, number, boolean, array, or parsed block.
 */
export type ConstantValue = string | number | boolean | string[] | Record<string, unknown> | Record<string, unknown>[];

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
const FORMAT_TAG_RE = /<format\s+id="([^"]+)"(?:\s+name="([^"]*)")?(?:\s+purpose="([^"]*)")?\s*>([\s\S]*?)<\/format>/g;

/**
 * Parse a CSV string into an array of objects keyed by header fields.
 * @param csv - Raw CSV text.
 * @returns Array of row objects.
 */
function parseCsvBlock(csv: string): Record<string, string>[] {
  const lines = csv.trim().split('\n').filter((l) => l.trim());
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
 * @param raw - Raw text inside <constants> tags.
 * @returns Map of constant names to parsed values.
 */
function parseConstants(raw: string): Record<string, ConstantValue> {
  const constants: Record<string, ConstantValue> = {};
  const lines = raw.split('\n');
  let i = 0;

  while (i < lines.length) {
    const line = lines[i] ?? '';
    const trimmed = line.trim();

    // Skip blanks and comments
    if (!trimmed || trimmed.startsWith('//') || trimmed.startsWith('#')) {
      i++;
      continue;
    }

    // Match KEY: VALUE or KEY: BLOCK
    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) {
      i++;
      continue;
    }

    const key = trimmed.slice(0, colonIdx).trim();
    const rest = trimmed.slice(colonIdx + 1).trim();

    // Check for block constants: JSON<<, TEXT<<, CSV<<, YAML
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
        // TEXT or YAML: store as string
        constants[key] = body;
      }
      continue;
    }

    // Inline array: [...]
    if (rest.startsWith('[')) {
      try {
        constants[key] = JSON.parse(rest) as ConstantValue;
      } catch {
        // May contain unquoted constant refs; store as string
        constants[key] = rest;
      }
      i++;
      continue;
    }

    // Quoted string
    if ((rest.startsWith('"') && rest.endsWith('"')) || (rest.startsWith("'") && rest.endsWith("'"))) {
      constants[key] = rest.slice(1, -1);
      i++;
      continue;
    }

    // Boolean / number
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
    const num = Number(rest);
    if (!isNaN(num) && rest !== '') {
      constants[key] = num;
      i++;
      continue;
    }

    // Fallback: bare string
    constants[key] = rest;
    i++;
  }

  return constants;
}

/**
 * Parse the formats section of an adaptor.md file.
 * @param raw - Raw text inside <formats> tags.
 * @returns Map of format IDs to FormatContract.
 */
function parseFormats(raw: string): Record<string, FormatContract> {
  const formats: Record<string, FormatContract> = {};
  let match: RegExpExecArray | null;
  FORMAT_TAG_RE.lastIndex = 0;

  while ((match = FORMAT_TAG_RE.exec(raw)) !== null) {
    const id = match[1] ?? '';
    formats[id] = {
      id,
      name: match[2] ?? '',
      purpose: match[3] ?? '',
      body: (match[4] ?? '').trim(),
    };
  }

  return formats;
}

/**
 * Parse an adaptor.md file into structured data.
 * @param filePath - Absolute path to the adaptor.md file.
 * @returns Parsed AdaptorData.
 */
export async function parseAdaptorMd(filePath: string): Promise<AdaptorData> {
  const raw = await fs.readFile(filePath, 'utf8');
  return parseAdaptorMdString(raw);
}

/**
 * Parse an adaptor.md string into structured data.
 * @param raw - Raw adaptor.md content.
 * @returns Parsed AdaptorData.
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
export function getString(constants: Record<string, ConstantValue>, key: string, fallback = ''): string {
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
