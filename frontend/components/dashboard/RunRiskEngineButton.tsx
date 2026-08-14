'use client';

import { useState } from 'react';
import { triggerRiskEngineScan } from '@/lib/api';
import { Zap, Loader2 } from 'lucide-react';

export default function RunRiskEngineButton() {
  const [running, setRunning] = useState(false);

  const handleRun = async () => {
    setRunning(true);
    try {
      const res = await triggerRiskEngineScan();
      alert(`Compliance Audit completed! Found ${res.new_alerts} new reminders.`);
      window.dispatchEvent(new Event('refresh-alerts'));
      // In a real app we'd refresh the whole dashboard, for MVP a window reload is fine to update stats
      if (res.new_alerts > 0) {
        window.location.reload();
      }
    } catch (e) {
      console.error(e);
      alert('Failed to run Risk Engine');
    } finally {
      setRunning(false);
    }
  };

  return (
    <button 
      onClick={handleRun}
      disabled={running}
      style={{
        background: '#3b82f6', 
        color: '#fff', 
        padding: '0.75rem 1.5rem', 
        borderRadius: '9999px', 
        border: 'none',
        cursor: running ? 'not-allowed' : 'pointer',
        fontWeight: 700,
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.4)'
      }}
    >
      {running ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Zap size={18} />}
      {running ? 'Scanning...' : 'Run Compliance Audit'}
    </button>
  );
}
