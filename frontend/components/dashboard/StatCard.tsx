'use client';
import React, { useState, useEffect } from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color?: string;
}

export default function StatCard({ title, value, icon: Icon, color = 'var(--primary)' }: StatCardProps) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const target = typeof value === 'number' ? value : parseInt(value as string, 10);
    if (isNaN(target)) {
      setDisplayValue(0);
      return;
    }

    let start = 0;
    const duration = 1000;
    const increment = target / (duration / 16); // 60fps

    const timer = setInterval(() => {
      start += increment;
      if (start >= target) {
        setDisplayValue(target);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.ceil(start));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <div style={{ 
      padding: '1.5rem', 
      borderRadius: '16px', 
      background: 'var(--card-bg)', 
      border: '1px solid var(--card-border)', 
      display: 'flex', 
      alignItems: 'center', 
      gap: '1.25rem', 
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
      transition: 'transform 0.2s',
      cursor: 'default'
    }}
    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
    onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
    >
      <div style={{ 
        backgroundColor: `${color}15`, 
        padding: '1rem', 
        borderRadius: '12px', 
        color: color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Icon size={28} strokeWidth={2.5} />
      </div>
      <div>
        <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.025em' }}>{title}</p>
        <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.75rem', fontWeight: 800, color: 'var(--foreground)' }}>
          {typeof value === 'number' || !isNaN(Number(value)) ? displayValue : value}
        </p>
      </div>
    </div>
  );
}
