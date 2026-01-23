import { loadPlatforms, resolvePayloadSkillDir } from '../core.js';

export async function runPlatforms(): Promise<void> {
  const payloadSkillDir = await resolvePayloadSkillDir();
  const platforms = await loadPlatforms(payloadSkillDir);
  console.log('Available platform adapters:');
  for (const p of platforms) {
    console.log(`- ${p.platformId}: ${p.displayName} (v${p.adapterVersion ?? 'unknown'})`);
  }
}
