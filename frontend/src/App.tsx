import React, { useEffect, useState } from 'react';
import { Map, BarChart3, ShieldCheck, Globe, Database, TestTube } from 'lucide-react';
import { api } from './api/client';
import type { HealthResponse, DataGovernanceSource } from './types/api';
import { OperationsPage } from './pages/OperationsPage';
import { AnalyticsDashboard } from './features/analytics/AnalyticsDashboard';
import { InvestigationsHistoryView } from './features/investigation/InvestigationsHistoryView';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'operations' | 'analytics' | 'audit'>('operations');
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
          <div className="brand-title">
            <Globe size={20} style={{ color: '#60a5fa' }} />
            ASTRAFLARE
          </div>
          <div className="brand-subtitle">Geospatial Intelligence Engine</div>
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
            <BarChart3 size={15} /> Analytics Summary
          </button>
          <button
            className={`nav-tab ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <ShieldCheck size={15} /> Analyst Audit Log
          </button>
        </nav>

        {/* Right Section: Mode Selector & Health Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Data Mode Selector */}
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
              <Database size={11} /> REAL DATA
            </button>
            <button
              onClick={() => setDataMode('SYNTHETIC_DEMO')}
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
                backgroundColor: dataMode === 'SYNTHETIC_DEMO' ? '#7c3aed' : 'transparent',
                color: '#ffffff',
                transition: 'all 0.15s ease',
              }}
            >
              <TestTube size={11} /> DEMO MODE
            </button>
          </div>

          <div className="system-status-indicator">
            <div className={`status-dot ${health?.status === 'healthy' ? '' : 'degraded'}`} />
            <span>
              {health?.status === 'healthy' ? 'System Operational' : 'Backend Degraded'} | DB:{' '}
              {health?.database || 'check...'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, overflow: 'hidden' }}>
        {activeTab === 'operations' && <OperationsPage dataMode={dataMode} setDataMode={setDataMode} />}
        {activeTab === 'analytics' && <AnalyticsDashboard />}
        {activeTab === 'audit' && <InvestigationsHistoryView />}
      </main>
    </div>
  );
};

export default App;
