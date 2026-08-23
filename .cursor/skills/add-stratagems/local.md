# Locate local installs

Resolve everything below at runtime. Do not hardcode home directories, clone paths, or GitHub usernames.

## Plugin repo

The plugin root is the directory that contains both `update/config.py` and `manifest.json` with `"id": "net_jslay_helldivers_2"`.

Prefer the current workspace root. If this skill is running from another workspace, search sibling directories and ask if it is still unclear.

```bash
# from plugin root
git remote -v
git rev-parse --show-toplevel
```

## Store checkout

Look for a clone of `StreamController/StreamController-Store` or a fork of it:

1. Other workspace roots in this session
2. Sibling directories of the plugin repo (`../StreamController-Store`, `../streamcontroller-store`, etc.)
3. `gh repo list --fork` / ask the user

Required remotes once found:

| Remote | Repo |
|--------|------|
| `upstream` | `StreamController/StreamController-Store` |
| `origin` | the user's fork |

If `upstream` is missing, add it. Fork owner for `--head` is the `origin` GitHub owner (`git remote get-url origin`), not a hardcoded username.

## StreamController data dir

Live plugin files come from the **installed app**, not a StreamController source checkout.

Search in order and use the first that contains `plugins/net_jslay_helldivers_2`:

```bash
PLUGIN_ID="net_jslay_helldivers_2"

# Flatpak (typical on Linux)
echo "$HOME/.var/app/com.core447.StreamController/data"

# Native / custom --data path
echo "${XDG_DATA_HOME:-$HOME/.local/share}/StreamController"
# also check running process args for --data
```

Confirm:

```
$DATA/plugins/$PLUGIN_ID/manifest.json
$DATA/settings/settings.json
```

If both Flatpak and a native install exist, ask which one they are testing. If the plugin is not installed, say so and skip link/restore.

`settings.json` key: `store.auto-update` (boolean). This is global (all store assets). There is no per-plugin switch.

Flatpak `com.core447.StreamController` usually has `filesystems=home`, so a symlink into a repo under `$HOME` works. If the install is sandboxed without home access, stop and tell the user.

## Link for testing

`SRC` is the plugin repo root from above (`git rev-parse --show-toplevel`).

```bash
PLUGIN_ID="net_jslay_helldivers_2"
PLUGIN_DIR="$DATA/plugins"
TARGET="$PLUGIN_DIR/$PLUGIN_ID"
BACKUP="$PLUGIN_DIR/${PLUGIN_ID}.store.bak"

# If TARGET is already a symlink to SRC, skip.
# If BACKUP exists, stop and ask.

mv "$TARGET" "$BACKUP"
ln -s "$SRC" "$TARGET"
```

Then set `store.auto-update` to `false` in `$DATA/settings/settings.json`. Confirm `manifest.json` through the symlink is the checkout version.

## Restore

```bash
TARGET="$PLUGIN_DIR/$PLUGIN_ID"
BACKUP="$PLUGIN_DIR/${PLUGIN_ID}.store.bak"

# If the backup used a versioned suffix (*.store-*.bak), use that path instead.

rm "$TARGET"          # symlink only; do not rm -rf
mv "$BACKUP" "$TARGET"
```

Set `store.auto-update` to `true`. Confirm `TARGET` is a directory, not a symlink, and `manifest.json` is the store version.
