import base64
import hashlib
import re
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLUGIN = ROOT / "calculadora_tiempo.py"
ICON = ROOT / "3.png"
DIST = ROOT / "dist"


def read_version():
    text = PLUGIN.read_text(encoding="utf-8")
    match = re.search(r'^# version = "([^"]+)"', text, re.M)
    if not match:
        raise SystemExit("No version found in calculadora_tiempo.py")
    return match.group(1)


def wheel_name(name, version):
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9.]+", "_", ascii_name).strip("._").lower()
    return "%s-%s-py3-none-any.whl" % (slug, version)


def record_line(archive_name, data):
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    return "%s,sha256=%s,%d" % (archive_name, digest, len(data))


def build():
    version = read_version()
    name = "Hora-de-Finalizacion"
    dist_info = "hora_de_finalizacion-%s.dist-info" % version
    files = {
        "calculadora_tiempo.py": PLUGIN.read_bytes(),
        "3.png": ICON.read_bytes(),
        dist_info + "/METADATA": (
            "Metadata-Version: 2.1\n"
            "Name: %s\n"
            "Version: %s\n"
            "Summary: Plugin para OrcaSlicer que muestra la hora de finalización estimada.\n"
            "Author: joseto1298\n"
            "Requires-Python: >=3.9\n"
            "License: MIT\n"
            "Import-Name: calculadora_tiempo\n"
            "\n"
            "Muestra la hora actual, el fin estimado, los totales y una tarjeta por placa.\n"
            % (name, version)
        ).encode("utf-8"),
        dist_info + "/WHEEL": (
            "Wheel-Version: 1.0\n"
            "Generator: build_wheel.py\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ).encode("utf-8"),
        dist_info + "/top_level.txt": b"calculadora_tiempo\n",
    }

    record = [record_line(archive_name, data) for archive_name, data in files.items()]
    record.append(dist_info + "/RECORD,,")
    files[dist_info + "/RECORD"] = ("\n".join(record) + "\n").encode("utf-8")

    DIST.mkdir(exist_ok=True)
    target = DIST / wheel_name(name, version)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for archive_name, data in files.items():
            zf.writestr(archive_name, data)
    print(target)
    return target


if __name__ == "__main__":
    build()
