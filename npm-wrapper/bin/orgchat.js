#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawnSync, execFileSync } = require('child_process');
const args = process.argv.slice(2);

const pkg = require('../package.json');
const ORGCHAT_VERSION = pkg.version || '0.1.0';

function getCacheDir() {
  const home = process.env.HOME || process.env.USERPROFILE || require('os').homedir();
  if (process.platform === 'win32') {
    const local = process.env.LOCALAPPDATA;
    if (local) return path.join(local, 'orgchat');
    return path.join(home, '.cache', 'orgchat');
  }
  const xdg = process.env.XDG_CACHE_HOME;
  if (xdg) return path.join(xdg, 'orgchat');
  if (process.platform === 'darwin') return path.join(home, 'Library', 'Caches', 'orgchat');
  return path.join(home, '.cache', 'orgchat');
}

const CACHE_DIR = getCacheDir();
const RUNTIME_DIR = path.join(CACHE_DIR, 'runtimes', ORGCHAT_VERSION);
const VENV_DIR = path.join(RUNTIME_DIR, '.venv');
const PYTHON = process.platform === 'win32' ? path.join(VENV_DIR, 'Scripts', 'python.exe') : path.join(VENV_DIR, 'bin', 'python');

function getPythonCandidates() {
  if (process.platform === 'win32') {
    return [
      { cmd: 'py', args: ['-3.13'] },
      { cmd: 'py', args: ['-3.12'] },
      { cmd: 'py', args: ['-3.11'] },
      { cmd: 'python', args: [] },
      { cmd: 'python3', args: [] },
    ];
  }
  return [
    { cmd: 'python3', args: [] },
    { cmd: 'python', args: [] },
  ];
}

function getPythonVersion(candidate) {
  try {
    const out = execFileSync(candidate.cmd, [...candidate.args, '--version'], { encoding: 'utf8', timeout: 5000 }).trim();
    const m = out.match(/Python\s+(\d+)\.(\d+)/);
    if (m) return { major: parseInt(m[1]), minor: parseInt(m[2]), raw: out };
  } catch {}
  return null;
}

function findCompatiblePython() {
  const candidates = getPythonCandidates();
  const checked = [];
  for (const c of candidates) {
    const ver = getPythonVersion(c);
    const label = (c.args.length ? c.cmd + ' ' + c.args.join(' ') : c.cmd);
    if (ver) {
      checked.push({ label, ver, ok: ver.major === 3 && ver.minor >= 11 });
      if (ver.major === 3 && ver.minor >= 11) return { cmd: c.cmd, args: c.args, ver, ok: true };
    } else {
      checked.push({ label, ver: null, ok: false });
    }
  }
  return { checked, ok: false };
}

function ensureRuntime() {
  const result = findCompatiblePython();
  if (!result.ok) {
    console.error('OrgChat requires Python 3.11+.');
    console.error('No compatible Python runtime was found.');
    console.error('Checked:');
    const list = Array.isArray(result.checked) ? result.checked : [];
    for (const c of list) {
      const status = c.ok ? '✓' : (c.ver ? `Python ${c.ver.raw.split(' ')[1]}` : 'not found');
      console.error(`  ${c.label.padEnd(16)}  ${status}`);
    }
    console.error('Install Python 3.11+ and run again:\n  npx orgchat check');
    process.exit(1);
  }

  // Health check existing runtime
  if (fs.existsSync(VENV_DIR)) {
    try {
      const verOut = execFileSync(PYTHON, ['-c', 'import orgchat; print(orgchat.__version__)'], { encoding: 'utf8', timeout: 10000 }).trim();
      if (verOut === ORGCHAT_VERSION) {
        return; // fully healthy
      }
      console.log('Updating OrgChat runtime...');
      // version mismatch: rebuild
      try {
        fs.rmSync(VENV_DIR, { recursive: true, force: true });
      } catch {}
    } catch {
      // broken import or missing executable
      console.log('OrgChat runtime appears corrupted. Rebuilding...');
      try {
        fs.rmSync(VENV_DIR, { recursive: true, force: true });
      } catch {}
    }
  }

  // Create / recreate
  try {
    if (!fs.existsSync(VENV_DIR)) {
      fs.mkdirSync(path.dirname(VENV_DIR), { recursive: true });
      console.log('Preparing isolated runtime...');
      const { cmd, args } = result;
      execFileSync(cmd, [...args, '-m', 'venv', VENV_DIR], { stdio: 'inherit', timeout: 30000 });
    }
  } catch (exc) {
    console.error('Failed to create isolated runtime. Check permissions/network.');
    console.error('Details:', exc.message || exc);
    process.exit(1);
  }

  // Install / repair
  try {
    const check = execFileSync(PYTHON, ['-c', 'import orgchat; print(orgchat.__version__)'], { encoding: 'utf8', timeout: 10000 }).trim();
    if (check === ORGCHAT_VERSION) return;
  } catch {}
  try {
    console.log('Installing OrgChat ' + ORGCHAT_VERSION + '...');
    try {
      execFileSync(PYTHON, ['-m', 'pip', 'install', '--quiet', 'orgchat==' + ORGCHAT_VERSION], { stdio: 'inherit', timeout: 120000 });
    } catch {
      console.log('Trying unversioned install...');
      execFileSync(PYTHON, ['-m', 'pip', 'install', '--quiet', 'orgchat'], { stdio: 'inherit', timeout: 120000 });
    }
    const verify = execFileSync(PYTHON, ['-c', 'import orgchat; print(orgchat.__version__)'], { encoding: 'utf8', timeout: 10000 }).trim();
    if (verify === ORGCHAT_VERSION) {
      console.log('✓ OrgChat ' + ORGCHAT_VERSION + ' ready');
    } else {
      console.error('Version mismatch after install. Expected ' + ORGCHAT_VERSION + ' got ' + verify);
      // If installed is newer/older, rebuild once
      try { fs.rmSync(VENV_DIR, { recursive: true, force: true }); } catch {}
      console.log('Rebuilding with correct version...');
      const { cmd, args } = result;
      execFileSync(cmd, [...args, '-m', 'venv', VENV_DIR], { stdio: 'inherit', timeout: 30000 });
      execFileSync(path.join(VENV_DIR, process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'), ['-m', 'pip', 'install', '--quiet', '--force-reinstall', 'orgchat==' + ORGCHAT_VERSION], { stdio: 'inherit', timeout: 120000 });
      const verify2 = execFileSync(PYTHON, ['-c', 'import orgchat; print(orgchat.__version__)'], { encoding: 'utf8', timeout: 10000 }).trim();
      if (verify2 === ORGCHAT_VERSION) {
        console.log('✓ OrgChat ' + ORGCHAT_VERSION + ' ready');
      } else {
        console.error('Still version mismatch: ' + verify2);
        process.exit(1);
      }
    }
  } catch (exc) {
    console.error('Failed to install OrgChat runtime. Check network/permissions.');
    console.error('Details:', exc.message || exc);
    process.exit(1);
  }
}

ensureRuntime();

const child = spawn(PYTHON, ['-m', 'orgchat', ...args], {
  stdio: 'inherit',
  cwd: process.cwd()
});
child.on('close', (code) => process.exit(code ?? 0));
