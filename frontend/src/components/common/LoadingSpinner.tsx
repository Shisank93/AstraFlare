import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading operational telemetry...',
  size = 20,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 16px', gap: '16px', color: 'var(--text-muted)' }}>
      <img src="/src/assets/branding/astraflare-logo.png" alt="AstraFlare Logo" style={{ height: '48px', objectFit: 'contain', opacity: 0.8 }} />
      <div style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '0.05em', color: '#64748b', textTransform: 'uppercase' }}>
        Geospatial Intelligence Engine
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px' }}>
        <Loader2 size={size} style={{ animation: 'spin 1s linear infinite' }} />
        <span style={{ fontSize: '13px', fontWeight: 500 }}>{message}</span>
      </div>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
