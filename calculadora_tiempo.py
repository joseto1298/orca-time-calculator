# /// script
# requires-python = ">=3.9"
# dependencies = []
#
# [tool.orcaslicer.plugin]
# name = "Hora de Finalización"
# version = "0.7.7"
# description = "Muestra la hora actual y, usando la estimación del laminado, cuándo terminará la impresión."
# author = "joseto1298"
# ///

import base64
import html
import os
import re
import tempfile
import time
import zipfile

import orca

_CURRENT_PROJECT = None
_LIVE_PLATE_NAMES = {}
_LIVE_PLATES = None
_LIVE_PLATES_AT = 0.0
_STALE = False
_STALE_NOTE = "Las placas cambiaron. Lamina de nuevo para actualizar los tiempos."
_NAME_CACHE = {}
_TAIL_CACHE = {}
_SCANNING = False
_ICON_PATH = None
_ICON_B64 = "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"


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
        seconds, source = _parse_duration(m.group(1)), "total estimated time"

    if seconds is None:
        m = re.search(
            r";\s*estimated printing time \(normal mode\)\s*=\s*([^\n]+)", text, re.I
        )
        if m:
            seconds, source = _parse_duration(m.group(1)), "estimated printing time (normal)"

    if seconds is None:
        m = re.search(r";\s*model printing time:\s*([^;\n]+)", text, re.I)
        if m:
            seconds, source = _parse_duration(m.group(1)), "model printing time"

    if seconds is None:
        m = re.search(r";\s*estimated printing time[^\n=]*=\s*([^\n]+)", text, re.I)
        if m:
            seconds, source = _parse_duration(m.group(1)), "estimated printing time"

    if seconds is None:
        m = re.search(r";\s*TIME:\s*([\d.]+)", text, re.I)
        if m:
            seconds, source = float(m.group(1)), "TIME (segundos)"

    if seconds is None:
        m = re.search(r";\s*print time:\s*([^\n;]+)", text, re.I)
        if m:
            seconds, source = _parse_duration(m.group(1)), "print time"

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


def _latest_session(project=None):
    root = _temp_root()
    if not root:
        return None
    days = _dirs(root)
    days.sort(key=lambda item: (item[1], item[0]), reverse=True)
    for day_name, _mtime in days[:7]:
        day_path = os.path.join(root, day_name)
        sessions = _dirs(day_path)
        sessions.sort(key=lambda item: item[0], reverse=True)
        for session_name, _ in sessions[:50]:
            session = os.path.join(day_path, session_name)
            metadata = os.path.join(session, "Metadata")
            if not _gcode_files(metadata):
                continue
            if project:
                origin = _read_origin(session)
                if not origin or not _project_matches(origin, project):
                    continue
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
        return {}
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


def _forget_live_plates():
    global _LIVE_PLATES, _LIVE_PLATES_AT
    _LIVE_PLATES = None
    _LIVE_PLATES_AT = 0.0


def _live_plates(force=False):
    """Exporta el proyecto vivo, con cambios sin guardar, y lee sus placas."""
    global _LIVE_PLATES, _LIVE_PLATES_AT
    now = time.time()
    if _LIVE_PLATES is not None:
        max_age = 2 if force else 60
        if now - _LIVE_PLATES_AT < max_age:
            return _LIVE_PLATES
    host = getattr(orca, "host", None)
    if host is None or not hasattr(host, "plater"):
        return _LIVE_PLATES
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
  input, button { background: var(--panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 8px 10px; font-size: 14px; font-family: inherit; }
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
</style>
</head>
<body>
  <h1>Hora de Finalización</h1>
  <div class="sub">Hora actual y estimación de cuándo termina la impresión.</div>

  <div class="hero">
    <div class="label">Hora actual</div>
    <div class="now" id="nowClock">--:--:--</div>
    <div class="label" style="margin-top:14px;">Terminará a las</div>
    <div class="finish"><em id="finishClock">--:--</em></div>
    <div class="day" id="finishDay"></div>
    <div class="modes">
      <button class="mode-btn ghost" id="modeSeq">Secuencial</button>
      <button class="mode-btn ghost active" id="modeInd">Independiente</button>
    </div>
    <div class="mode-hint" id="modeHint">Independiente: cada placa empieza ahora, por separado.</div>
    <div class="dur" id="durTag">sin datos de laminado</div>
  </div>

  <div class="card">
    <h2>Datos del laminado</h2>
    <div class="field" style="margin-bottom:10px;">
      <label for="dur">Duración estimada</label>
      <input id="dur" placeholder="p. ej. 5h 23m 12s" readonly>
    </div>
    <div class="kpis">
      <div class="kpi"><div class="k">Filamento</div><div class="v" id="printFil">—</div></div>
      <div class="kpi"><div class="k">Peso</div><div class="v" id="printWeight">—</div></div>
      <div class="kpi"><div class="k">Coste</div><div class="v" id="printCost">—</div></div>
    </div>
    <div class="diag warn" id="diag">Lamina la pieza y pulsa Refrescar. Busco el G-code en la caché temporal de OrcaSlicer (%TEMP%\orcaslicer_model).</div>
    <div style="margin-top:10px;">
      <button class="ghost" id="refreshBtn">Refrescar</button>
    </div>
  </div>

  <div class="card" id="platesCard" style="display:none;">
    <h2>Placas</h2>
    <div id="platesList" class="kanban"></div>
  </div>

<script>
(function () {
  var bridge = window.orca || (typeof orca !== "undefined" ? orca : null);
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
      tagEl.textContent = DURATION_SECONDS !== null ? fmtDur(DURATION_SECONDS) : "sin datos de laminado";
      return;
    }

    tagEl.textContent = (MODE === "ind" ? "Máx. por placa · " : "Total · ") + fmtDur(horizon);
    var finish = new Date(now.getTime() + horizon * 1000);
    finishEl.textContent = two(finish.getHours()) + ":" + two(finish.getMinutes());
    dayEl.textContent = fullDate(finish);
  }

  function setMode(mode) {
    MODE = mode;
    document.getElementById("modeSeq").classList.toggle("active", mode === "seq");
    document.getElementById("modeInd").classList.toggle("active", mode === "ind");
    document.getElementById("modeHint").textContent = mode === "seq"
      ? "Secuencial: cada placa empieza al terminar la anterior."
      : "Independiente: cada placa empieza ahora, por separado.";
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
      var title = esc(p.name || p.file || ("Placa " + num));
      html +=
        "<div class='plate-card'>" +
          "<div class='pc-head'><span class='pc-num'>" + num + "</span>" +
            "<span class='pc-name' title='" + title + "'>" + title + "</span></div>" +
          "<div class='pc-label' style='margin-top:2px;'>Termina</div>" +
          "<div class='pc-finish'>--:--</div>" +
          "<div class='pc-date'></div>" +
          "<label class='pc-label' style='margin-top:8px;'>Duración estimada</label>" +
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
    document.getElementById("durTag").textContent = "sin datos de laminado";
    document.getElementById("platesCard").style.display = "none";
    document.getElementById("platesList").innerHTML = "";
  }

  function applyState(state) {
    var diag = document.getElementById("diag");
    resetState();
    if (!state || state.reset) {
      diag.className = "diag warn";
      diag.textContent = (state && state.note)
        ? String(state.note)
        : "Lamina la pieza y pulsa Refrescar. Busco el G-code en la caché temporal de OrcaSlicer (%TEMP%\\orcaslicer_model).";
      tick();
      return;
    }
    if (state.duration_seconds !== null && state.duration_seconds !== undefined) {
      DURATION_SECONDS = state.duration_seconds;
      document.getElementById("dur").value = fmtDur(state.duration_seconds);
      diag.className = "diag ok";
      diag.textContent = "Captura OK · fuente: " + (state.source || "desconocida");
    } else {
      diag.className = "diag warn";
      diag.textContent = state.note
        ? String(state.note)
        : "Ninguna placa tiene tiempo en el G-code.";
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

  function requestState() {
    if (bridge && bridge.postMessage) bridge.postMessage({ type: "get_state" });
  }

  if (bridge && bridge.onMessage) {
    bridge.onMessage(function (msg) {
      if (msg && msg.type === "state") applyState(msg);
    });
  }

  document.getElementById("refreshBtn").addEventListener("click", requestState);
  document.getElementById("modeSeq").addEventListener("click", function () { setMode("seq"); });
  document.getElementById("modeInd").addEventListener("click", function () { setMode("ind"); });

  setMode(MODE);
  tick();
  requestState();
  setInterval(tick, 1000);
})();
</script>
</body>
</html>
"""


class TimeCalculatorPage(orca.pages.PagesPluginCapabilityBase):
    def get_name(self):
        return "Tiempo"

    def get_ui(self):
        return PAGE

    def get_icon(self):
        return _icon_path()

    def on_message(self, data):
        if not isinstance(data, dict):
            return
        if data.get("type") == "get_state":
            self.post_message({"type": "state", **self._scan(force_live=True)})

    def _scan(self, force_live=False):
        global _SCANNING
        if _SCANNING:
            return {"note": "Actualizando…"}
        _SCANNING = True
        try:
            if _STALE:
                return {"note": _STALE_NOTE}
            session = _latest_session(_CURRENT_PROJECT)
            if not session:
                if _CURRENT_PROJECT:
                    return {
                        "note": "No encontré G-code de este proyecto. Lamina la pieza y pulsa Refrescar."
                    }
                return {
                    "note": "No encontré G-code en %TEMP%\\orcaslicer_model. Lamina la pieza y pulsa Refrescar."
                }

            folder = os.path.join(session, "Metadata")
            plater_names = _plater_names(session)
            files = _gcode_files(folder)
            if not files:
                return {"note": "La carpeta de G-code no contiene placas válidas."}

            live = _live_plates(force=force_live)
            live_names = live.get("names", {}) if live else {}
            if live and live.get("count"):
                allowed = set(live.get("indices") or [])
                filtered = [
                    item for item in files
                    if item[0] is None or item[0] in allowed
                ]
                if filtered:
                    files = filtered
                elif len(files) > live["count"]:
                    def _mtime(item):
                        try:
                            return os.path.getmtime(os.path.join(folder, item[1]))
                        except OSError:
                            return 0
                    files = sorted(files, key=_mtime, reverse=True)[: live["count"]]

            plates = []
            for index, name in files:
                path = os.path.join(folder, name)
                try:
                    seconds, source, filament_mm, filament_g, cost = _metrics_for(path)
                except Exception as exc:
                    print("[time-calc] error leyendo %s: %s" % (name, exc))
                    continue
                ordinal = index if index is not None else len(plates)
                plate_no = ordinal + 1
                live_name = _LIVE_PLATE_NAMES.get(index) if index is not None else None
                plates.append({
                    "index": index,
                    "name": live_name or live_names.get(index) or plater_names.get(ordinal) or ("Placa %d" % plate_no),
                    "file": name,
                    "duration_seconds": seconds,
                    "filament_mm": filament_mm,
                    "filament_g": filament_g,
                    "cost": cost,
                    "source": source,
                })

            if not plates:
                return {"note": "La carpeta de G-code no contiene placas válidas."}

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

            data = {
                "plates": plates,
                "plate_count": len(plates),
                "duration_seconds": total_secs,
                "filament_mm": total_mm,
                "filament_g": total_g,
                "cost": total_cost,
                "source": ("suma de %d placas" % len(plates)) if len(plates) > 1 else (plates[0]["source"] or "desconocida"),
                "note": None if total_secs is not None else "Ninguna placa tiene tiempo en el G-code.",
                "ran_at": time.time(),
            }
            print("[time-calc] scan %d placas -> %s s" % (len(plates), total_secs))
            return data
        except Exception as exc:
            print("[time-calc] error en scan: %s" % exc)
            return {"note": "Error leyendo la caché de OrcaSlicer: %s" % exc}
        finally:
            _SCANNING = False

    def on_lifecycle_event(self, event, ctx):
        global _CURRENT_PROJECT, _STALE
        try:
            code = getattr(ctx, "code", None)
            msg = getattr(ctx, "msg", "") or ""
            error_code = getattr(getattr(orca, "LifecycleEvtCode", None), "Error", None)
            warn_code = getattr(getattr(orca, "LifecycleEvtCode", None), "Warn", None)
            life = orca.LifecycleEvent
            plate_created = getattr(life, "PlateCreated", None)
            plate_deleted = getattr(life, "PlateDeleted", None)
            plate_renamed = getattr(life, "PlateRenamed", None)
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
                        "note": "El laminado falló: %s" % (msg or "sin detalle"),
                    })
                    return
                if warn_code is not None and code == warn_code and "cancel" in msg.lower():
                    self.post_message({
                        "type": "state",
                        "reset": True,
                        "note": "Laminado cancelado.",
                    })
                    return
                _STALE = False
                _forget_live_plates()
                self.post_message({"type": "state", **self._scan()})
            elif event == orca.LifecycleEvent.ProjectOpened:
                _STALE = False
                _LIVE_PLATE_NAMES.clear()
                _forget_live_plates()
                _CURRENT_PROJECT = getattr(ctx, "name", None)
                self.post_message({"type": "state", **self._scan()})
            elif event in (orca.LifecycleEvent.NewProject, orca.LifecycleEvent.ProjectClosed):
                _STALE = False
                _LIVE_PLATE_NAMES.clear()
                _forget_live_plates()
                _CURRENT_PROJECT = None
                self.post_message({
                    "type": "state",
                    "reset": True,
                    "note": "Abre o lamina un proyecto para ver la estimación.",
                })
            elif event == orca.LifecycleEvent.SliceStarted:
                self.post_message({
                    "type": "state",
                    "reset": True,
                    "note": "Laminando…",
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
                self.post_message({
                    "type": "state",
                    "reset": True,
                    "note": _STALE_NOTE,
                })
        except Exception as exc:
            print("[time-calc] lifecycle %s: %s" % (event, exc))


@orca.plugin
class TimeCalculatorPlugin(orca.base):
    def register_capabilities(self):
        orca.register_capability(TimeCalculatorPage)
