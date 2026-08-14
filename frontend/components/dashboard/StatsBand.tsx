'use client';

import React, { useState, useEffect, useRef } from 'react';

function CountUp({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(0);
  const prevValue = useRef(0);

  useEffect(() => {
    if (value === prevValue.current) return;
    
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      setDisplayValue(value);
      prevValue.current = value;
      return;
    }

    const startValue = prevValue.current;
    const endValue = value;
    const duration = 600;
    let startTime: number | null = null;
    let animationFrameId: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      
      // easeOutCubic
      const t = Math.min(progress / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      
      const current = Math.floor(startValue + (endValue - startValue) * ease);
      setDisplayValue(current);

      if (progress < duration) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        setDisplayValue(endValue);
        prevValue.current = endValue;
      }
    };

    animationFrameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrameId);
  }, [value]);

  const padded = String(displayValue).padStart(2, '0');
  return <>{padded}</>;
}

const Metric = ({ value, label }: { value: number; label: string }) => (
  <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
    <span style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
      <CountUp value={value} />
    </span>
    <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
      {label}
    </span>
  </div>
);

const Divider = () => <span style={{ color: 'var(--text-tertiary)', fontSize: '24px', lineHeight: 1 }}>·</span>;

interface StatsBandProps {
  stats: {
    total: number;
    stable: number;
    priority: number;
    open: number;
  };
}

export default function StatsBand({ stats }: StatsBandProps) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-6)',
      padding: 'var(--space-4) 0',
      borderBottom: '1px solid var(--border-default)',
      fontFamily: 'var(--font-sans)',
      flexWrap: 'wrap'
    }}>
      <Metric value={stats.total} label="Sites" />
      <Divider />
      <Metric value={stats.stable} label="Stable" />
      <Divider />
      <Metric value={stats.priority} label="Priority" />
      <Divider />
      <Metric value={stats.open} label="Open" />
    </div>
  );
}
