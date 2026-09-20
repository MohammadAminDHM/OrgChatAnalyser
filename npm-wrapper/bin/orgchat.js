#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const args = process.argv.slice(2);

const CACHE_DIR = path.resolve(__dirname, '..', '.cache', 'orgchat');
const VENV_DIR = path.join(CACHE_DIR, '.venv');
const PYTHON = process.platform === 'win32' ? path.join(VENV_DIR, 'Scripts', 'python.exe') : path.join(VENV_DIR, 'bin', 'python');

function ensureVenv() {
  if (!fs.existsSync(VENV_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    execSync(`${process.platform === 'win32' ? 'py' : 'python3'} -m venv ${VENV_DIR}`, { stdio: 'inherit' });
  }
  try {
    execSync(`${PYTHON} -c "import orgchat"`, { stdio: 'pipe' });
  } catch {
    execSync(`${PYTHON} -m pip install --quiet orgchat`, { stdio: 'inherit' });
  }
}

ensureVenv();
const child = spawn(PYTHON, ['-m', 'orgchat', ...args], { stdio: 'inherit' });
child.on('close', (code) => process.exit(code ?? 0));
