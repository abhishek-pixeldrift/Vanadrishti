'use client';

import { useState, useEffect } from 'react';
import { getAlerts, acknowledgeAlert } from '@/lib/api';
import { Alert } from '@/lib/types';
import { ChevronDown, ChevronRight, AlertCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function AlertsPanel() {
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [resolvedAlerts, setResolvedAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState<'critical' | 'warning' | 'resolved' | null>('warning');

  const fetchAlerts = async () => {
    try {
      const data = await getAlerts();
      setActiveAlerts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const handleRefresh = () => fetchAlerts();
    window.addEventListener('refresh-alerts', handleRefresh);
    return () => window.removeEventListener('refresh-alerts', handleRefresh);
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await acknowledgeAlert(id);
      const alertToResolve = activeAlerts.find(a => a.id === id);
      if (alertToResolve) {
        setActiveAlerts(activeAlerts.filter(a => a.id !== id));
        setResolvedAlerts([alertToResolve, ...resolvedAlerts]);
      }
      window.dispatchEvent(new Event('refresh-stats'));
    } catch (e) {
      console.error("Failed to resolve alert", e);
    }
  };

  const criticalAlerts = activeAlerts.filter(a => a.severity === 'critical' || a.severity === 'high');
  const warningAlerts = activeAlerts.filter(a => a.severity === 'medium' || a.severity === 'low');

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const SectionHeader = ({ title, count, section, icon: Icon, color }: { title: string, count: number, section: 'critical' | 'warning' | 'resolved' | null, icon: any, color: string }) => (
    <button 
      onClick={() => setExpandedSection(expandedSection === section ? null : section)}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        padding: 'var(--space-3) var(--space-4)',
        background: 'var(--surface-secondary)',
        border: 'none',
        borderRadius: 'var(--radius-md)',
        cursor: 'pointer',
        marginBottom: 'var(--space-2)',
        transition: 'background var(--duration-sm)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <Icon size={16} color={color} />
        <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>{title}</span>
        <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', background: 'var(--border-subtle)', padding: '2px 6px', borderRadius: '4px' }}>{count}</span>
      </div>
      {expandedSection === section ? <ChevronDown size={16} color="var(--text-tertiary)" /> : <ChevronRight size={16} color="var(--text-tertiary)" />}
    </button>
  );

  const AlertCard = ({ alert, isResolved }: { alert: Alert, isResolved: boolean }) => (
    <div style={{ 
      background: 'var(--surface-primary)',
      border: '1px solid var(--border-default)',
      borderLeft: `3px solid ${isResolved ? 'var(--status-neutral)' : (alert.severity === 'critical' || alert.severity === 'high' ? 'var(--status-critical)' : 'var(--status-attention)')}`,
      borderRadius: 'var(--radius-md)',
      padding: 'var(--space-3) var(--space-4)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-2)',
      marginBottom: 'var(--space-2)',
      opacity: isResolved ? 0.6 : 1
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
          {alert.alert_type.replace(/_/g, ' ')}
        </h3>
        {!isResolved && (
          <span style={{ 
            color: alert.severity === 'critical' || alert.severity === 'high' ? 'var(--status-critical)' : 'var(--status-attention)',
            fontSize: '11px',
            fontWeight: 600,
            textTransform: 'uppercase'
          }}>
            {alert.severity}
          </span>
        )}
      </div>
      
      <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
        {alert.message}
      </p>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--space-1)' }}>
        <div style={{ color: 'var(--text-tertiary)', fontSize: '11px' }}>
          {new Date(alert.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
        </div>
        
        {!isResolved && (
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button className="btn btn-secondary" style={{ height: '28px', padding: '0 8px', fontSize: '11px' }} onClick={() => {}}>
              Review
            </button>
            <button className="btn btn-ghost" style={{ height: '28px', padding: '0 8px', fontSize: '11px' }} onClick={() => handleResolve(alert.id)}>
              Resolve
            </button>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) return <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)' }}>Loading alerts...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2 style={{ fontSize: '15px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: 'var(--space-4)' }}>OPEN ALERTS</h2>
      
      <div style={{ overflowY: 'auto', flex: 1, paddingRight: 'var(--space-2)' }}>
        <SectionHeader title="Requires Attention" count={criticalAlerts.length} section="critical" icon={AlertCircle} color="var(--status-critical)" />
        {expandedSection === 'critical' && (
          <div style={{ paddingBottom: 'var(--space-3)' }}>
            {criticalAlerts.length === 0 ? <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', padding: 'var(--space-2)' }}>No critical alerts.</p> : criticalAlerts.map(a => <AlertCard key={a.id} alert={a} isResolved={false} />)}
          </div>
        )}

        <SectionHeader title="Monitor" count={warningAlerts.length} section="warning" icon={AlertTriangle} color="var(--status-attention)" />
        {expandedSection === 'warning' && (
          <div style={{ paddingBottom: 'var(--space-3)' }}>
            {warningAlerts.length === 0 ? <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', padding: 'var(--space-2)' }}>No warnings.</p> : warningAlerts.map(a => <AlertCard key={a.id} alert={a} isResolved={false} />)}
          </div>
        )}

        <SectionHeader title="Resolved" count={resolvedAlerts.length} section="resolved" icon={CheckCircle2} color="var(--status-stable)" />
        {expandedSection === 'resolved' && (
          <div style={{ paddingBottom: 'var(--space-3)' }}>
            {resolvedAlerts.length === 0 ? <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', padding: 'var(--space-2)' }}>No alerts resolved yet.</p> : resolvedAlerts.map(a => <AlertCard key={a.id} alert={a} isResolved={true} />)}
          </div>
        )}
      </div>
    </div>
  );
}
