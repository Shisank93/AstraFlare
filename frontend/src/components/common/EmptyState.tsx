import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Found',
  message,
  action,
}) => {
  return (
    <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
      <div style={{ display: 'inline-flex', padding: '10px', borderRadius: '50%', backgroundColor: 'var(--bg-surface-subtle)', marginBottom: '8px' }}>
        <Inbox size={24} />
      </div>
      <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)', marginBottom: '4px' }}>{title}</div>
      <div style={{ fontSize: '12px', marginBottom: '12px', maxWidth: '300px', margin: '0 auto 12px' }}>{message}</div>
      {action}
    </div>
  );
};
