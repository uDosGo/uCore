// MultiColumnProse Component
// Usage: <MultiColumnProse>content</MultiColumnProse>
// This component extends Prose UI with multi-column layout support

import React from 'react';
import './multi-column-prose.css';

interface MultiColumnProseProps {
  children: React.ReactNode;
  className?: string;
}

export default function MultiColumnProse({ children, className = '' }: MultiColumnProseProps) {
  return (
    <div className={`prose-multi ${className}`}>
      {children}
    </div>
  );
}