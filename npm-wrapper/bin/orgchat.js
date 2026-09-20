#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const args = process.argv.slice(2);

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

function getPythonVersion(pythonPath) {
  try {
    const out = execSync(`"${pythonPath}" --version`, { encoding: 'utf8', timeout: 5000 }).trim();
    const m = out.match(/Python\s+(\d+)\.(\d+)/);
    if (m) return { major: parseInt(m[1]), minor: parseInt(m[2]) };
  } catch {}
  return null;
}

function findPython() {
  const candidates = process.platform === 'win32'
    ? ['py', 'py -3.13', 'py -3.12', 'py -3.11', 'python', 'python3']
    : ['python3', 'python'];
  for (const cmd of candidates) {
    try {
      const pythonPath = cmd.includes(' ') ? cmd.split(' ')[0] : cmd;
      const ver = getPythonVersion(pythonPath);
      if (ver && ver.major === 3 && ver.minor >= 11) return pythonPath;
    } catch {}
  }
  return null;
}

const CACHE_DIR = getCacheDir();
const VENV_DIR = path.join(CACHE_DIR, 'runtimes', '0.1.0', '.venv');
const PYTHON = process.platform === 'win32' ? path.join(VENV_DIR, 'Scripts', 'python.exe') : path.join(VENV_DIR, 'bin', 'python');

function ensureRuntime() {
  const pythonBin = findPython();
  if (!pythonBin) {
    console.error('OrgChat needs Python 3.11 or newer.\nNo compatible Python runtime was found.');
    console.error('Install Python 3.11+ and run again: npx orgchat check');
    process.exit(1);
  }
  if (!fs.existsSync(VENV_DIR)) {
    fs.mkdirSync(path.dirname(VENV_DIR), { recursive: true });
    try {
      console.log('Preparing isolated runtime...');
      execSync(`"${pythonBin}" -m venv "${VENV_DIR}"`, { stdio: 'inherit' });
    } catch {
      console.error('Failed to create isolated runtime. Check permissions/network.');
      process.exit(1);
    }
  }
  try {
    execSync(`"${PYTHON}" -c "import orgchat"`, { stdio: 'pipe', timeout: 10000 });
  } catch {
    try {
      console.log('Installing OrgChat runtime...');
      execSync(`"${PYTHON}" -m pip install --quiet orgchat==0.1.0`, { stdio: 'inherit', timeout: 120000 });
    } catch {
      console.error('Failed to install OrgChat runtime. Check network/permissions.');
      process.exit(1);
    }
  }
}

ensureRuntime();
const child = spawn(PYTHON, ['-m', 'orgchat', ...args], { stdio: 'inherit' });
child.on('close', (code) => process.exit(code ?? 0));
