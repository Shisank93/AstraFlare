import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  loading = false,
  icon,
  disabled,
  className = '',
  ...props
}) => {
  const variantClass =
    variant === 'primary'
      ? 'btn-primary'
      : variant === 'danger'
      ? 'btn-danger'
      : variant === 'success'
      ? 'btn-success'
      : '';
  const sizeClass = size === 'sm' ? 'btn-sm' : '';

  return (
    <button
      className={`btn ${variantClass} ${sizeClass} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 size={14} className="animate-spin" />
      ) : (
        icon
      )}
      {children}
    </button>
  );
};
