import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to reach AstraFlare backend',
  message,
  onRetry,
}) => {
  return (
    <div style={{ padding: '24px 16px', textAlign: 'center', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', margin: '16px' }}>
      <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'inline-flex', padding: '8px', borderRadius: '50%', backgroundColor: '#fee2e2', color: '#dc2626' }}>
          <AlertOctagon size={24} />
        </div>
      </div>
      <div style={{ fontWeight: 600, fontSize: '14px', color: '#991b1b', marginBottom: '4px' }}>{title}</div>
      <div style={{ fontSize: '12px', color: '#7f1d1d', marginBottom: '12px' }}>{message}</div>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={<RefreshCw size={12} />} onClick={onRetry}>
          Retry Connection
        </Button>
      )}
    </div>
  );
};
