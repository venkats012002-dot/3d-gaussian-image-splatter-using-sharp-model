"""Local SHARP web app: upload an image, get a 3D particle scene.

Wraps Apple's `sharp` CLI (`pip install git+https://github.com/apple/ml-sharp.git`)
behind a tiny Flask + Three.js UI. Inference runs locally on CPU/MPS/CUDA.
"""
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).parent
INPUTS = ROOT / "data" / "inputs"
OUTPUTS = ROOT / "data" / "outputs"
WEB = ROOT / "web"
META_PATH = OUTPUTS / "_meta.json"

INPUTS.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

SHARP_BIN = os.environ.get("SHARP_BIN") or shutil.which("sharp")
if not SHARP_BIN:
    raise SystemExit(
        "Could not find the `sharp` CLI on PATH. Install it with:\n"
        "  pip install git+https://github.com/apple/ml-sharp.git\n"
        "or set SHARP_BIN to its full path."
    )

DEVICE = os.environ.get("SHARP_DEVICE", "mps")  # mps | cuda | cpu
PORT = int(os.environ.get("PORT", "8765"))

app = Flask(__name__, static_folder=None)


def load_meta():
    if META_PATH.exists():
        return json.loads(META_PATH.read_text())
    return []


def save_meta(meta):
    META_PATH.write_text(json.dumps(meta, indent=2))


def seed_meta_if_empty():
    """Backfill meta with any .ply in outputs/ that isn't yet tracked."""
    meta = load_meta()
    known = {e["ply"] for e in meta}
    img_exts = {".png", ".jpg", ".jpeg", ".webp", ".heic"}
    for ply in sorted(OUTPUTS.glob("*.ply")):
        if ply.name in known:
            continue
        stem = ply.stem
        thumb = next((p for p in INPUTS.glob(f"{stem}.*") if p.suffix.lower() in img_exts), None)
        meta.append({
            "id": stem,
            "name": stem,
            "ply": ply.name,
            "thumb": thumb.name if thumb else None,
        })
    save_meta(meta)


@app.route("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.route("/splats/<path:fn>")
def splat(fn):
    return send_from_directory(OUTPUTS, fn)


@app.route("/thumbs/<path:fn>")
def thumb(fn):
    return send_from_directory(INPUTS, fn)


@app.route("/list")
def list_splats():
    return jsonify(load_meta())


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify({"error": "no image provided"}), 400

    ext = Path(f.filename).suffix.lower() or ".jpg"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".heic"}:
        return jsonify({"error": f"unsupported format {ext}"}), 400

    uid = uuid.uuid4().hex[:8]
    img_path = INPUTS / f"{uid}{ext}"
    f.save(img_path)

    cmd = [
        str(SHARP_BIN), "predict",
        "-i", str(img_path),
        "-o", str(OUTPUTS),
        "--device", DEVICE,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    ply_path = OUTPUTS / f"{uid}.ply"
    if proc.returncode != 0 or not ply_path.exists():
        img_path.unlink(missing_ok=True)
        tail = (proc.stderr or proc.stdout or "")[-800:]
        return jsonify({"error": "inference failed", "log": tail}), 500

    entry = {
        "id": uid,
        "name": Path(f.filename).stem,
        "ply": ply_path.name,
        "thumb": img_path.name,
    }
    meta = load_meta()
    meta.append(entry)
    save_meta(meta)
    return jsonify(entry)


if __name__ == "__main__":
    seed_meta_if_empty()
    print(f"SHARP particle viewer ready at http://127.0.0.1:{PORT}")
    print(f"Using `{SHARP_BIN}` on device `{DEVICE}`")
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
