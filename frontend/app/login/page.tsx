'use client';

import { User, ShieldCheck } from 'lucide-react';
import ThemeToggle from '@/components/ThemeToggle';

export default function LoginPage() {

  const handleLogin = (role: 'public' | 'officer') => {
    localStorage.setItem('ecotrack_role', role);
    window.location.href = '/';
  };

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--surface-ground)', fontFamily: 'var(--font-sans)', padding: '2rem', position: 'relative' }}>
      
      <div style={{ position: 'absolute', top: '1rem', right: '1rem' }}>
        <ThemeToggle />
      </div>

      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>Vanadrishti</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', margin: 0, maxWidth: '500px' }}>
          Environmental Monitoring & Geographic Accountability Platform
        </p>
      </div>

      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        
        {/* Public Citizen Login */}
        <button 
          onClick={() => handleLogin('public')}
          style={{
            background: 'var(--surface-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: '12px',
            padding: '2rem',
            width: '280px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-sm)',
            transition: 'transform 0.2s ease',
          }}
          onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
          onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
        >
          <User size={48} color="var(--text-tertiary)" style={{ marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)', margin: '0 0 0.5rem 0' }}>Citizen Access</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
            View public data and transparency dashboard.
          </p>
        </button>

        {/* Forestry Officer Login */}
        <button 
          onClick={() => handleLogin('officer')}
          style={{
            background: 'var(--surface-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: '12px',
            padding: '2rem',
            width: '280px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-sm)',
            transition: 'transform 0.2s ease',
          }}
          onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
          onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
        >
          <ShieldCheck size={48} color="var(--brand-primary)" style={{ marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)', margin: '0 0 0.5rem 0' }}>Authorized Personnel</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
            Run compliance audits and manage alerts.
          </p>
        </button>

      </div>
    </main>
  );
}
