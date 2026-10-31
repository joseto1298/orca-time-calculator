# /// script
# requires-python = ">=3.9"
# dependencies = []
#
# [tool.orcaslicer.plugin]
# name = "Hora de Finalización"
# version = "0.8.0"
# description = "Muestra la hora actual y, usando la estimación del laminado, cuándo terminará la impresión."
# author = "joseto1298"
# ///

import base64
import html
import json
import os
import re
import tempfile
import time
import zipfile

import orca

_DEFAULT_LANGUAGE = "es"
_SUPPORTED_LANGUAGES = ("es", "en")
_LANGUAGE = None
_SETTINGS_FILE = "settings.json"
_CURRENT_PROJECT = None
_CURRENT_SESSION = None
_CURRENT_GCODE_PATHS = []
_LIVE_PLATE_NAMES = {}
_LIVE_PLATES = None
_LIVE_PLATES_AT = 0.0
_LIVE_EXPORTING = False
_STALE = False
_NAME_CACHE = {}
_TAIL_CACHE = {}
_SCANNING = False
_NO_DATA_NOTE = None
_NO_DATA_AT = 0.0
_NO_DATA_TTL = 30.0
_ICON_PATH = None

_STRINGS = {
    "es": {
        "tab.name": "Tiempo",
        "ui.title": "Hora de Finalización",
        "ui.subtitle": "Hora actual y estimación de cuándo termina la impresión.",
        "ui.current_time": "Hora actual",
        "ui.finish_at": "Terminará a las",
        "ui.mode_seq": "Secuencial",
        "ui.mode_ind": "Independiente",
        "ui.mode_seq_hint": "Secuencial: cada placa empieza al terminar la anterior.",
        "ui.mode_ind_hint": "Independiente: cada placa empieza ahora, por separado.",
        "ui.no_data": "sin datos de laminado",
        "ui.print_data": "Datos del laminado",
        "ui.estimated_duration": "Duración estimada",
        "ui.duration_placeholder": "p. ej. 5h 23m 12s",
        "ui.filament": "Filamento",
        "ui.weight": "Peso",
        "ui.cost": "Coste",
        "ui.diag_initial": "Lamina la pieza y pulsa Refrescar. Usaré el G-code exacto de ese laminado.",
        "ui.refresh": "Refrescar",
        "ui.loading": "Cargando datos",
        "ui.plates": "Placas",
        "ui.plate_finish": "Termina",
        "ui.max_per_plate": "Máx. por placa · {value}",
        "ui.total": "Total · {value}",
        "ui.capture_ok": "Captura OK · fuente: {source}",
        "ui.unknown": "desconocida",
        "ui.plate_fallback": "Placa {n}",
        "ui.language": "Idioma",
        "ui.language_save_failed": "No se pudo guardar el idioma. Se mantiene el anterior.",
        "note.updating": "Actualizando…",
        "note.empty_plate": "La placa está vacía. Añade una pieza y lamina.",
        "note.slice_first": "Lamina la pieza para localizar su G-code; después pulsa Refrescar.",
        "note.no_valid_plates": "La carpeta de G-code no contiene placas válidas.",
        "note.no_plate_time": "Ninguna placa tiene tiempo en el G-code.",
        "note.scan_error": "Error leyendo la caché de OrcaSlicer: {error}",
        "note.slice_failed": "El laminado falló: {detail}",
        "note.slice_failed_detail": "sin detalle",
        "note.slice_cancelled": "Laminado cancelado.",
        "note.open_project": "Abre o lamina un proyecto para ver la estimación.",
        "note.slicing": "Laminando…",
        "note.stale": "Las placas cambiaron. Lamina de nuevo para actualizar los tiempos.",
        "source.total_estimated": "tiempo total estimado",
        "source.estimated_normal": "tiempo estimado (modo normal)",
        "source.model_printing": "tiempo de impresión del modelo",
        "source.estimated_printing": "tiempo de impresión estimado",
        "source.time_seconds": "TIME (segundos)",
        "source.print_time": "tiempo de impresión",
        "source.sum_of_plates": "suma de {n} placas",
        "source.sum_of_plates_one": "suma de 1 placa",
        "source.unknown": "desconocida",
    },
    "en": {
        "tab.name": "Time",
        "ui.title": "Finish Time",
        "ui.subtitle": "Current time and estimated print finish.",
        "ui.current_time": "Current time",
        "ui.finish_at": "Will finish at",
        "ui.mode_seq": "Sequential",
        "ui.mode_ind": "Independent",
        "ui.mode_seq_hint": "Sequential: each plate starts when the previous one ends.",
        "ui.mode_ind_hint": "Independent: each plate starts now, separately.",
        "ui.no_data": "no slice data",
        "ui.print_data": "Slice data",
        "ui.estimated_duration": "Estimated duration",
        "ui.duration_placeholder": "e.g. 5h 23m 12s",
        "ui.filament": "Filament",
        "ui.weight": "Weight",
        "ui.cost": "Cost",
        "ui.diag_initial": "Slice the model and press Refresh. I'll use the exact G-code from that slice.",
        "ui.refresh": "Refresh",
        "ui.loading": "Loading data",
        "ui.plates": "Plates",
        "ui.plate_finish": "Finishes",
        "ui.max_per_plate": "Max per plate · {value}",
        "ui.total": "Total · {value}",
        "ui.capture_ok": "Capture OK · source: {source}",
        "ui.unknown": "unknown",
        "ui.plate_fallback": "Plate {n}",
        "ui.language": "Language",
        "ui.language_save_failed": "Could not save the language. Keeping the previous one.",
        "note.updating": "Updating…",
        "note.empty_plate": "The plate is empty. Add a model and slice.",
        "note.slice_first": "Slice the model to locate its G-code, then press Refresh.",
        "note.no_valid_plates": "The G-code folder has no valid plates.",
        "note.no_plate_time": "No plate has a time in the G-code.",
        "note.scan_error": "Error reading the OrcaSlicer cache: {error}",
        "note.slice_failed": "Slicing failed: {detail}",
        "note.slice_failed_detail": "no details",
        "note.slice_cancelled": "Slicing cancelled.",
        "note.open_project": "Open or slice a project to see the estimate.",
        "note.slicing": "Slicing…",
        "note.stale": "Plates changed. Slice again to update the times.",
        "source.total_estimated": "total estimated time",
        "source.estimated_normal": "estimated printing time (normal)",
        "source.model_printing": "model printing time",
        "source.estimated_printing": "estimated printing time",
        "source.time_seconds": "TIME (seconds)",
        "source.print_time": "print time",
        "source.sum_of_plates": "sum of {n} plates",
        "source.sum_of_plates_one": "sum of 1 plate",
        "source.unknown": "unknown",
    },
}

_ICON_B64 = "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"


def _plugin_storage():
    folder = str(orca.host.plugin.storage())
    os.makedirs(folder, exist_ok=True)
    return folder


def _read_settings():
    try:
        path = os.path.join(_plugin_storage(), _SETTINGS_FILE)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _current_language():
    global _LANGUAGE
    if _LANGUAGE in _SUPPORTED_LANGUAGES:
        return _LANGUAGE
    saved = _read_settings().get("language")
    _LANGUAGE = saved if saved in _SUPPORTED_LANGUAGES else _DEFAULT_LANGUAGE
    return _LANGUAGE


def _write_language(lang):
    path = os.path.join(_plugin_storage(), _SETTINGS_FILE)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "language": lang}, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
        return True
    except Exception as exc:
        print("[time-calc] no pude guardar el idioma: %s" % exc)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


def _set_language(lang):
    global _LANGUAGE
    if lang not in _SUPPORTED_LANGUAGES:
        return False
    if not _write_language(lang):
        return False
    _LANGUAGE = lang
    return True


def _t(key, **params):
    table = _STRINGS.get(_current_language(), {})
    text = table.get(key)
    if text is None:
        text = _STRINGS[_DEFAULT_LANGUAGE].get(key, key)
    if params:
        try:
            text = text.format(**params)
        except (KeyError, ValueError):
            pass
    return text


def _tn(one_key, many_key, n):
    return _t(one_key if n == 1 else many_key, n=n)


def _source_label(key):
    if not key:
        return _t("source.unknown")
    label = _t("source." + key)
    return label if label != "source." + key else key


def _stale_note():
    return _t("note.stale")


def _icon_path():
    global _ICON_PATH
    if _ICON_PATH and os.path.isfile(_ICON_PATH):
        return _ICON_PATH
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "3.png")
    if os.path.isfile(here):
        _ICON_PATH = here
        return here
    try:
        folder = str(orca.host.plugin.storage())
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "time_icon.png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(_ICON_B64))
        _ICON_PATH = path
        return path
    except Exception:
        _ICON_PATH = ""
        return ""


def _parse_duration(text):
    """Acepta '2h 8m 6s', '2d3h15m', '45s', '01:23:45'."""
    text = (text or "").strip()
    if not text:
        return None
    m = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", text)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    total = 0.0
    found = False
    for num, unit in re.findall(r"([\d.]+)\s*([dhms])", text.lower()):
        found = True
        total += float(num) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[unit]
    return total if found else None


def _sum_floats(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if not m:
            continue
        values = []
        for part in m.group(1).split(","):
            try:
                values.append(float(part.strip()))
            except ValueError:
                pass
        if values:
            return sum(values)
    return None


def _extract_metrics(text):
    """Devuelve (segundos, fuente). Cubre formatos Bambu y no-Bambu."""
    seconds = None
    source = None

    # Bambu Lab: total estimated time (incluye preparación) es lo más útil.
    m = re.search(r";\s*total estimated time:\s*([^;\n]+)", text, re.I)
    if m:
        seconds, source = _parse_duration(m.group(1)), "total_estimated"

    if seconds is None:
        m = re.search(
            r";\s*estimated printing time \(normal mode\)\s*=\s*([^\n]+)", text, re.I
        )
        if m:
            seconds, source = _parse_duration(m.group(1)), "estimated_normal"

    if seconds is None:
        m = re.search(r";\s*model printing time:\s*([^;\n]+)", text, re.I)
        if m:
            seconds, source = _parse_duration(m.group(1)), "model_printing"

    if seconds is None:
        m = re.search(r";\s*estimated printing time[^\n=]*=\s*([^\n]+)", text, re.I)
        if m:
            seconds, source = _parse_duration(m.group(1)), "estimated_printing"

    if seconds is None:
        m = re.search(r";\s*TIME:\s*([\d.]+)", text, re.I)
        if m:
            seconds, source = float(m.group(1)), "time_seconds"

    if seconds is None:
        m = re.search(r";\s*print time:\s*([^\n;]+)", text, re.I)
        if m:
            seconds, source = _parse_duration(m.group(1)), "print_time"

    return seconds, source


def _read_tail(path, nbytes=131072):
    """Lee el final del G-code, donde OrcaSlicer pone las estadísticas."""
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - nbytes))
        data = f.read()
    return data.decode("utf-8", "replace")


def _temp_root():
    bases = []
    for key in ("TEMP", "TMP", "TMPDIR"):
        value = os.environ.get(key)
        if value:
            bases.append(value)
    try:
        bases.append(tempfile.gettempdir())
    except Exception:
        pass
    seen = set()
    for base in bases:
        base = os.path.abspath(base)
        if base in seen:
            continue
        seen.add(base)
        candidate = os.path.join(base, "orcaslicer_model")
        if os.path.isdir(candidate):
            return candidate
    return None


def _dirs(path):
    found = []
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_dir():
                        found.append((entry.name, entry.stat().st_mtime))
                except OSError:
                    continue
    except OSError:
        return []
    return found


def _read_origin(session):
    try:
        with open(
            os.path.join(session, "origin.txt"),
            "r",
            encoding="utf-8-sig",
            errors="replace",
        ) as f:
            return f.read().strip()
    except OSError:
        return ""


_MODEL_EXTENSIONS = {
    ".3mf", ".stl", ".obj", ".amf", ".step", ".stp", ".ply",
    ".dae", ".gltf", ".glb", ".3ds", ".svg", ".dxf",
}


def _project_stem(value):
    if not value:
        return ""
    base = os.path.basename(str(value).replace("\\", "/")).strip()
    if base.lower().endswith(".3mf"):
        base = base[:-4]
    return base.strip().lower()


def _project_matches(origin, project):
    want = _project_stem(project)
    if not want or want.startswith("untitled") or want in ("sin título", "sin titulo"):
        return True
    got = _project_stem(origin)
    if got == want:
        return True
    stem, ext = os.path.splitext(got)
    return ext in _MODEL_EXTENSIONS and stem == want


def _gcode_files(folder):
    try:
        names = [n for n in os.listdir(folder) if n.lower().endswith(".gcode")]
    except OSError:
        return []
    indexed = []
    others = []
    for name in names:
        match = re.search(r"\.(\d+)\.gcode$", name, re.I)
        if match:
            indexed.append((int(match.group(1)), name))
        else:
            others.append(name)
    if indexed:
        indexed.sort(key=lambda item: (item[0], item[1]))
        return [(index, name) for index, name in indexed]
    others.sort()
    return [(None, name) for name in others]


def _record_gcode_path(path):
    global _CURRENT_SESSION
    if not path:
        return
    full = os.path.abspath(str(path))
    metadata = os.path.dirname(full)
    if os.path.basename(metadata).lower() != "metadata":
        return
    if not os.path.isfile(full):
        return
    if full not in _CURRENT_GCODE_PATHS:
        _CURRENT_GCODE_PATHS.append(full)
        _CURRENT_GCODE_PATHS.sort()
    _CURRENT_SESSION = os.path.dirname(metadata)


def _session_from_gcode(path):
    if not path:
        return None
    full = os.path.abspath(str(path))
    metadata = os.path.dirname(full)
    if os.path.basename(metadata).lower() != "metadata":
        return None
    session = os.path.dirname(metadata)
    if os.path.isdir(session):
        return session
    return None


def _latest_session(project=None):
    root = _temp_root()
    if not root:
        return None
    days = _dirs(root)
    days.sort(key=lambda item: (item[1], item[0]), reverse=True)
    for day_name, _mtime in days[:1]:
        day_path = os.path.join(root, day_name)
        sessions = _dirs(day_path)
        sessions.sort(key=lambda item: item[0], reverse=True)
        for session_name, _ in sessions[:3]:
            session = os.path.join(day_path, session_name)
            metadata = os.path.join(session, "Metadata")
            if not _gcode_files(metadata):
                continue
            if project:
                origin = _read_origin(session)
                if not origin or not _project_matches(origin, project):
                    return None
            return session
    return None


def _plate_data_from_3mf(path):
    """Placas reales del 3MF: {count, indices, names, ordered}."""
    try:
        stat = os.stat(path)
        key = (path, stat.st_mtime_ns, stat.st_size)
    except OSError:
        key = (path, None, None)
    cached = _NAME_CACHE.get(key)
    if cached is not None:
        return dict(cached)
    try:
        with zipfile.ZipFile(path) as zf:
            config = zf.read("Metadata/model_settings.config").decode("utf-8", "replace")
    except Exception:
        return {}
    blocks = re.findall(r"<plate>(.*?)</plate>", config, re.S | re.I)
    if not blocks:
        data = {"count": 0, "indices": [], "names": {}, "ordered": []}
        _NAME_CACHE[key] = dict(data)
        return data
    indices = []
    names = {}
    ordered = []
    for ordinal, block in enumerate(blocks):
        meta = dict(re.findall(r'key="([^"]+)"\s+value="([^"]*)"', block, re.I))
        name = html.unescape(meta.get("plater_name", "")).strip()
        try:
            index = int(meta.get("plater_id", "")) - 1
        except (TypeError, ValueError):
            index = ordinal
        if index < 0:
            index = ordinal
        indices.append(index)
        ordered.append(name)
        if name:
            names[index] = name
    data = {
        "count": len(blocks),
        "indices": sorted(set(indices)),
        "names": names,
        "ordered": ordered,
    }
    _NAME_CACHE[key] = dict(data)
    return data


def _live_project_path():
    try:
        host = orca.host
        path = host.plater().project_path()
        return str(path) if path else None
    except Exception:
        return None


def _set_no_data(note):
    global _NO_DATA_NOTE, _NO_DATA_AT
    _NO_DATA_NOTE = note
    _NO_DATA_AT = time.time()


def _clear_no_data():
    global _NO_DATA_NOTE, _NO_DATA_AT
    _NO_DATA_NOTE = None
    _NO_DATA_AT = 0.0


def _forget_live_plates():
    global _LIVE_PLATES, _LIVE_PLATES_AT
    _LIVE_PLATES = None
    _LIVE_PLATES_AT = 0.0


def _live_plates(force=False):
    """Exporta el proyecto vivo, con cambios sin guardar, y lee sus placas."""
    global _LIVE_PLATES, _LIVE_PLATES_AT, _LIVE_EXPORTING
    now = time.time()
    if _LIVE_PLATES is not None:
        max_age = 2 if force else 60
        if now - _LIVE_PLATES_AT < max_age:
            return _LIVE_PLATES
    if _LIVE_EXPORTING:
        return _LIVE_PLATES
    host = getattr(orca, "host", None)
    if host is None or not hasattr(host, "plater"):
        return _LIVE_PLATES
    _LIVE_EXPORTING = True
    folder = None
    temporary = False
    path = None
    try:
        try:
            folder = str(orca.host.plugin.storage())
        except Exception:
            folder = tempfile.mkdtemp(prefix="orca_time_")
            temporary = True
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "live_plates.3mf")
        host.plater().export_3mf_copy(path)
        data = _plate_data_from_3mf(path)
        if data:
            _LIVE_PLATES = data
            _LIVE_PLATES_AT = now
            return data
        return _LIVE_PLATES
    except Exception as exc:
        print("[time-calc] no pude leer las placas vivas: %s" % exc)
        return _LIVE_PLATES
    finally:
        _LIVE_EXPORTING = False
        if path:
            try:
                os.remove(path)
            except OSError:
                pass
        if temporary and folder:
            try:
                os.rmdir(folder)
            except OSError:
                pass


def _plater_names(session_dir):
    """Nombres de placa del 3MF de origen, por orden: {orden: nombre}."""
    origin = _read_origin(session_dir)
    if not origin or not os.path.isfile(origin):
        return {}
    data = _plate_data_from_3mf(origin)
    names = {}
    for ordinal, name in enumerate(data.get("ordered", [])):
        if name:
            names[ordinal] = name
    return names


def _metrics_from_text(text):
    seconds, source = _extract_metrics(text)
    filament_mm = _sum_floats(
        [
            r";\s*total filament length \[mm\]\s*=\s*([^\n;]+)",
            r";\s*filament used \[mm\]\s*=\s*([^\n;]+)",
        ],
        text,
    )
    filament_g = _sum_floats(
        [
            r";\s*total filament weight \[g\]\s*=\s*([^\n;]+)",
            r";\s*total filament used \[g\]\s*=\s*([^\n;]+)",
            r";\s*filament used \[g\]\s*=\s*([^\n;]+)",
        ],
        text,
    )
    cost = _sum_floats(
        [
            r";\s*total cost\s*=\s*([^\n;]+)",
            r";\s*total filament cost\s*=\s*([^\n;]+)",
            r";\s*filament cost\s*=\s*([^\n;]+)",
        ],
        text,
    )
    return seconds, source, filament_mm, filament_g, cost


def _metrics_for(path):
    try:
        stat = os.stat(path)
        key = (path, stat.st_mtime_ns, stat.st_size)
    except OSError:
        key = (path, None, None)
    cached = _TAIL_CACHE.get(key)
    if cached is not None:
        return cached
    metrics = _metrics_from_text(_read_tail(path))
    _TAIL_CACHE[key] = metrics
    return metrics


PAGE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #26292e; --panel: #2e3238; --panel2: #343941; --border: #41464e;
    --text: #e8eaed; --muted: #9aa0a6; --accent: #f28c38; --warn: #e0a44c; --ok: #5fb96a;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 16px;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.45;
  }
  h1 { font-size: 16px; margin: 0 0 4px; font-weight: 600; }
  .sub { color: var(--muted); font-size: 12px; margin-bottom: 16px; }
  .topbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
  .topbar .sub { margin-bottom: 16px; }
  .lang-wrap { flex: 0 0 auto; }
  .lang-wrap select { min-width: 110px; }
  .lang-error { color: var(--warn); font-size: 11px; margin-top: 6px; }
  .hero {
    background: linear-gradient(180deg, #32363d 0%, #2b2f35 100%);
    border: 1px solid var(--border); border-radius: 10px;
    padding: 20px; text-align: center; margin-bottom: 14px;
  }
  .hero .label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }
  .hero .now { font-size: 42px; font-weight: 700; letter-spacing: 1px;
    font-variant-numeric: tabular-nums; margin: 4px 0 2px; }
  .hero .now .sec { font-size: 20px; color: var(--muted); }
  .hero .finish { font-size: 30px; font-weight: 700; margin: 10px 0 2px; }
  .hero .finish em { font-style: normal; color: var(--accent); }
  .hero .day { color: var(--muted); font-size: 14px; margin-top: 2px; }
  .hero .dur { display: inline-block; margin-top: 8px; padding: 4px 12px; border-radius: 999px;
    background: rgba(242,140,56,.14); color: var(--accent); font-weight: 600; font-size: 13px; }
  .modes { display: inline-flex; gap: 6px; margin-top: 12px; }
  .mode-btn { padding: 6px 12px; font-size: 12px; border-radius: 999px; }
  .mode-btn.active { background: var(--accent); color: #1b1d20; border-color: var(--accent); }
  .mode-hint { color: var(--muted); font-size: 11px; margin-top: 6px; }
  .card { background: var(--panel); border: 1px solid var(--border);
    border-radius: 8px; padding: 14px; margin-bottom: 14px; }
  .card h2 { font-size: 13px; margin: 0 0 10px; font-weight: 600;
    color: var(--muted); text-transform: uppercase; letter-spacing: .4px; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field label { font-size: 12px; color: var(--muted); }
  input, button, select { background: var(--panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 8px 10px; font-size: 14px; font-family: inherit; }
  select:disabled { opacity: .6; cursor: wait; }
  input:focus { outline: none; border-color: var(--accent); }
  button { cursor: pointer; border: none; background: var(--accent); color: #1b1d20; font-weight: 600; }
  button.ghost { background: var(--panel2); color: var(--text); border: 1px solid var(--border); }
  button:hover { filter: brightness(1.08); }
  .kpis { display: flex; gap: 12px; flex-wrap: wrap; }
  .kpi { flex: 1 1 110px; background: var(--panel2); border-radius: 6px; padding: 10px; }
  .kpi .k { color: var(--muted); font-size: 11px; }
  .kpi .v { font-size: 17px; font-weight: 600; margin-top: 2px; }
  .diag { font-size: 12px; padding: 8px 10px; border-radius: 6px; margin-top: 10px; }
  .diag.ok { background: rgba(95,185,106,.14); color: var(--ok); }
  .diag.warn { background: rgba(224,164,76,.14); color: var(--warn); }
  .muted { color: var(--muted); }
  .mono { font-family: Consolas, monospace; font-size: 11px; word-break: break-word; }
  .kanban { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; }
  .plate-card { background: var(--panel2); border: 1px solid var(--border); border-radius: 8px;
    padding: 12px; display: flex; flex-direction: column; }
  .pc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
  .pc-num { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px;
    border-radius: 50%; background: var(--accent); color: #1b1d20; font-weight: 700; font-size: 12px; }
  .pc-name { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pc-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .4px; }
  .pc-finish { font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; }
  .pc-date { color: var(--muted); font-size: 12px; margin-bottom: 8px; }
  .pc-dur { width: 100%; margin-top: 2px; }
  input[readonly] { opacity: .85; }
  .pc-meta { color: var(--muted); margin-top: 6px; }
  .loading-row { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
  .spinner { width: 16px; height: 16px; border-radius: 50%;
    border: 2px solid var(--border); border-top-color: var(--accent);
    animation: spin .7s linear infinite; }
  .spinner[hidden] { display: none; }
  @keyframes spin { to { transform: rotate(360deg); } }
  button:disabled { opacity: .6; cursor: wait; }
</style>
</head>
<body>
  <div class="topbar">
    <div>
      <h1 data-i18n="ui.title">Hora de Finalización</h1>
      <div class="sub" data-i18n="ui.subtitle">Hora actual y estimación de cuándo termina la impresión.</div>
    </div>
    <div class="lang-wrap">
      <select id="lang" data-i18n-aria-label="ui.language" aria-label="Idioma">
        <option value="es">Español</option>
        <option value="en">English</option>
      </select>
      <div class="lang-error" id="langError" hidden></div>
    </div>
  </div>

  <div class="hero">
    <div class="label" data-i18n="ui.current_time">Hora actual</div>
    <div class="now" id="nowClock">--:--:--</div>
    <div class="label" style="margin-top:14px;" data-i18n="ui.finish_at">Terminará a las</div>
    <div class="finish"><em id="finishClock">--:--</em></div>
    <div class="day" id="finishDay"></div>
    <div class="modes">
      <button class="mode-btn ghost" id="modeSeq" data-i18n="ui.mode_seq">Secuencial</button>
      <button class="mode-btn ghost active" id="modeInd" data-i18n="ui.mode_ind">Independiente</button>
    </div>
    <div class="mode-hint" id="modeHint">Independiente: cada placa empieza ahora, por separado.</div>
    <div class="dur" id="durTag" data-i18n="ui.no_data">sin datos de laminado</div>
  </div>

  <div class="card">
    <h2 data-i18n="ui.print_data">Datos del laminado</h2>
    <div class="field" style="margin-bottom:10px;">
      <label for="dur" data-i18n="ui.estimated_duration">Duración estimada</label>
      <input id="dur" data-i18n-placeholder="ui.duration_placeholder" placeholder="p. ej. 5h 23m 12s" readonly>
    </div>
    <div class="kpis">
      <div class="kpi"><div class="k" data-i18n="ui.filament">Filamento</div><div class="v" id="printFil">—</div></div>
      <div class="kpi"><div class="k" data-i18n="ui.weight">Peso</div><div class="v" id="printWeight">—</div></div>
      <div class="kpi"><div class="k" data-i18n="ui.cost">Coste</div><div class="v" id="printCost">—</div></div>
    </div>
    <div class="diag warn" id="diag">Lamina la pieza y pulsa Refrescar. Usaré el G-code exacto de ese laminado.</div>
    <div class="loading-row">
      <button class="ghost" id="refreshBtn" data-i18n="ui.refresh">Refrescar</button>
      <span class="spinner" id="loading" role="status" data-i18n-aria-label="ui.loading" aria-label="Cargando datos" hidden></span>
    </div>
  </div>

  <div class="card" id="platesCard" style="display:none;">
    <h2 data-i18n="ui.plates">Placas</h2>
    <div id="platesList" class="kanban"></div>
  </div>

<script>
(function () {
  var bridge = window.orca || (typeof orca !== "undefined" ? orca : null);
  var I18N = __I18N__;
  var LANG = "__LANG__";
  var loadingTimer = null;

  function t(key, vars) {
    var table = I18N[LANG] || I18N.es || {};
    var text = table[key];
    if (text === undefined) text = (I18N.es || {})[key] || key;
    if (vars) {
      for (var name in vars) {
        if (Object.prototype.hasOwnProperty.call(vars, name)) {
          text = text.split("{" + name + "}").join(String(vars[name]));
        }
      }
    }
    return text;
  }

  function applyI18n() {
    if (document.documentElement) document.documentElement.lang = LANG;
    var nodes = document.querySelectorAll("[data-i18n]");
    for (var i = 0; i < nodes.length; i++) {
      var key = nodes[i].getAttribute("data-i18n");
      if (key) nodes[i].textContent = t(key);
    }
    var placeholders = document.querySelectorAll("[data-i18n-placeholder]");
    for (var j = 0; j < placeholders.length; j++) {
      var pkey = placeholders[j].getAttribute("data-i18n-placeholder");
      if (pkey) placeholders[j].setAttribute("placeholder", t(pkey));
    }
    var aria = document.querySelectorAll("[data-i18n-aria-label]");
    for (var k = 0; k < aria.length; k++) {
      var akey = aria[k].getAttribute("data-i18n-aria-label");
      if (akey) aria[k].setAttribute("aria-label", t(akey));
    }
    var select = document.getElementById("lang");
    if (select) select.value = LANG;
    var error = document.getElementById("langError");
    if (error && !error.hidden) error.textContent = t("ui.language_save_failed");
  }

  function setLoading(on) {
    var spinner = document.getElementById("loading");
    var button = document.getElementById("refreshBtn");
    var select = document.getElementById("lang");
    if (loadingTimer && typeof clearTimeout === "function") {
      clearTimeout(loadingTimer);
    }
    loadingTimer = null;
    if (spinner) spinner.hidden = !on;
    if (button) button.disabled = !!on;
    if (select) select.disabled = !!on;
    if (on && typeof setTimeout === "function") {
      loadingTimer = setTimeout(function () { setLoading(false); }, 20000);
    }
  }
  var DURATION_SECONDS = null;
  var PLATES = [];
  var MODE = "ind";

  function fmtDur(s) {
    if (s === null || s === undefined || isNaN(s)) return "—";
    s = Math.max(0, Math.round(s));
    var d = Math.floor(s / 86400);
    var h = Math.floor(s / 3600) % 24;
    var m = Math.floor(s / 60) % 60;
    var sec = s % 60;
    var out = [];
    if (d) out.push(d + "d");
    if (h || d) out.push(h + "h");
    if (m || h || d) out.push(m + "m");
    out.push(sec + "s");
    return out.join(" ");
  }

  function parseDuration(raw) {
    if (!raw) return null;
    var re = /(\d+(?:\.\d+)?)\s*(d|h|m|s)/g;
    var total = 0, found = false, m;
    var mult = { d: 86400, h: 3600, m: 60, s: 1 };
    while ((m = re.exec(raw.toLowerCase())) !== null) {
      total += parseFloat(m[1]) * mult[m[2]];
      found = true;
    }
    if (!found) {
      var n = parseFloat(raw.replace(",", "."));
      if (!isNaN(n)) total = n * 60;
    }
    return total;
  }

  function two(n) { return (n < 10 ? "0" : "") + n; }

  function esc(s) {
    return String(s === null || s === undefined ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function fullDate(d) {
    if (LANG === "en") {
      return two(d.getMonth() + 1) + "/" + two(d.getDate()) + "/" + d.getFullYear();
    }
    return two(d.getDate()) + "/" + two(d.getMonth() + 1) + "/" + d.getFullYear();
  }

  function tick() {
    var now = new Date();
    document.getElementById("nowClock").innerHTML =
      two(now.getHours()) + ":" + two(now.getMinutes()) + ":" +
      "<span class='sec'>" + two(now.getSeconds()) + "</span>";

    updatePlateFinishes(now);

    var dur = parseDuration(document.getElementById("dur").value);
    var finishEl = document.getElementById("finishClock");
    var dayEl = document.getElementById("finishDay");
    var tagEl = document.getElementById("durTag");

    var horizon = dur;
    if (MODE === "ind") {
      var maxd = 0;
      for (var i = 0; i < PLATES.length; i++) {
        var d = PLATES[i].duration_seconds;
        if (d !== null && d !== undefined && d > maxd) maxd = d;
      }
      if (maxd > 0) horizon = maxd;
    }

    if (!horizon || horizon <= 0) {
      finishEl.textContent = "--:--";
      dayEl.textContent = "";
      tagEl.textContent = DURATION_SECONDS !== null ? fmtDur(DURATION_SECONDS) : t("ui.no_data");
      return;
    }

    tagEl.textContent = t(MODE === "ind" ? "ui.max_per_plate" : "ui.total", {
      value: fmtDur(horizon)
    });
    var finish = new Date(now.getTime() + horizon * 1000);
    finishEl.textContent = two(finish.getHours()) + ":" + two(finish.getMinutes());
    dayEl.textContent = fullDate(finish);
  }

  function setMode(mode) {
    MODE = mode;
    document.getElementById("modeSeq").classList.toggle("active", mode === "seq");
    document.getElementById("modeInd").classList.toggle("active", mode === "ind");
    document.getElementById("modeHint").textContent = t(
      mode === "seq" ? "ui.mode_seq_hint" : "ui.mode_ind_hint"
    );
    tick();
  }

  function renderPlates(state) {
    var card = document.getElementById("platesCard");
    var list = document.getElementById("platesList");
    PLATES = (state && state.plates) ? state.plates.slice() : [];
    if (!PLATES.length) {
      card.style.display = "none";
      list.innerHTML = "";
      return;
    }
    var html = "";
    for (var i = 0; i < PLATES.length; i++) {
      var p = PLATES[i];
      var num = (p.index !== null && p.index !== undefined) ? (p.index + 1) : (i + 1);
      var meta = [];
      if (p.filament_g !== null && p.filament_g !== undefined) meta.push(p.filament_g.toFixed(1) + " g");
      if (p.cost !== null && p.cost !== undefined) meta.push(parseFloat(p.cost).toFixed(2));
      var displayName = p.name || p.file || t("ui.plate_fallback", { n: num });
      var title = esc(displayName);
      html +=
        "<div class='plate-card'>" +
          "<div class='pc-head'><span class='pc-num'>" + num + "</span>" +
            "<span class='pc-name' title='" + title + "'>" + title + "</span></div>" +
          "<div class='pc-label' style='margin-top:2px;'>" + esc(t("ui.plate_finish")) + "</div>" +
          "<div class='pc-finish'>--:--</div>" +
          "<div class='pc-date'></div>" +
          "<label class='pc-label' style='margin-top:8px;'>" + esc(t("ui.estimated_duration")) + "</label>" +
          "<input class='pc-dur' readonly value='" +
            (p.duration_seconds !== null && p.duration_seconds !== undefined ? fmtDur(p.duration_seconds) : "—") +
          "'>" +
          (meta.length ? "<div class='pc-meta mono'>" + meta.join(" · ") + "</div>" : "") +
        "</div>";
    }
    list.innerHTML = html;
    card.style.display = "";
    updatePlateFinishes(new Date());
  }

  function updatePlateFinishes(now) {
    if (!PLATES.length) return;
    var finishes = document.querySelectorAll(".pc-finish");
    var dates = document.querySelectorAll(".pc-date");
    var cumulative = 0;
    for (var i = 0; i < PLATES.length; i++) {
      var d = PLATES[i].duration_seconds;
      if (d === null || d === undefined) {
        if (finishes[i]) finishes[i].textContent = "—";
        if (dates[i]) dates[i].textContent = "";
        continue;
      }
      if (MODE === "seq") cumulative += d; else cumulative = d;
      var f = new Date(now.getTime() + cumulative * 1000);
      if (finishes[i]) finishes[i].textContent = two(f.getHours()) + ":" + two(f.getMinutes());
      if (dates[i]) dates[i].textContent = fullDate(f);
    }
  }

  function resetState() {
    DURATION_SECONDS = null;
    PLATES = [];
    document.getElementById("dur").value = "";
    document.getElementById("printFil").textContent = "—";
    document.getElementById("printWeight").textContent = "—";
    document.getElementById("printCost").textContent = "—";
    document.getElementById("finishClock").textContent = "--:--";
    document.getElementById("finishDay").textContent = "";
    document.getElementById("durTag").textContent = t("ui.no_data");
    document.getElementById("platesCard").style.display = "none";
    document.getElementById("platesList").innerHTML = "";
  }

  function applyState(state) {
    setLoading(false);
    if (state && state.language && I18N[state.language] && state.language !== LANG) {
      LANG = state.language;
      applyI18n();
      setMode(MODE);
    }
    var langError = document.getElementById("langError");
    if (langError) {
      langError.hidden = !(state && state.language_saved === false);
      if (!langError.hidden) langError.textContent = t("ui.language_save_failed");
    }
    var diag = document.getElementById("diag");
    resetState();
    if (!state || state.reset) {
      diag.className = "diag warn";
      diag.textContent = (state && state.note)
        ? String(state.note)
        : t("note.slice_first");
      tick();
      return;
    }
    if (state.duration_seconds !== null && state.duration_seconds !== undefined) {
      DURATION_SECONDS = state.duration_seconds;
      document.getElementById("dur").value = fmtDur(state.duration_seconds);
      diag.className = "diag ok";
      diag.textContent = t("ui.capture_ok", {
        source: state.source || t("ui.unknown")
      });
    } else {
      diag.className = "diag warn";
      diag.textContent = state.note
        ? String(state.note)
        : t("note.no_plate_time");
    }
    document.getElementById("printFil").textContent =
      (state.filament_mm !== null && state.filament_mm !== undefined)
        ? (Math.round(state.filament_mm) + " mm") : "—";
    document.getElementById("printWeight").textContent =
      (state.filament_g !== null && state.filament_g !== undefined)
        ? (state.filament_g.toFixed(1) + " g") : "—";
    document.getElementById("printCost").textContent =
      (state.cost !== null && state.cost !== undefined)
        ? parseFloat(state.cost).toFixed(2) : "—";
    renderPlates(state);
    tick();
  }

  function setLanguage(lang) {
    if (lang !== "es" && lang !== "en") return;
    LANG = lang;
    applyI18n();
    setMode(MODE);
    tick();
    setLoading(true);
    if (bridge && bridge.postMessage) {
      bridge.postMessage({ type: "set_language", language: lang });
    }
  }

  function requestState() {
    setLoading(true);
    if (bridge && bridge.postMessage) bridge.postMessage({ type: "get_state" });
  }

  if (bridge && bridge.onMessage) {
    bridge.onMessage(function (msg) {
      if (msg && msg.type === "state") applyState(msg);
    });
  }

  document.getElementById("refreshBtn").addEventListener("click", function () {
    tick();
    requestState();
  });
  document.getElementById("modeSeq").addEventListener("click", function () { setMode("seq"); });
  document.getElementById("modeInd").addEventListener("click", function () { setMode("ind"); });
  var langSelect = document.getElementById("lang");
  if (langSelect) {
    langSelect.addEventListener("change", function () { setLanguage(langSelect.value); });
  }

  applyI18n();
  var initialDiag = document.getElementById("diag");
  if (initialDiag) initialDiag.textContent = t("ui.diag_initial");
  setMode(MODE);
  tick();
  requestState();
  setInterval(tick, 1000);
})();
</script>
</body>
</html>
"""


def _render_page():
    payload = json.dumps(_STRINGS, ensure_ascii=False).replace("</", "<\\/")
    return PAGE.replace("__I18N__", payload).replace("__LANG__", _current_language())


class TimeCalculatorPage(orca.pages.PagesPluginCapabilityBase):
    def get_name(self):
        return _t("tab.name")

    def get_ui(self):
        return _render_page()

    def get_icon(self):
        return _icon_path()

    def on_message(self, data):
        if not isinstance(data, dict):
            return
        kind = data.get("type")
        if kind == "get_state":
            self.post_message({
                "type": "state",
                "language": _current_language(),
                **self._scan(force_live=True),
            })
        elif kind == "set_language":
            lang = data.get("language")
            saved = _set_language(lang)
            if saved:
                _clear_no_data()
            self.post_message({
                "type": "state",
                "language": _current_language(),
                "language_saved": saved,
                **self._scan(force_live=True),
            })

    def _scan(self, force_live=False):
        global _SCANNING
        if _SCANNING:
            return {"note": _t("note.updating")}
        _SCANNING = True
        try:
            if _STALE:
                return {"note": _stale_note()}
            live = _live_plates(force=force_live)
            if live is not None and live.get("count") == 0:
                return {"note": _t("note.empty_plate")}
            if _NO_DATA_NOTE and time.time() - _NO_DATA_AT < _NO_DATA_TTL:
                return {"note": _NO_DATA_NOTE}
            entries = []
            for path in _CURRENT_GCODE_PATHS:
                if not os.path.isfile(path):
                    continue
                name = os.path.basename(path)
                match = re.search(r"\.(\d+)\.gcode$", name, re.I)
                index = int(match.group(1)) if match else None
                entries.append((index, name, path))
            entries.sort(key=lambda item: (item[0] is None, item[0], item[1]))
            if not entries:
                note = _t("note.slice_first")
                _set_no_data(note)
                return {"note": note}

            live_names = live.get("names", {}) if live else {}
            if live and live.get("count"):
                allowed = set(live.get("indices") or [])
                filtered = [
                    item for item in entries
                    if item[0] is None or item[0] in allowed
                ]
                if filtered:
                    entries = filtered
                elif len(entries) > live["count"]:
                    entries = entries[: live["count"]]

            plates = []
            for index, name, path in entries:
                try:
                    seconds, source, filament_mm, filament_g, cost = _metrics_for(path)
                except Exception as exc:
                    print("[time-calc] error leyendo %s: %s" % (name, exc))
                    continue
                live_name = _LIVE_PLATE_NAMES.get(index) if index is not None else None
                plates.append({
                    "index": index,
                    "name": live_name or live_names.get(index) or "",
                    "file": name,
                    "duration_seconds": seconds,
                    "filament_mm": filament_mm,
                    "filament_g": filament_g,
                    "cost": cost,
                    "source": source,
                })

            if not plates:
                note = _t("note.no_valid_plates")
                _set_no_data(note)
                return {"note": note}
            _clear_no_data()

            total_secs = total_mm = total_g = total_cost = None
            for plate in plates:
                if plate["duration_seconds"] is not None:
                    total_secs = (total_secs or 0) + plate["duration_seconds"]
                if plate["filament_mm"] is not None:
                    total_mm = (total_mm or 0) + plate["filament_mm"]
                if plate["filament_g"] is not None:
                    total_g = (total_g or 0) + plate["filament_g"]
                if plate["cost"] is not None:
                    total_cost = (total_cost or 0) + plate["cost"]

            if len(plates) > 1:
                source = _tn(
                    "source.sum_of_plates_one",
                    "source.sum_of_plates",
                    len(plates),
                )
            else:
                source = _source_label(plates[0]["source"])
            data = {
                "plates": plates,
                "plate_count": len(plates),
                "duration_seconds": total_secs,
                "filament_mm": total_mm,
                "filament_g": total_g,
                "cost": total_cost,
                "source": source,
                "note": None if total_secs is not None else _t("note.no_plate_time"),
                "ran_at": time.time(),
            }
            print("[time-calc] scan %d placas -> %s s" % (len(plates), total_secs))
            return data
        except Exception as exc:
            print("[time-calc] error en scan: %s" % exc)
            return {"note": _t("note.scan_error", error=exc)}
        finally:
            _SCANNING = False

    def on_lifecycle_event(self, event, ctx):
        global _CURRENT_PROJECT, _CURRENT_SESSION, _STALE
        if _LIVE_EXPORTING:
            return
        try:
            code = getattr(ctx, "code", None)
            msg = getattr(ctx, "msg", "") or ""
            error_code = getattr(getattr(orca, "LifecycleEvtCode", None), "Error", None)
            warn_code = getattr(getattr(orca, "LifecycleEvtCode", None), "Warn", None)
            life = orca.LifecycleEvent
            plate_created = getattr(life, "PlateCreated", None)
            plate_deleted = getattr(life, "PlateDeleted", None)
            plate_renamed = getattr(life, "PlateRenamed", None)
            gcode_started = getattr(life, "GCodeExportStarted", None)
            gcode_finished = getattr(life, "GCodeExportFinished", None)
            object_events = tuple(
                value for value in (
                    getattr(life, "ObjectAdded", None),
                    getattr(life, "ObjectDeleted", None),
                    getattr(life, "ObjectTransformed", None),
                    getattr(life, "ObjectChanged", None),
                    getattr(life, "ObjectRenamed", None),
                ) if value is not None
            )

            if event == orca.LifecycleEvent.SlicingJobComplete:
                if error_code is not None and code == error_code:
                    self.post_message({
                        "type": "state",
                        "reset": True,
                        "note": _t("note.slice_failed", detail=msg or _t("note.slice_failed_detail")),
                    })
                    return
                if warn_code is not None and code == warn_code and "cancel" in msg.lower():
                    self.post_message({
                        "type": "state",
                        "reset": True,
                        "note": _t("note.slice_cancelled"),
                    })
                    return
                _STALE = False
                _forget_live_plates()
                _clear_no_data()
                self.post_message({"type": "state", **self._scan()})
            elif event in (gcode_started, gcode_finished):
                if not (error_code is not None and code == error_code):
                    _record_gcode_path(getattr(ctx, "msg", "") or "")
                    _clear_no_data()
                    _forget_live_plates()
            elif event == orca.LifecycleEvent.ProjectOpened:
                _STALE = False
                _LIVE_PLATE_NAMES.clear()
                _forget_live_plates()
                _clear_no_data()
                _CURRENT_SESSION = None
                _CURRENT_GCODE_PATHS.clear()
                _CURRENT_PROJECT = getattr(ctx, "name", None)
                self.post_message({"type": "state", **self._scan()})
            elif event in (orca.LifecycleEvent.NewProject, orca.LifecycleEvent.ProjectClosed):
                _STALE = False
                _LIVE_PLATE_NAMES.clear()
                _forget_live_plates()
                _clear_no_data()
                _CURRENT_SESSION = None
                _CURRENT_GCODE_PATHS.clear()
                _CURRENT_PROJECT = None
                self.post_message({
                    "type": "state",
                    "reset": True,
                    "note": _t("note.open_project"),
                })
            elif event == orca.LifecycleEvent.SliceStarted:
                _CURRENT_SESSION = None
                _CURRENT_GCODE_PATHS.clear()
                _clear_no_data()
                self.post_message({
                    "type": "state",
                    "reset": True,
                    "note": _t("note.slicing"),
                })
            elif event == plate_renamed and not _STALE:
                index = getattr(ctx, "index", None)
                name = (getattr(ctx, "name", "") or "").strip()
                if isinstance(index, int) and name:
                    _LIVE_PLATE_NAMES[index] = name
                    self.post_message({"type": "state", **self._scan()})
            elif event in (plate_created, plate_deleted) or event in object_events:
                if _STALE:
                    return
                _STALE = True
                _LIVE_PLATE_NAMES.clear()
                _forget_live_plates()
                _clear_no_data()
                self.post_message({
                    "type": "state",
                    "reset": True,
                    "note": _stale_note(),
                })
        except Exception as exc:
            print("[time-calc] lifecycle %s: %s" % (event, exc))


@orca.plugin
class TimeCalculatorPlugin(orca.base):
    def register_capabilities(self):
        orca.register_capability(TimeCalculatorPage)
