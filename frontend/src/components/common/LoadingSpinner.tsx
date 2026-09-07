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
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px 16px', gap: '12px', color: 'var(--text-muted)' }}>
      <Loader2 size={size} style={{ animation: 'spin 1s linear infinite' }} />
      <span style={{ fontSize: '13px', fontWeight: 500 }}>{message}</span>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
