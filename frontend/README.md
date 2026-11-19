# TerraSpectra Frontend

React + TypeScript scientific research dashboard for the TerraSpectra hyperspectral analytics platform.

## Prerequisites

- Node.js 18+
- npm 9+
- TerraSpectra FastAPI backend running on port 8000

## Setup

```powershell
cd frontend
npm install
```

## Configuration

Copy `.env.example` to `.env` and update if needed:
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Development

Start the backend first (from project root):
```powershell
.\.venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the frontend dev server:
```powershell
cd frontend
npm run dev
```

Navigate to: **http://127.0.0.1:5173**

## Production Build

```powershell
cd frontend
npm run build
```

Output is placed in `frontend/dist/`.

## Views

| View | Route | Description |
|------|-------|-------------|
| Overview | `/` | Platform summary, dataset stats, ML feasibility |
| Dataset Explorer | click nav | Browse 2436, 2973, 3079 cubes with preview images and metadata |
| Spectral Analytics | click nav | Per-cube mean/median spectral profiles with Recharts |
| ROI Comparison | click nav | Image 3079 three-region lesion comparison with divergence charts |
| Quality & Reports | click nav | Per-cube quality audit and Phase B/C report viewer |

## Scientific Constraints

- Wavelength calibration is **only shown for image 2436** (Specim IQ ENVI, 397.32–1003.58 nm).
- Images 2973 and 3079 use **zero-based band indices only**.
- NPZ values are **not** calibrated laboratory reflectance.
- No ML predictions or disease classifications are made.
