import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle, Eye, Info } from 'lucide-react';
import type { RiskLevel, ClassificationType } from '../../types/api';

interface BadgeProps {
  type?: 'risk' | 'classification' | 'review' | 'status' | 'neutral';
  riskLevel?: RiskLevel | string | null;
  classification?: ClassificationType | string | null;
  reviewRequired?: boolean;
  text?: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  type = 'neutral',
  riskLevel,
  classification,
  reviewRequired,
  text,
  className = '',
}) => {
  if (type === 'risk' || riskLevel) {
    const level = (riskLevel || 'LOW').toUpperCase();
    if (level === 'HIGH') {
      return (
        <span className={`badge badge-high ${className}`}>
          <AlertTriangle size={12} />
          {text || 'HIGH RISK'}
        </span>
      );
    }
    if (level === 'MEDIUM') {
      return (
        <span className={`badge badge-medium ${className}`}>
          <AlertCircle size={12} />
          {text || 'MEDIUM RISK'}
        </span>
      );
    }
    return (
      <span className={`badge badge-low ${className}`}>
        <CheckCircle size={12} />
        {text || 'LOW RISK'}
      </span>
    );
  }

  if (reviewRequired) {
    return (
      <span className={`badge badge-review ${className}`}>
        <Eye size={12} />
        {text || 'REVIEW REQUIRED'}
      </span>
    );
  }

  if (type === 'classification' || classification) {
    const label = classification || 'UNLABELED';
    let formatted = label.replace(/_/g, ' ');
    if (label === 'LIKELY_INDUSTRIAL_INCIDENT') {
      return (
        <span className={`badge badge-high ${className}`}>
          <AlertTriangle size={12} />
          {text || formatted}
        </span>
      );
    }
    if (label === 'PERSISTENT_INDUSTRIAL_HEAT') {
      return (
        <span className={`badge badge-medium ${className}`}>
          <Info size={12} />
          {text || formatted}
        </span>
      );
    }
    if (label === 'NATURAL_WILDLAND_FIRE') {
      return (
        <span className={`badge badge-low ${className}`}>
          <CheckCircle size={12} />
          {text || formatted}
        </span>
      );
    }
    return (
      <span className={`badge badge-neutral ${className}`}>
        <Info size={12} />
        {text || formatted}
      </span>
    );
  }

  return (
    <span className={`badge badge-neutral ${className}`}>
      {text || 'INFO'}
    </span>
  );
};
