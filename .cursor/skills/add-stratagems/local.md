# Local paths (jslay)

## Repos

| Role | Path | Remotes |
|------|------|---------|
| Plugin | `/home/jslay/dev/streamcontroller_helldivers_2` | `origin` → `jslay88/streamcontroller_helldivers_2` |
| Store fork | `/home/jslay/dev/StreamController-Store` | `origin` → `jslay88/StreamController-Store`, `upstream` → `StreamController/StreamController-Store` |
| StreamController source | `/home/jslay/dev/StreamController` | not used for this workflow |

Live install is the **Flatpak**, not the source checkout.

## Flatpak

```
~/.var/app/com.core447.StreamController/data/plugins/net_jslay_helldivers_2
~/.var/app/com.core447.StreamController/data/settings/settings.json
```

`com.core447.StreamController` has `filesystems=home`, so a symlink into `~/dev/...` works.

`settings.json` key: `store.auto-update` (boolean). This is global (all store assets). There is no per-plugin switch.

## Link for testing

```bash
PLUGIN_DIR="$HOME/.var/app/com.core447.StreamController/data/plugins"
SRC="$HOME/dev/streamcontroller_helldivers_2"
TARGET="$PLUGIN_DIR/net_jslay_helldivers_2"
BACKUP="$PLUGIN_DIR/net_jslay_helldivers_2.store.bak"

# If TARGET is already a symlink to SRC, skip.
# If BACKUP exists, stop and ask.

mv "$TARGET" "$BACKUP"
ln -s "$SRC" "$TARGET"
```

Then set `store.auto-update` to `false` in `settings.json`. Confirm `manifest.json` through the symlink is the checkout version.

## Restore

```bash
PLUGIN_DIR="$HOME/.var/app/com.core447.StreamController/data/plugins"
TARGET="$PLUGIN_DIR/net_jslay_helldivers_2"
BACKUP="$PLUGIN_DIR/net_jslay_helldivers_2.store.bak"

rm "$TARGET"          # symlink only
mv "$BACKUP" "$TARGET"
```

Set `store.auto-update` to `true`. Confirm `TARGET` is a directory, not a symlink, and `manifest.json` is the store version.

If the backup name from an older run was `net_jslay_helldivers_2.store-2.3.1.bak`, use that path instead.
