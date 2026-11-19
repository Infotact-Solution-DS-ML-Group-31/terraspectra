# TerraSpectra Frontend Architecture

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript 5 |
| Bundler | Vite 5 |
| Styling | Tailwind CSS 3 (dark slate theme) |
| Charting | Recharts 2 |
| Icons | Lucide React |
| API | Native `fetch` with `credentials: include` |

## Directory Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # Centralized API fetch client
│   ├── components/
│   │   ├── Badge.tsx           # Coloured pill badges
│   │   ├── DisclaimerBox.tsx   # Scientific disclaimer panel
│   │   ├── ErrorBanner.tsx     # Error display
│   │   ├── LoadingState.tsx    # Spinner
│   │   ├── MetricCard.tsx      # KPI card
│   │   └── Sidebar.tsx         # Navigation sidebar with health pill
│   ├── types/
│   │   └── api.ts              # TypeScript interfaces (strict backend match)
│   ├── views/
│   │   ├── OverviewView.tsx
│   │   ├── DatasetExplorerView.tsx
│   │   ├── SpectralAnalyticsView.tsx
│   │   ├── RoiComparisonView.tsx
│   │   └── QualityReportsView.tsx
│   ├── App.tsx                 # Root layout and view router
│   ├── index.css               # Tailwind directives + scrollbar styles
│   └── main.tsx                # React DOM entry point
├── .env                        # VITE_API_BASE_URL=http://127.0.0.1:8000
├── .env.example
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

## API Binding

All backend calls go through `src/api/client.ts`. The base URL is read from
`import.meta.env.VITE_API_BASE_URL` at build time (default: `http://127.0.0.1:8000`).

| Client method | Endpoint |
|---------------|----------|
| `api.health()` | `GET /api/health` |
| `api.listDatasets()` | `GET /api/datasets` |
| `api.getMetadata(id)` | `GET /api/datasets/{id}/metadata` |
| `api.previewUrl(id)` | `GET /api/datasets/{id}/preview` (URL only) |
| `api.getSpectralProfile(id)` | `GET /api/datasets/{id}/spectral-profile` |
| `api.getRoiAnalysis()` | `GET /api/datasets/3079/roi-analysis` |
| `api.getQuality(id)` | `GET /api/datasets/{id}/quality` |
| `api.listReports()` | `GET /api/reports` |
| `api.getReport(id)` | `GET /api/reports/{id}` |

## State Management

Each view is self-contained with local `useState` + `useEffect` for data fetching.
No global state store (Zustand/Redux) is required at this scale.
App-level state: `activeView: ViewId` and `backendStatus`.

## Charting

- **SpectralAnalyticsView**: Recharts `LineChart` with dual Mean/Median lines.
  - X-axis: wavelength (nm) for 2436, band index for 2973/3079.
  - Dashed line for Median, solid for Mean.
  - Q25/Q75 shown as faint lines where available.
- **RoiComparisonView**: Recharts `BarChart` for top-5 divergent bands per pair.

## Scientific Constraints Enforced in UI

1. **Wavelength guard**: The `has_verified_wavelengths` field from the API
   determines whether the spectral X-axis shows "nm" or "band index". The UI
   never assigns wavelengths to 2973 or 3079.
2. **Calibration badge**: Each view displays a prominent Badge indicating
   calibration status.
3. **Disclaimer boxes**: Every view includes `<DisclaimerBox>` with scientific
   notes sourced from the backend API response.
4. **No predictions**: No classification or disease prediction UI elements exist.

## CORS

The backend (`backend/app/main.py`) restricts CORS to explicit local dev origins:
- `http://localhost:5173` / `http://127.0.0.1:5173` (Vite dev server)
- `http://localhost:3000` / `http://127.0.0.1:3000`
- `http://localhost:8000` / `http://127.0.0.1:8000`

Credentials (`cookies`) are allowed for future auth integration.

## Running Commands

| Task | Command |
|------|---------|
| Install | `cd frontend && npm install` |
| Dev server | `cd frontend && npm run dev` |
| Production build | `cd frontend && npm run build` |
| Backend | `.\.venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000` |
| All tests | `.\.venv\Scripts\python -m pytest tests/ -v` |
