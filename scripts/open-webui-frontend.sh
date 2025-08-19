#!/bin/bash
# shellcheck disable=SC1091
set -e

script_file_path="${BASH_SOURCE[0]}"
script_dir_path="$(cd "$(dirname "$script_file_path")" && pwd)"
root_dir_path="$(cd "$script_dir_path/.." && pwd)"

if [ "$(pwd)" != "$root_dir_path" ]; then
    cd "$root_dir_path"
fi

if [ -d .venv ]; then
    source .venv/bin/activate
fi

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p

npm run dev
