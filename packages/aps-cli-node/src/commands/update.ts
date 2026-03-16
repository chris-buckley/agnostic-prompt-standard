import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs/promises';

import { confirm } from '@inquirer/prompts';

import {
  defaultPersonalSkillPath,
  defaultProjectSkillPath,
  homeDir,
  isDirectory,
  listFilesRecursive,
  pathExists,
  pickWorkspaceRoot,
  replaceDirWithCopy,
  resolvePayloadSkillDir,
  getActivePlatformsForTemplateRoot,
  cleanOldPlatformTemplates,
  copyTemplateTree,
  LEGACY_AGENT_NAMES,
  toPosixPath
} from '../core.js';
import { parseAdaptorMdString } from '../parsers/adaptor.js';

const require = createRequire(import.meta.url);
const pkg = require('../../package.json') as { version: string };

const APS_SKIP_SELF_UPDATE_ENV = 'APS_SKIP_SELF_UPDATE';
const NODE_PACKAGE_NAME = '@agnostic-prompt/aps';
const NPM_REGISTRY_URL = 'https://registry.npmjs.org/@agnostic-prompt%2Faps';

export interface UpdateCliOptions {
  root?: string;
  repo?: boolean;
  personal?: boolean;
  check: boolean;
  json: boolean;
  dryRun: boolean;
  yes: boolean;
  force: boolean;
}

export type NodeRuntimeMode = 'dev-local' | 'local-project' | 'ephemeral' | 'installed';

export type SkillUpdateStatus = 'missing' | 'orphaned' | 'up-to-date' | 'update-available' | 'updated';

export interface SkillUpdateTarget {
  scope: string;
  path: string;
  exists: boolean;
  installedVersion: string | null;
  desiredVersion: string;
  status: SkillUpdateStatus;
}

export interface TemplateUpdateTarget {
  scope: string;
  platformId: string;
  templateRoot: string;
  templatesDir: string;
  status: SkillUpdateStatus;
  removed: string[];
  copied: string[];
}

interface PackageUpdateStatus {
  packageName: string;
  currentVersion: string;
  payloadVersion: string;
  latestVersion: string | null;
  updateAvailable: boolean;
  runtimeMode: NodeRuntimeMode;
  registryError: string | null;
}

function isTTY(): boolean {
  return Boolean(process.stdout.isTTY && process.stdin.isTTY);
}

function fmtPath(p: string): string {
  const home = process.env.HOME ?? process.env.USERPROFILE;
  if (!home) return p;
  if (p === home) return '~';

  const prefix = home.endsWith(path.sep) ? home : `${home}${path.sep}`;
  return p.startsWith(prefix) ? `~${p.slice(home.length)}` : p;
}

function parseSemver(v: string): [number, number, number] | null {
  const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(v.trim());
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

export function compareSemver(a: string, b: string): number {
  const pa = parseSemver(a);
  const pb = parseSemver(b);
  if (!pa || !pb) return a.localeCompare(b);

  for (let i = 0; i < 3; i += 1) {
    if (pa[i] !== pb[i]) return pa[i]! > pb[i]! ? 1 : -1;
  }
  return 0;
}

export function detectNodeRuntimeMode(scriptPath: string): NodeRuntimeMode {
  const normalized = scriptPath.split(path.sep).join('/');

  if (normalized.includes('/packages/aps-cli-node/')) return 'dev-local';
  if (normalized.includes('/_npx/') || normalized.includes('/npm-cache/') || normalized.includes('/.npm/_npx/')) {
    return 'ephemeral';
  }
  if (normalized.includes('/lib/node_modules/') || normalized.includes('/AppData/Roaming/npm/node_modules/')) {
    return 'installed';
  }
  if (normalized.includes('/node_modules/')) return 'local-project';
  return 'installed';
}

function readFrameworkRevision(text: string): string | null {
  const m = /framework_revision:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?/.exec(text);
  return m?.[1] ?? null;
}

async function readSkillMdVersion(skillDir: string): Promise<string | null> {
  const skillMd = path.join(skillDir, 'SKILL.md');
  if (!(await pathExists(skillMd))) return null;

  try {
    const text = await fs.readFile(skillMd, 'utf-8');
    return readFrameworkRevision(text);
  } catch {
    return null;
  }
}

function extractVersionCandidates(text: string): string[] {
  const out = new Set<string>();

  for (const pattern of [/framework_revision:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?/g, /aps-v([0-9]+\.[0-9]+\.[0-9]+)(?:\.agent)?\.md\b/g]) {
    for (const match of text.matchAll(pattern)) {
      const version = match[1];
      if (version) out.add(version);
    }
  }

  return [...out];
}

function pickHighestVersion(versions: Iterable<string>): string | null {
  let highest: string | null = null;

  for (const version of versions) {
    if (!highest || compareSemver(version, highest) > 0) {
      highest = version;
    }
  }

  return highest;
}

export async function inferInstalledSkillVersion(skillDir: string): Promise<string | null> {
  const skillMdVersion = await readSkillMdVersion(skillDir);
  if (skillMdVersion) return skillMdVersion;

  const versions = new Set<string>();
  const platformsDir = path.join(skillDir, 'platforms');
  if (!(await isDirectory(platformsDir))) return null;

  try {
    const files = await listFilesRecursive(platformsDir);

    for (const filePath of files) {
      for (const version of extractVersionCandidates(filePath)) {
        versions.add(version);
      }

      if (path.basename(filePath) !== 'adaptor.md') continue;
      try {
        const text = await fs.readFile(filePath, 'utf-8');
        for (const version of extractVersionCandidates(text)) {
          versions.add(version);
        }
      } catch {
        // Ignore unreadable adaptor files while inferring a best-effort version.
      }
    }
  } catch {
    return null;
  }

  return pickHighestVersion(versions);
}

export async function fetchLatestCliVersion(fetchImpl: typeof fetch = fetch): Promise<string> {
  const res = await fetchImpl(NPM_REGISTRY_URL, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error(`npm registry request failed with status ${res.status}`);
  }

  const data = (await res.json()) as { 'dist-tags'?: { latest?: string } };
  const latest = data['dist-tags']?.latest;
  if (!latest || !parseSemver(latest)) {
    throw new Error('npm registry response did not include a valid latest dist-tag');
  }

  return latest;
}

export async function collectSkillTargets(options: {
  root?: string | undefined;
  repo?: boolean | undefined;
  personal?: boolean | undefined;
  desiredVersion: string;
}): Promise<SkillUpdateTarget[]> {
  const workspaceRoot = await pickWorkspaceRoot(options.root);

  if (options.repo && !workspaceRoot) {
    throw new Error('Repo update selected but no workspace root found. Run in a git repo or pass --root <path>.');
  }

  const explicitScope = Boolean(options.repo || options.personal);
  const candidates: Array<{ scope: string; path: string }> = [];

  if (options.repo || (!explicitScope && workspaceRoot)) {
    if (workspaceRoot) {
      candidates.push({ scope: 'repo', path: defaultProjectSkillPath(workspaceRoot, { claude: false }) });
      candidates.push({ scope: 'repo (claude)', path: defaultProjectSkillPath(workspaceRoot, { claude: true }) });
    }
  }

  if (options.personal || !explicitScope) {
    candidates.push({ scope: 'personal', path: defaultPersonalSkillPath({ claude: false }) });
    candidates.push({ scope: 'personal (claude)', path: defaultPersonalSkillPath({ claude: true }) });
  }

  const seen = new Set<string>();
  const results: SkillUpdateTarget[] = [];

  for (const candidate of candidates) {
    if (seen.has(candidate.path)) continue;
    seen.add(candidate.path);

    const exists = await pathExists(candidate.path);
    if (!explicitScope && !exists) continue;

    const hasEntrypoint = exists ? await pathExists(path.join(candidate.path, 'SKILL.md')) : false;
    const installedVersion = exists ? await inferInstalledSkillVersion(candidate.path) : null;
    const status: SkillUpdateStatus = !exists
      ? 'missing'
      : !hasEntrypoint
        ? 'orphaned'
        : installedVersion === options.desiredVersion
          ? 'up-to-date'
          : 'update-available';

    results.push({
      scope: candidate.scope,
      path: candidate.path,
      exists,
      installedVersion,
      desiredVersion: options.desiredVersion,
      status,
    });
  }

  return results;
}

export async function collectTemplateTargets(
  options: {
    root?: string | undefined;
    repo?: boolean | undefined;
    personal?: boolean | undefined;
    payloadSkillDir: string;
  }
): Promise<TemplateUpdateTarget[]> {
  const workspaceRoot = await pickWorkspaceRoot(options.root);
  const explicitScope = Boolean(options.repo || options.personal);
  
  const scopes: Array<{ scope: string; root: string }> = [];
  
  if (options.repo || (!explicitScope && workspaceRoot)) {
    if (workspaceRoot) scopes.push({ scope: 'repo', root: workspaceRoot });
  }
  
  if (options.personal || !explicitScope) {
    const home = homeDir();
    if (home) scopes.push({ scope: 'personal', root: home });
  }
  
  const targets: TemplateUpdateTarget[] = [];
  
  for (const { scope, root } of scopes) {
    const activePlatformIds = await getActivePlatformsForTemplateRoot(root, options.payloadSkillDir);
    if (activePlatformIds.length === 0) continue;
    
    for (const platformId of activePlatformIds) {
      const templatesDir = path.join(options.payloadSkillDir, 'platforms', platformId, 'templates');
      
      let hasUpdate = false;
      let hasOldFiles = false;
      
      const adaptorPath = path.join(options.payloadSkillDir, 'platforms', platformId, 'adaptor.md');
      try {
        const raw = await fs.readFile(adaptorPath, 'utf8');
        const data = parseAdaptorMdString(raw);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const versioning = data.constants['AGENT_VERSIONING'] as any;
        if (versioning && Array.isArray(versioning.templates)) {
          for (const tmpl of versioning.templates) {
            let pathPattern = tmpl.path as string;
            let currentPath = (tmpl.current_path || tmpl.currentPath) as string;
            if (!pathPattern || !currentPath) continue;

            if (pathPattern.startsWith('templates/')) pathPattern = pathPattern.slice(10);
            if (currentPath.startsWith('templates/')) currentPath = currentPath.slice(10);

            const dirName = path.dirname(pathPattern);
            const fileNamePattern = path.basename(pathPattern);
            const currentFileName = path.basename(currentPath);

            let regexStr = fileNamePattern.replace(/\./g, '\\.');
            regexStr = regexStr.replace(/\{[a-z]+\}/g, '\\d+');
            const regex = new RegExp(`^${regexStr}$`);

            const targetDir = path.join(root, dirName);
            if (await pathExists(targetDir)) {
              const entries = await fs.readdir(targetDir, { withFileTypes: true });
              for (const entry of entries) {
                if (!entry.isFile()) continue;
                if (LEGACY_AGENT_NAMES.includes(entry.name) || (regex.test(entry.name) && entry.name !== currentFileName)) {
                  hasOldFiles = true;
                }
              }
            }
            if (!(await pathExists(path.join(root, currentPath)))) {
              hasUpdate = true;
            }
          }
        }
      } catch {}
      
      if (!hasUpdate && await isDirectory(templatesDir)) {
        try {
          const allFiles = await listFilesRecursive(templatesDir);
          for (const src of allFiles) {
            const relPath = toPosixPath(path.relative(templatesDir, src));
            if (!(await pathExists(path.join(root, relPath)))) {
               hasUpdate = true;
               break;
            }
          }
        } catch {}
      }
      
      targets.push({
        scope,
        platformId,
        templateRoot: root,
        templatesDir,
        status: (hasUpdate || hasOldFiles) ? 'update-available' : 'up-to-date',
        removed: [],
        copied: [],
      });
    }
  }
  
  return targets;
}

function buildForwardedArgs(options: UpdateCliOptions): string[] {
  const args = ['update'];
  if (options.root) args.push('--root', options.root);
  if (options.repo) args.push('--repo');
  if (options.personal) args.push('--personal');
  if (options.check) args.push('--check');
  if (options.json) args.push('--json');
  if (options.dryRun) args.push('--dry-run');
  if (options.yes) args.push('--yes');
  if (options.force) args.push('--force');
  return args;
}

function runAndExit(command: string, args: string[]): never {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    env: {
      ...process.env,
      [APS_SKIP_SELF_UPDATE_ENV]: '1',
    },
  });

  if (result.error) {
    throw result.error;
  }

  process.exit(result.status ?? 1);
}

function tryCommand(command: string, args: string[]): boolean {
  const result = spawnSync(command, args, { stdio: 'inherit' });
  if (result.error) return false;
  return result.status === 0;
}

function maybeSelfUpdate(runtimeMode: NodeRuntimeMode, latestVersion: string, options: UpdateCliOptions): void {
  const forwardedArgs = buildForwardedArgs(options);

  if (runtimeMode === 'dev-local') {
    return;
  }

  if (runtimeMode === 'ephemeral') {
    runAndExit('npx', ['--yes', `${NODE_PACKAGE_NAME}@${latestVersion}`, ...forwardedArgs]);
  }

  if (runtimeMode === 'local-project') {
    if (tryCommand('npm', ['install', `${NODE_PACKAGE_NAME}@${latestVersion}`])) {
      runAndExit(process.execPath, [process.argv[1] ?? '', ...forwardedArgs]);
    }
    runAndExit('npx', ['--yes', `${NODE_PACKAGE_NAME}@${latestVersion}`, ...forwardedArgs]);
  }

  if (tryCommand('npm', ['install', '-g', `${NODE_PACKAGE_NAME}@${latestVersion}`])) {
    runAndExit(process.execPath, [process.argv[1] ?? '', ...forwardedArgs]);
  }

  runAndExit('npx', ['--yes', `${NODE_PACKAGE_NAME}@${latestVersion}`, ...forwardedArgs]);
}

async function applySkillUpdates(
  targets: SkillUpdateTarget[],
  payloadSkillDir: string,
  options: { force: boolean }
): Promise<SkillUpdateTarget[]> {
  const updatedTargets: SkillUpdateTarget[] = [];

  for (const target of targets) {
    if (!target.exists) {
      updatedTargets.push(target);
      continue;
    }

    if (target.status === 'up-to-date' && !options.force) {
      updatedTargets.push(target);
      continue;
    }

    await replaceDirWithCopy(payloadSkillDir, target.path);
    updatedTargets.push({
      ...target,
      exists: true,
      installedVersion: target.desiredVersion,
      status: 'updated',
    });
  }

  return updatedTargets;
}

export async function applyTemplateUpdates(
  targets: TemplateUpdateTarget[],
  payloadSkillDir: string,
  options: { force: boolean }
): Promise<TemplateUpdateTarget[]> {
  const updated: TemplateUpdateTarget[] = [];

  for (const target of targets) {
    if (target.status === 'up-to-date' && !options.force) {
      updated.push(target);
      continue;
    }

    const removed = await cleanOldPlatformTemplates(target.templateRoot, target.platformId, payloadSkillDir);
    
    const filter = (relPath: string): boolean => {
      if (target.scope === 'personal' && relPath.startsWith('.github')) return false;
      return true;
    };

    let copied: string[] = [];
    if (await isDirectory(target.templatesDir)) {
      copied = await copyTemplateTree(target.templatesDir, target.templateRoot, {
        force: true, // Overwriting during update process
        filter,
      });
    }
    
    updated.push({
      ...target,
      status: 'updated',
      removed,
      copied,
    });
  }
  return updated;
}

function renderTextReport(packageStatus: PackageUpdateStatus, targets: SkillUpdateTarget[], templateTargets: TemplateUpdateTarget[], options: UpdateCliOptions): void {
  console.log('APS Update');
  console.log('----------');
  console.log(`CLI package: ${packageStatus.packageName}`);
  console.log(`Current CLI version: ${packageStatus.currentVersion}`);
  console.log(`Bundled skill version: ${packageStatus.payloadVersion}`);

  if (packageStatus.latestVersion) {
    const summary = packageStatus.updateAvailable
      ? `${packageStatus.latestVersion} (newer release available)`
      : `${packageStatus.latestVersion} (already current)`;
    console.log(`Latest registry version: ${summary}`);
  } else {
    console.log(`Latest registry version: unavailable (${packageStatus.registryError ?? 'unknown error'})`);
  }

  console.log(`Runtime mode: ${packageStatus.runtimeMode}`);

  if (packageStatus.updateAvailable && process.env[APS_SKIP_SELF_UPDATE_ENV] !== '1' && !options.yes && !options.check && !options.dryRun) {
    console.log('');
    console.log('Note: The running CLI is older than the latest published release.');
    console.log(`      Re-run with npx ${NODE_PACKAGE_NAME}@latest update to refresh from the newest payload immediately.`);
  }

  console.log('');
  console.log(options.check || options.dryRun ? 'Skill installations:' : 'Skill installation results:');

  if (targets.length === 0) {
    console.log('- (none found)');
  } else {
    const statusLabels: Record<string, string> = {
      'updated': 'Refreshed',
      'up-to-date': 'Up to date',
      'update-available': 'Update available',
      'missing': 'Not found',
      'orphaned': 'Orphaned',
    };

    for (const target of targets) {
      const label = statusLabels[target.status] ?? target.status;
      let versionInfo: string;
      if (!target.installedVersion) {
        versionInfo = `target ${target.desiredVersion}`;
      } else if (target.installedVersion === target.desiredVersion) {
        versionInfo = `reinstalled v${target.desiredVersion}`;
      } else {
        versionInfo = `${target.installedVersion} -> ${target.desiredVersion}`;
      }
      console.log(`- ${target.scope}: ${label} ${fmtPath(target.path)} (${versionInfo})`);
    }
  }

  if (templateTargets && templateTargets.length > 0) {
    console.log('');
    console.log(options.check || options.dryRun ? 'Platform template updates:' : 'Platform template results:');
    for (const target of templateTargets) {
      if (target.status === 'updated' && (target.removed.length > 0 || target.copied.length > 0)) {
        console.log(`  ${target.platformId} (${target.scope}):`);
        if (target.removed.length > 0) {
          console.log(`    Removed ${target.removed.length} old file(s):`);
          for (const file of target.removed) {
            console.log(`      - ${file}`);
          }
        }
        if (target.copied.length > 0) {
          console.log(`    Added ${target.copied.length} new file(s):`);
          for (const file of target.copied) {
            console.log(`      - ${file}`);
          }
        }
      } else {
        const statusLabel = target.status === 'up-to-date' ? 'up to date' : target.status;
        console.log(`  - ${target.platformId} (${target.scope}): ${statusLabel}`);
      }
    }
  }

  if (!targets.length && (!templateTargets || !templateTargets.length) && !options.check && !options.dryRun) {
    console.log('');
    console.log('Nothing to update. Run `aps init` first to install APS.');
  }
}

export async function runUpdate(options: UpdateCliOptions): Promise<void> {
  const payloadSkillDir = await resolvePayloadSkillDir();
  const payloadVersion = (await readSkillMdVersion(payloadSkillDir)) ?? pkg.version;
  const runtimeMode = detectNodeRuntimeMode(process.argv[1] ?? fileURLToPath(import.meta.url));

  let latestVersion: string | null = null;
  let registryError: string | null = null;

  try {
    latestVersion = await fetchLatestCliVersion();
  } catch (err) {
    registryError = err instanceof Error ? err.message : String(err);
  }

  const packageStatus: PackageUpdateStatus = {
    packageName: NODE_PACKAGE_NAME,
    currentVersion: pkg.version,
    payloadVersion,
    latestVersion,
    updateAvailable: Boolean(latestVersion && compareSemver(latestVersion, pkg.version) > 0),
    runtimeMode,
    registryError,
  };

  if (
    packageStatus.updateAvailable &&
    !options.check &&
    !options.dryRun &&
    !options.json &&
    process.env[APS_SKIP_SELF_UPDATE_ENV] !== '1' &&
    runtimeMode !== 'dev-local'
  ) {
    let shouldSelfUpdate = options.yes;

    if (!shouldSelfUpdate && isTTY()) {
      shouldSelfUpdate = await confirm({
        message: `A newer APS CLI release is available (${pkg.version} -> ${latestVersion}). Update the CLI package now before refreshing installed skills?`,
        default: true,
      });
    }

    if (shouldSelfUpdate && latestVersion) {
      maybeSelfUpdate(runtimeMode, latestVersion, options);
      return;
    }
  }

  const plannedTargets = await collectSkillTargets({
    root: options.root,
    repo: options.repo,
    personal: options.personal,
    desiredVersion: payloadVersion,
  });

  const plannedTemplates = await collectTemplateTargets({
    root: options.root,
    repo: options.repo,
    personal: options.personal,
    payloadSkillDir,
  });

  const targets = options.check || options.dryRun
    ? plannedTargets
    : await applySkillUpdates(plannedTargets, payloadSkillDir, { force: options.force });

  const templates = options.check || options.dryRun
    ? plannedTemplates
    : await applyTemplateUpdates(plannedTemplates, payloadSkillDir, { force: options.force });

  if (options.json) {
    console.log(JSON.stringify({
      package: packageStatus,
      installations: targets,
      templates,
      mode: options.check ? 'check' : options.dryRun ? 'dry-run' : 'apply',
    }, null, 2));
    return;
  }

  renderTextReport(packageStatus, targets, templates, options);
}
