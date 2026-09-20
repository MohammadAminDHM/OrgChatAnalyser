#!/usr/bin/env node
const { spawn } = require('child_process');
const args = process.argv.slice(2);

// Try local python module or installed executable
const cmd = process.platform === 'win32' ? 'orgchat' : 'orgchat';
const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

const child = spawn(cmd, args, { stdio: 'inherit', shell: true });
child.on('close', (code) => process.exit(code || 0));
