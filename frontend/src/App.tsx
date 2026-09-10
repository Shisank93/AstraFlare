import React, { useEffect, useState } from 'react';
import { Map, BarChart3, ShieldCheck, Database, FileText } from 'lucide-react';
import { api } from './api/client';
import type { HealthResponse, DataGovernanceSource } from './types/api';
import { OperationsPage } from './pages/OperationsPage';
import { AnalyticsDashboard } from './features/analytics/AnalyticsDashboard';
import { ReportsPage } from './pages/ReportsPage';
import { InvestigationsHistoryView } from './features/investigation/InvestigationsHistoryView';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'operations' | 'analytics' | 'reports' | 'audit'>('operations');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dataMode, setDataMode] = useState<DataGovernanceSource>('REAL');

  useEffect(() => {
    api
      .getHealth()
      .then((data) => setHealth(data))
      .catch(() =>
        setHealth({
          status: 'degraded',
          database: 'disconnected',
          postgis: 'unavailable',
          ml_model: 'missing',
          version: '1.0.0',
          environment: 'production',
        })
      );
  }, []);

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Top Application Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img className="logo" src="/src/assets/branding/astraflare-logo.png" alt="AstraFlare Logo" style={{ height: '32px', width: 'auto', objectFit: 'contain' }} />
            <span style={{ fontWeight: 700, fontSize: '16px', color: '#ffffff', letterSpacing: '0.5px' }}>AstraFlare</span>
          </div>
          <span className="brand-subtitle">Geospatial Intelligence</span>
        </div>

        {/* Primary View Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'operations' ? 'active' : ''}`}
            onClick={() => setActiveTab('operations')}
          >
            <Map size={15} /> Operations Workspace
          </button>
          <button
            className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart3 size={15} /> Summary
          </button>
          <button
            className={`nav-tab ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <FileText size={15} /> Reports
          </button>
          <button
            className={`nav-tab ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <ShieldCheck size={15} /> Audit Log
          </button>
        </nav>

        {/* Right Section: Mode Selector & Health Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* System Health Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#94a3b8' }}>
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: health?.status === 'healthy' ? '#10b981' : health ? '#f59e0b' : '#64748b',
                boxShadow: health?.status === 'healthy' ? '0 0 6px rgba(16, 185, 129, 0.6)' : 'none',
              }}
            />
            <span style={{ fontWeight: 500, letterSpacing: '0.02em' }}>
              {health ? (health.status === 'healthy' ? 'SYS OPERATIONAL' : 'SYS DEGRADED') : 'CONNECTING...'}
            </span>
          </div>

          {/* Strict Data Mode Selector: REAL HISTORICAL vs REAL LIVE only */}
          <div style={{ display: 'flex', backgroundColor: 'rgba(0, 0, 0, 0.3)', borderRadius: '4px', padding: '2px' }}>
            <button
              onClick={() => setDataMode('REAL')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '3px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: dataMode === 'REAL' ? '#2563eb' : 'transparent',
                color: '#ffffff',
                transition: 'all 0.15s ease',
              }}
            >
              <Database size={11} /> REAL · HISTORICAL
            </button>
            <button
              onClick={() => setDataMode('REAL_LIVE')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '3px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: dataMode === 'REAL_LIVE' ? '#ef4444' : 'transparent',
                color: '#ffffff',
                transition: 'all 0.15s ease',
              }}
            >
              <Database size={11} /> REAL · LIVE
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, overflow: 'hidden' }}>
        {activeTab === 'operations' && <OperationsPage dataMode={dataMode} setDataMode={setDataMode} />}
        {activeTab === 'analytics' && <AnalyticsDashboard />}
        {activeTab === 'reports' && <ReportsPage />}
        {activeTab === 'audit' && <InvestigationsHistoryView />}
      </main>
    </div>
  );
};

export default App;
