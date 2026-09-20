# Run orgchat on any device with uv / uvx

## Option 1: Global install (type `orgchat check` anywhere)
uv tool install .

Then inside your project folder:
orgchat check --config orgchat.toml

## Option 2: One-time / no install (uvx)
uvx --from . orgchat check --config orgchat.toml

## Option 3: From this repo on another machine
1. Clone / copy repo
2. uv tool install .
3. cd your-chatbot-project
4. orgchat check
