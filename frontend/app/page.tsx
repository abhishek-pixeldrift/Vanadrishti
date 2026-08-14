'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getPlantations, getDashboardStats } from '@/lib/api';
import { DashboardStats, Plantation } from '@/lib/types';
import dynamic from 'next/dynamic';
import StatCard from '@/components/dashboard/StatCard';
import AlertsPanel from '@/components/dashboard/AlertsPanel';
import RunRiskEngineButton from '@/components/dashboard/RunRiskEngineButton';
import { TreePine, CheckCircle, Bell, Activity, LogOut, Plus } from 'lucide-react';
import ThemeToggle from '@/components/ThemeToggle';
import Link from 'next/link';

const PlantationMap = dynamic(() => import('@/components/map/PlantationMap'), { 
  ssr: false,
  loading: () => <div style={{ height: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--card-bg, #ffffff)', borderRadius: '12px', border: '1px solid var(--card-border, #e5e5e5)', color: 'var(--text-muted, #737373)' }}>Loading Map...</div>
});

export default function Home() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [plantations, setPlantations] = useState<Plantation[]>([]);
  const [role, setRole] = useState<'public' | 'officer' | null>(null);

  const [alertsExpanded, setAlertsExpanded] = useState(false);
  const [actionsExpanded, setActionsExpanded] = useState(false);

  useEffect(() => {
    const storedRole = localStorage.getItem('ecotrack_role') as 'public' | 'officer';
    if (!storedRole) {
      router.push('/login');
      return;
    }
    setRole(storedRole);

    const loadData = async () => {
      try {
        const s = await getDashboardStats();
        setStats(s);
        const p = await getPlantations();
        setPlantations(p);
      } catch {
        console.error("Failed to load dashboard data");
      }
    };
    loadData();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('ecotrack_role');
    window.location.href = '/login';
  };

  if (!stats || !role) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted, #737373)' }}>Loading Dashboard...</div>;

  const isOfficer = role === 'officer';

  return (
    <main className="dashboard-main">
      <header className="dashboard-header">
        <div className="dashboard-header-titles">
          <h1>Vanadrishti</h1>
          <p style={{ color: 'var(--text-muted, #737373)' }}>
            {isOfficer ? 'Forestry Officer View - Audits & Alerts' : 'Public Citizen View - Transparency Dashboard'}
          </p>
        </div>
        
        {/* Desktop Header Actions */}
        <div className="dashboard-header-actions desktop-only">
          <ThemeToggle />
          <Link href="/field" className="btn btn-primary">
            <Plus size={16} /> Record Field Visit
          </Link>
          {isOfficer && <RunRiskEngineButton />}
          <button onClick={handleLogout} className="btn btn-secondary">
            <LogOut size={16} /> Logout
          </button>
        </div>

        {/* Mobile Header Actions (Compact) */}
        <div className="dashboard-header-actions mobile-only" style={{ gap: '0.5rem', width: '100%', justifyContent: 'space-between' }}>
          <ThemeToggle />
          <button onClick={handleLogout} className="btn btn-secondary">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </header>

      {/* Stats Row */}
      <div className="dashboard-stats">
        <StatCard title="Total Plantations" value={stats.total_plantations} icon={TreePine} color="#3b82f6" />
        <StatCard title="Healthy Zones" value={stats.healthy_count} icon={CheckCircle} color="#10b981" />
        <StatCard title="High Risk" value={stats.at_risk_count} icon={Activity} color="#f59e0b" />
        <StatCard title="Active Alerts" value={stats.active_alerts} icon={Bell} color="#ef4444" />
      </div>

      {/* Map & Content Container */}
      <div className={`dashboard-content ${!isOfficer ? 'public' : ''}`}>
        <div className="dashboard-map-container">
          <PlantationMap plantations={plantations} />
        </div>
        
        {isOfficer && (
          <>
            {/* Desktop Alerts */}
            <div className="dashboard-alerts-container desktop-only">
              <AlertsPanel />
            </div>
          </>
        )}
      </div>

      {/* Mobile Collapsible Alerts (Officer Only) */}
      {isOfficer && (
        <div className="mobile-collapsible mobile-only-block">
          <div className="mobile-collapsible-header" onClick={() => setAlertsExpanded(!alertsExpanded)}>
            <span>System Alerts ({stats.active_alerts})</span>
            <span>{alertsExpanded ? '▲' : '▼'}</span>
          </div>
          {alertsExpanded && (
            <div className="mobile-collapsible-content">
              <AlertsPanel />
            </div>
          )}
        </div>
      )}

      {/* Mobile Field Actions (All Roles, but dynamic contents) */}
      <div className="mobile-collapsible mobile-only-block">
        <div className="mobile-collapsible-header" onClick={() => setActionsExpanded(!actionsExpanded)}>
          <span>Field Actions</span>
          <span>{actionsExpanded ? '▲' : '▼'}</span>
        </div>
        {actionsExpanded && (
          <div className="mobile-collapsible-content" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Link href="/field" className="btn btn-primary" style={{ width: '100%' }}>
              <Plus size={16} /> Record Field Visit
            </Link>
            {isOfficer && (
              <div style={{ display: 'flex', width: '100%' }}>
                 <RunRiskEngineButton />
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
