# 3D Gaussian Image Splatter using SHARP

By Venkat

Drop in a single photo, get a 3D particle cloud you can orbit around in the browser.

A tiny local web app that wraps Apple's [SHARP](https://github.com/apple/ml-sharp) monocular view-synthesis model. SHARP turns one image into ~1.2 million 3D Gaussians; this project renders them as colored particles using Three.js instead of the usual smooth Gaussian splat look.

```
image  ──►  SHARP (Apple, runs locally on MPS/CUDA/CPU)  ──►  .ply  ──►  Three.js Points renderer
```

## Features

- Upload any image from the browser, watch SHARP run on your machine, see the result load instantly
- Sidebar with thumbnails of every scene you've generated
- Live size / opacity / round-dot controls
- Pure local: runs at `http://localhost:8765`, your images and splats never leave your machine
- Apple Silicon friendly (MPS) — also works on CUDA and CPU

## Requirements

- macOS or Linux (Windows likely works but untested)
- Python 3.13
- [`uv`](https://docs.astral.sh/uv/) (`brew install uv`)
- ~6 GB free disk: ~2 GB for PyTorch + ml-sharp deps, ~2.6 GB for the SHARP model checkpoint
- A reasonably recent GPU helps a lot:
  - **CUDA**: ~1 sec per image
  - **Apple Silicon (MPS)**: ~30-40 sec per image (M1 Air tested)
  - **CPU**: minutes per image, not really recommended

## Setup

```bash
git clone https://github.com/venkats012002-dot/3d-gaussian-image-splatter-using-sharp-model.git
cd 3d-gaussian-image-splatter-using-sharp-model
./scripts/setup.sh
```

Then run it:

```bash
source .venv/bin/activate
python server.py
```

Open http://localhost:8765.

The first upload triggers a one-time 2.6 GB download of the SHARP checkpoint from Apple's CDN. Subsequent uploads skip that.

### Configuration

Environment variables:

- `SHARP_DEVICE` — `mps` (default), `cuda`, or `cpu`
- `PORT` — defaults to `8765`
- `SHARP_BIN` — full path to the `sharp` CLI if it's not on `PATH`

Example:

```bash
SHARP_DEVICE=cuda PORT=9000 python server.py
```

## How it works

1. The browser POSTs your image to `/upload`
2. The Flask server saves it under `data/inputs/` and runs `sharp predict` as a subprocess
3. SHARP outputs a `.ply` of ~1.2M 3D Gaussians under `data/outputs/`
4. The browser fetches the `.ply`, parses positions and the SH DC color (`rgb = clamp(0.5 + 0.28209 * f_dc, 0, 1)`), and renders them as Three.js `Points` with a circular sprite

The model uses an OpenCV coordinate convention (x right, y down, z forward), so the camera up vector is set to `(0, -1, 0)`.

## Limitations

- Each `.ply` is ~63 MB. Fine locally; not great for sharing over the web. A future pass should compress or downsample.
- Inference is run as a fresh subprocess per upload, so the model reloads each time (~10 sec overhead). Trade-off for a smaller idle RAM footprint.
- Trajectory video rendering (`sharp predict --render`) requires a CUDA GPU; this UI doesn't expose it.

## License

This wrapper code is MIT (see [LICENSE](LICENSE)).

**The SHARP model itself is licensed by Apple under a non-commercial research-only license.** This project does not redistribute the model weights — they are downloaded directly from Apple on first use. Use it for personal projects, research, and exploration. See [Apple's model license](https://github.com/apple/ml-sharp/blob/main/LICENSE_MODEL).

## Acknowledgements

Built on top of:

- [Apple ml-sharp](https://github.com/apple/ml-sharp) — the model that does all the heavy lifting
- [Three.js](https://threejs.org/) — particle rendering

If you build on this or share results, please cite the SHARP paper:

```bibtex
@inproceedings{Sharp2025:arxiv,
  title  = {Sharp Monocular View Synthesis in Less Than a Second},
  author = {Lars Mescheder and Wei Dong and Shiwei Li and Xuyang Bai and Marcel Santos and Peiyun Hu and Bruno Lecouat and Mingmin Zhen and Ama\"{e}l Delaunoy and Tian Fang and Yanghai Tsin and Stephan R. Richter and Vladlen Koltun},
  journal = {arXiv preprint arXiv:2512.10685},
  year   = {2025},
  url    = {https://arxiv.org/abs/2512.10685},
}
```
