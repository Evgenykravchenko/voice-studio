import assert from 'node:assert/strict';
import {chmodSync, copyFileSync, existsSync, mkdirSync, mkdtempSync, realpathSync, rmSync, symlinkSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import test from 'node:test';

const repository = fileURLToPath(new URL('../../', import.meta.url));

function pnpmEntry() {
  const local = join(repository, '.runtime/toolchains/pnpm/bin/pnpm.mjs');
  if (existsSync(local)) return local;
  // CI exposes the exact pinned pnpm through npm exec, never a global install.
  const found = spawnSync('/bin/sh', ['-c', 'command -v pnpm'], {encoding: 'utf8'});
  assert.equal(found.status, 0, 'Run these tests with npm exec --package=pnpm@11.25.0 -- node --test');
  const entry = join(dirname(realpathSync(found.stdout.trim())), 'pnpm.mjs');
  assert.ok(existsSync(entry), 'The pinned pnpm ESM entry point is required');
  return entry;
}

function fixture(run) {
  const root = mkdtempSync(join(tmpdir(), 'voice studio local pnpm-'));
  try {
    mkdirSync(join(root, 'scripts'));
    for (const name of ['runtime-env.sh', 'pnpm.sh']) copyFileSync(join(repository, 'scripts', name), join(root, 'scripts', name));
    chmodSync(join(root, 'scripts/pnpm.sh'), 0o755);
    const env = {...process.env, PATH: '/usr/bin:/bin',
      XDG_DATA_HOME: join(root, '.runtime/data'), XDG_CONFIG_HOME: join(root, '.runtime/config'),
      npm_config_store_dir: join(root, '.runtime/store')};
    delete env.CI;
    const missing = spawnSync('/bin/sh', ['-c', 'command -v pnpm'], {env, encoding: 'utf8'});
    assert.notEqual(missing.status, 0, 'The fixture must have no global pnpm');
    run(root, (args, extra = {}) => spawnSync(join(root, 'scripts/pnpm.sh'), args, {cwd: root, env: {...env, ...extra}, encoding: 'utf8', timeout: 60000}));
  } finally { rmSync(root, {recursive: true, force: true}); }
}

test('local pnpm can reinstall and build from a path with spaces without global node or pnpm', () => {
  const entry = pnpmEntry();
  fixture((root, run) => {
    mkdirSync(join(root, '.runtime/toolchains/node/bin'), {recursive: true});
    mkdirSync(join(root, '.runtime/toolchains/pnpm'), {recursive: true});
    symlinkSync(process.execPath, join(root, '.runtime/toolchains/node/bin/node'));
    symlinkSync(dirname(entry), join(root, '.runtime/toolchains/pnpm/bin'), 'dir');
    mkdirSync(join(root, 'frontend'));
    writeFileSync(join(root, 'frontend/package.json'), JSON.stringify({name: 'local-pnpm-fixture', version: '1.0.0', private: true,
      scripts: {build: 'node -e "console.log(\'local-build-ok\')"'}}));
    writeFileSync(join(root, 'frontend/pnpm-lock.yaml'), "lockfileVersion: '9.0'\nsettings:\n  autoInstallPeers: true\n  excludeLinksFromLockfile: false\nimporters:\n  .: {}\n");
    // No node_modules exists: pnpm must re-enter its installer before the script.
    const first = run(['--dir', 'frontend', 'build']);
    assert.equal(first.status, 0, first.stdout + first.stderr);
    assert.match(first.stdout, /local-build-ok/);
    const install = run(['--dir', 'frontend', 'install', '--frozen-lockfile'], {CI: 'true'});
    assert.equal(install.status, 0, install.stdout + install.stderr);
    const again = run(['--dir', 'frontend', 'build']);
    assert.equal(again.status, 0, again.stdout + again.stderr);
    assert.match(again.stdout, /local-build-ok/);
  });
});

test('missing project tools fail clearly instead of using a global package manager', () => {
  fixture((_root, run) => {
    const result = run(['--version']);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /bootstrap\.sh/);
    assert.doesNotMatch(result.stderr, /ENOENT/);
  });
});
