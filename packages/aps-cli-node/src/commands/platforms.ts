import { loadPlatforms, resolvePayloadSkillDir, type PlatformInfo } from '../core.js';
import { sortPlatformsForUi } from '../detection/adapters.js';

/**
 * Renders an ASCII table similar to Python's Rich Table.
 * @param platforms - Array of platform info objects.
 * @returns Formatted table string.
 */
function renderPlatformsTable(platforms: readonly PlatformInfo[]): string {
  const headers = ['platform_id', 'display_name', 'adapter_version'];

  // Calculate column widths based on header + data
  const widths = headers.map((h, i) => {
    const dataMax = platforms.reduce((max, p) => {
      const val = i === 0 ? p.platformId : i === 1 ? p.displayName : p.adapterVersion ?? '';
      return Math.max(max, val.length);
    }, 0);
    return Math.max(h.length, dataMax);
  });

  // Box drawing characters
  const topBorder = '┌' + widths.map((w) => '─'.repeat(w + 2)).join('┬') + '┐';
  const headerSep = '├' + widths.map((w) => '─'.repeat(w + 2)).join('┼') + '┤';
  const bottomBorder = '└' + widths.map((w) => '─'.repeat(w + 2)).join('┴') + '┘';

  const padCell = (text: string, width: number) => ` ${text.padEnd(width)} `;

  const headerRow =
    '│' + headers.map((h, i) => padCell(h, widths[i] ?? 0)).join('│') + '│';

  const dataRows = platforms.map(
    (p) =>
      '│' +
      [
        padCell(p.platformId, widths[0] ?? 0),
        padCell(p.displayName, widths[1] ?? 0),
        padCell(p.adapterVersion ?? '', widths[2] ?? 0),
      ].join('│') +
      '│'
  );

  return [topBorder, headerRow, headerSep, ...dataRows, bottomBorder].join('\n');
}

export async function runPlatforms(): Promise<void> {
  const payloadSkillDir = await resolvePayloadSkillDir();
  const platforms = await loadPlatforms(payloadSkillDir);
  const sorted = sortPlatformsForUi(platforms);

  console.log('             APS Platform Adapters              ');
  console.log(renderPlatformsTable(sorted));
}
