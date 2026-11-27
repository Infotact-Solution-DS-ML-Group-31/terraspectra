import { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { OverviewView } from './views/OverviewView';
import { DatasetExplorerView } from './views/DatasetExplorerView';
import { SpectralAnalyticsView } from './views/SpectralAnalyticsView';
import { RoiComparisonView } from './views/RoiComparisonView';
import { QualityReportsView } from './views/QualityReportsView';
import { PcaAnalysisView } from './views/PcaAnalysisView';
import { ClusteringView } from './views/ClusteringView';
import { api } from './api/client';
import type { ViewId } from './types/api';

function App() {
  const [activeView, setActiveView] = useState<ViewId>('overview');
  const [backendStatus, setBackendStatus] = useState<'healthy' | 'degraded' | 'unknown'>('unknown');

  useEffect(() => {
    api.health()
      .then((h) => setBackendStatus(h.status))
      .catch(() => setBackendStatus('degraded'));
  }, []);

  function renderView() {
    switch (activeView) {
      case 'overview':
        return <OverviewView />;
      case 'dataset-explorer':
        return <DatasetExplorerView />;
      case 'spectral-analytics':
        return <SpectralAnalyticsView />;
      case 'roi-comparison':
        return <RoiComparisonView />;
      case 'quality-reports':
        return <QualityReportsView />;
      case 'pca-analysis':
        return <PcaAnalysisView />;
      case 'clustering':
        return <ClusteringView />;
      default:
        return <OverviewView />;
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        backendStatus={backendStatus}
      />
      <main className="flex-1 overflow-y-auto">
        <div className="min-h-full px-8 py-8">
          {renderView()}
        </div>
      </main>
    </div>
  );
}

export default App;
