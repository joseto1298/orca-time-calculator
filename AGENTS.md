# AGENTS.md

## What this is
- Single-file OrcaSlicer plugin: `calculadora_tiempo.py`. No package, test suite, linter, CI, or git history in this folder.
- PEP 723 script: metadata lives in the `# /// script` header, including `[tool.orcaslicer.plugin]`.
- **Bump `# version = "x.y.z"` on every change**, or OrcaSlicer may keep the old build when reinstalling.
- Install: OrcaSlicer -> Plugins -> Install local plugin -> select `calculadora_tiempo.py` (requires a recent/nightly build with Python plugin support).

## Validate (no test command exists)
- Python syntax: `python -c "import ast; ast.parse(open('calculadora_tiempo.py', encoding='utf-8').read())"`
- `import orca` only exists inside OrcaSlicer. To import the module in a test, stub an `orca` module in `sys.modules` first: `orca.pages.PagesPluginCapabilityBase`, `orca.slicing.{SlicingPipelineCapabilityBase,Step}`, `ExecutionResult`, `PluginResult`, `LifecycleEvent`, `LifecycleEvtCode`, `register_capability`, `plugin`, `base`.
- JS syntax: extract the `<script>` from `PAGE` and compile/run it under Node with a small DOM/bridge stub. Test default independent mode, sequential mode, reset, no-data and recovery.
- `_scan()` reads only the exact paths captured in `_CURRENT_GCODE_PATHS`; use a synthetic G-code path and monkeypatch `_live_plates()`/`_metrics_for()` for deterministic tests.
- Real 5-plate regression session: `%TEMP%\orcaslicer_model\Fri_Oct_30\13_38_03#16108#42` → 71334 s, 357.47 g, 8.94, names empty (fallback `Placa N`).

## Architecture (non-obvious)
- `PAGE` is one large `r"""..."""` HTML+JS string. Python pushes data with `post_message`; JS requests it with `post_message({"type":"get_state"})`. All UI work happens inside that string.
- Language preference is persisted globally in a stable `plugin_data/calculadora_tiempo/settings.json` (`{"version":1,"language":"es|en"}`), with a backup copy in the version-specific storage folder. On load the newest valid copy wins; legacy settings are migrated. `_current_language()` does not cache the default when `orca.host` is not ready yet, so an early `get_name()` cannot lock the locale. `set_language` saves atomically to both paths and rescans. The UI applies the language immediately and uses `state.language` as the authoritative value.
- `TimeCalculatorPage._scan()` is the primary path: it builds one card per live plate from `_live_plates()` and attaches the exact `.gcode` captured by `GCodeExportStarted`/`GCodeExportFinished` when that plate was sliced. It also reads `gcode_file` paths from the live 3MF and probes exact sibling paths (`.<<pid>>.<<index>>.gcode`) without listing folders, because Orca may emit the export event only for the active plate. Unsliced plates remain in the list with `duration_seconds=None` and increment `unsliced_count`. Filename `.<<pid>>.<<index>>.gcode` is 0-based; labels are `index + 1`.
- `_live_plates()` exports the **live** project (unsaved changes included) with `orca.host.plater().export_3mf_copy()` to a stable file in plugin storage, then reads `plater_id`/`plater_name` from `Metadata/model_settings.config`. `_scan()` filters G-code to those plate indices; this is what prevents old G-code files from deleted plates from showing as extra plates. The export is cached (60s normally, 2s for an explicit refresh) and invalidated on project/plate/slice events. `_LIVE_EXPORTING` ignores lifecycle events fired by the export itself, otherwise that loop keeps exporting and freezes the clock/UI. If export fails, fall back to the origin 3MF and all session files. The export may prompt for filesystem write permission once.
- `_SCANNING` guards re-entrant `_scan()` calls and returns an "Actualizando…" note; the explicit `get_state` refresh passes `force_live=True`.
- If the live project has zero plates, `_scan()` returns "La placa está vacía…" before touching `%TEMP%`, so an empty plate does not trigger repeated permission prompts.
- `GCodeExportStarted`/`GCodeExportFinished` carry the concrete G-code path in `ctx.msg`; `_record_gcode_path()` stores one latest path per plate index in `_CURRENT_GCODE_PATHS` and persists them per project in `plugin_data/calculadora_tiempo/gcode_paths.json`. `SliceStarted` no longer clears previous plates; `ProjectOpened` reloads the project's saved paths. `_scan()` reads only those exact files; it never lists `Metadata` or enumerates `%TEMP%`. Without captured paths it returns "Lamina la pieza…" only when there is no live plate; otherwise it shows every live plate. `_latest_session()`/`_gcode_files()` remain test/debug-only. Plate names come from the live export. `_NO_DATA_NOTE` is cached for 30s; project/slice/plate events clear it.
- Project filtering uses the global `_CURRENT_PROJECT` from `ProjectOpened` (`ctx.name`) and compares it with `origin.txt`; `Untitled`/empty project names are wildcards. If a named project has no matching session, return the no-match note; do not fall back to another project's latest session.
- Plate display names come from the live export (`plater_name`), mapped by plate index. Python sends an empty name when there is no custom name; JS renders the localized fallback (`Placa N` / `Plate N`). Use `html.unescape`.
- Statistics are at the **end** of the G-code (after `; CONFIG_BLOCK_END`), not the header. Use `_read_tail` (~128 KB); reading the head finds nothing. `_metrics_for()` caches parsed metrics by `(path, mtime_ns, size)`.
- Totals are the sum of plates. Two UI modes (`MODE`): `"seq"` shows the main finish as `now + total` and each card as `now + cumulative durations` in plate order; `"ind"` starts every plate at `now` (card = `now + own duration`, main finish = `now + longest plate`). Default is `"ind"`. `setMode()` toggles the buttons and re-ticks; it also runs once at startup. Mode is a user preference: `applyState()` never changes it.
- `SliceTimeCapture` was intentionally removed. The "Tiempo" page is the only capability and works on a plain Slice; it does not depend on the experimental `slicing_pipeline_plugin`.
- `get_icon()` uses `3.png` next to the script when developing, otherwise writes the embedded `_ICON_B64` to `orca.host.plugin.storage()/time_icon.png`. Keep the embedded copy in sync with `3.png` when the icon changes; single-file `.py` installs do not copy sibling assets.
- Lifecycle handling: `SliceStarted` resets to "Laminando…"; `SlicingJobComplete` ignores errors/cancellation with a reset note, otherwise rescans; `ProjectOpened` sets `_CURRENT_PROJECT` and rescans; `NewProject`/`ProjectClosed` clear it and reset.
- Plate edits invalidate the cached G-code view: `PlateCreated`/`PlateDeleted` and object add/delete/transform/change/rename show `_stale_note()` until the next Slice. `PlateRenamed` instead updates `_LIVE_PLATE_NAMES[index]` and rescans immediately; names are cleared on project/slice changes. `_scan()` returns the stale note while `_STALE` is true.
- `_temp_root()` checks `TEMP`, `TMP`, `TMPDIR`, then `tempfile.gettempdir()` because sandboxes use a different temp root.
- `orca.host` is read-only and exposes no time stats; parsing G-code is mandatory.
- Shared state is module-level: `_CURRENT_PROJECT`, `_NAME_CACHE` (3MF names), `_TAIL_CACHE` (parsed metrics).

## Conventions / gotchas
- UI strings are localized (`es`/`en`) through `_STRINGS`; keep both tables in sync and keep the file UTF-8. `_render_page()` injects the table into `PAGE`.
- The duration inputs are intentionally `readonly`; plates render as kanban cards.
- Duration formats handled: `; total estimated time:`, `; model printing time:`, `; estimated printing time (normal mode) =`, generic `; estimated printing time...=`, `; TIME: <sec>`, `; print time:`, plus `1:23:45` and `2d3h15m` via `_parse_duration`.
- Filament/cost regexes prefer `total ...` lines and support multiextruder comma-separated values via `_sum_floats`.
- `_request_read()` asks for `fs_read` on each exact `.gcode` path as it is captured or loaded; cloud/local installs start with empty permissions, so this prompt is required. The plugin never requests a directory-tree permission; do not reintroduce `%TEMP%` traversal or folder listings.
- Reset/error messages are pushed as `{"type":"state","reset":true,"note":...}`; JS `resetState()` clears duration, KPIs, hero, tag and plate cards before rendering.
