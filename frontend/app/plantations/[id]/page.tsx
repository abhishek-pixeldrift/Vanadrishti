import { getPlantation, getNDVIObservations, getLastVerifiedVisit, getActiveAlerts, getRiskScore } from '@/lib/api';
import { RiskResult } from '@/lib/types';
import NDVIChart from '@/components/charts/NDVIChart';
import Link from 'next/link';
import { ArrowLeft, MapPin, CalendarCheck, Map, ShieldCheck, BellRing, Activity, AlertTriangle, CheckCircle2 } from 'lucide-react';
import ThemeToggle from '@/components/ThemeToggle';

export default async function PlantationDetailPage({ params }: { params: { id: string } }) {
  const plantation = await getPlantation(params.id);
  const ndviRes = await getNDVIObservations(params.id);
  const ndviData = ndviRes.data;
  const metadata = ndviRes.metadata;
  
  const lastVerifiedVisit = await getLastVerifiedVisit(params.id);
  const activeAlerts = await getActiveAlerts(params.id);
  
  let riskResult: RiskResult | null = null;
  try {
    riskResult = await getRiskScore(params.id);
  } catch {
    // Fallback: risk endpoint unavailable
  }

  // Group by month-year
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const monthlyDataMap = new globalThis.Map<string, any>();
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ndviData.forEach((d: any) => {
    const dateObj = new Date(d.observation_date);
    const monthKey = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
    const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    
    if (!monthlyDataMap.has(monthKey)) {
      monthlyDataMap.set(monthKey, {
        date: dateStr,
        monthKey,
        rawDate: d.observation_date,
        values: [],
        status: d.health_status
      });
    }
    
    if (d.ndvi_value !== null && d.ndvi_value !== undefined) {
      monthlyDataMap.get(monthKey).values.push(Number(d.ndvi_value));
    }
  });

  // Calculate median per month and sort chronologically
  const aggregatedData = Array.from(monthlyDataMap.values())
    .sort((a, b) => a.monthKey.localeCompare(b.monthKey))
    .map(bucket => {
      let median = null;
      if (bucket.values.length > 0) {
        bucket.values.sort((a: number, b: number) => a - b);
        const mid = Math.floor(bucket.values.length / 2);
        median = bucket.values.length % 2 !== 0 
          ? bucket.values[mid] 
          : (bucket.values[mid - 1] + bucket.values[mid]) / 2;
      }
      return {
        observation_date: bucket.rawDate,
        ndvi_value: median, // preserve null
        health_status: bucket.status
      };
    });

  // Calculate trend from valid aggregated monthly points
  let trend = 'Stable';
  let trendColor = 'var(--text-secondary)';
  let latestNdvi = null;
  let latestDate = null;
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const validAggregatedData = aggregatedData.filter((d: any) => d.ndvi_value !== null);
  
  if (validAggregatedData.length > 0) {
    const latest = validAggregatedData[validAggregatedData.length - 1];
    latestNdvi = latest.ndvi_value.toFixed(2);
    latestDate = new Date(latest.observation_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    
    if (validAggregatedData.length > 1) {
      const prev = validAggregatedData[validAggregatedData.length - 2];
      const diff = latest.ndvi_value - prev.ndvi_value;
      if (diff > 0.05) {
        trend = 'Improving';
        trendColor = 'var(--status-stable)';
      } else if (diff < -0.05) {
        trend = 'Declining';
        trendColor = 'var(--status-critical)';
      }
    }
  }

  // Dynamic risk — use engine result if available, fall back to static
  const riskScore = riskResult?.risk_score ?? plantation.risk_score;
  const riskLevel = riskResult?.risk_level ?? (plantation.status === 'healthy' ? 'HEALTHY' : plantation.status === 'warning' ? 'WARNING' : 'CRITICAL');
  const statusColor = riskLevel === 'HEALTHY' ? 'var(--status-stable)' : riskLevel === 'WARNING' ? 'var(--status-attention)' : 'var(--status-critical)';
  const statusBg = riskLevel === 'HEALTHY' ? 'var(--status-stable-bg)' : riskLevel === 'WARNING' ? 'var(--status-attention-bg)' : 'var(--status-critical-bg)';

  return (
    <main style={{ padding: 'var(--space-6)', maxWidth: '1200px', margin: '0 auto', background: 'var(--surface-background)', minHeight: '100vh', fontFamily: 'var(--font-sans)' }}>
      {/* Navigation & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
        <Link href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 500, fontSize: '13px', transition: 'color var(--duration-sm)' }}>
          <ArrowLeft size={16} /> Back to Map
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <ThemeToggle />
          <Link href={`/field?site=${plantation.id}`} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--brand-primary)', border: 'none', color: 'var(--text-inverse)', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 500, fontSize: '13px', textDecoration: 'none' }}>
            Record Visit
          </Link>
        </div>
      </div>

      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-8)', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 var(--space-2) 0', letterSpacing: '-0.01em', lineHeight: 1.2 }}>
            {plantation.name}
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-1)', fontSize: '14px' }}>
            <MapPin size={14} /> {plantation.district}, {plantation.state}
          </p>
          <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
            {plantation.boundary_status === 'mvp_proxy' && (
              <span style={{ padding: '2px 6px', fontSize: '11px', background: 'var(--status-attention-bg)', color: 'var(--status-attention)', border: '1px solid var(--status-attention)', borderRadius: 'var(--radius-sm)', fontWeight: 500 }}>
                Traced Boundary
              </span>
            )}
            {plantation.site_class === 'synthetic_demo' && (
              <span style={{ padding: '2px 6px', fontSize: '11px', background: 'var(--status-neutral-bg)', color: 'var(--status-neutral)', border: '1px solid var(--status-neutral)', borderRadius: 'var(--radius-sm)', fontWeight: 500 }}>
                Demonstration Site
              </span>
            )}
          </div>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 'var(--space-2)' }}>
            <div style={{ 
            backgroundColor: statusBg, 
            color: statusColor, 
            border: `1px solid ${statusColor}`,
            padding: 'var(--space-2) var(--space-4)', 
            borderRadius: 'var(--radius-sm)', 
            fontWeight: 600, 
            textTransform: 'uppercase', 
            letterSpacing: '0.05em',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            fontSize: '13px'
            }}>
            {riskLevel === 'CRITICAL' && <AlertTriangle size={16} />}
            {riskLevel === 'HEALTHY' && <CheckCircle2 size={16} />}
            {riskLevel === 'WARNING' && <Activity size={16} />}
            {riskLevel} STATUS
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                RISK INDEX: {riskScore}/100
            </div>
        </div>
      </header>

      {/* Dynamic Risk Breakdown */}
      {riskResult && (
        <section style={{ background: 'var(--surface-primary)', padding: 'var(--space-5)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', marginBottom: 'var(--space-6)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
            <h3 style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Risk Breakdown</h3>
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginLeft: 'auto', fontFamily: 'var(--font-mono)' }}>
              COMPUTED {new Date(riskResult.generated_at).toLocaleString().toUpperCase()}
            </span>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--space-4)' }}>
            {Object.entries(riskResult.components).map(([key, comp]) => {
              const pct = (comp.score / comp.max) * 100;
              const barColor = pct === 0 ? 'var(--status-stable)' : pct < 50 ? 'var(--status-attention)' : 'var(--status-critical)';
              const labels: Record<string, string> = {
                ndvi: 'NDVI', ai_health: 'AI Health', visit_recency: 'Visit Recency',
                maintenance: 'Maintenance', location_trust: 'Location Trust'
              };
              return (
                <div key={key}>
                  <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.02em' }}>{labels[key] || key}</p>
                  <div style={{ background: 'var(--border-subtle)', borderRadius: '2px', height: '4px', overflow: 'hidden', marginBottom: 'var(--space-1)' }}>
                    <div style={{ width: `${pct}%`, background: barColor, height: '100%', borderRadius: '2px', transition: 'width 0.3s' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <p style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{comp.score}/{comp.max}</p>
                    <p style={{ margin: 0, fontSize: '10px', color: 'var(--text-tertiary)' }}>{comp.source === 'none' ? 'No data' : comp.source}</p>
                  </div>
                </div>
              );
            })}
          </div>
          {riskResult.missing_inputs.length > 0 && (
            <div style={{ margin: 'var(--space-4) 0 0 0', padding: 'var(--space-2) var(--space-3)', fontSize: '11px', color: 'var(--status-attention)', background: 'var(--status-attention-bg)', border: '1px solid var(--status-attention)', borderRadius: 'var(--radius-sm)', display: 'inline-block' }}>
              Missing telemetry: {riskResult.missing_inputs.join(', ')}
            </div>
          )}
        </section>
      )}

      {/* Info Cards */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
        {/* Mapped Area */}
        <div style={{ background: 'var(--surface-primary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
            <Map size={14} color="var(--text-tertiary)" />
            <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Area</p>
          </div>
          <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '24px', fontWeight: 500, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{plantation.area_hectares} <span style={{fontSize: '14px', color: 'var(--text-tertiary)'}}>ha</span></p>
          <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-tertiary)' }}>GIS Survey</p>
        </div>

        {/* Location Trust */}
        <div style={{ background: 'var(--surface-primary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
            <ShieldCheck size={14} color="var(--text-tertiary)" />
            <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Location Trust</p>
          </div>
          <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '24px', fontWeight: 500, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
            {lastVerifiedVisit?.location_confidence?.score ? `${lastVerifiedVisit.location_confidence.score}` : '--'} <span style={{fontSize: '14px', color: 'var(--text-tertiary)'}}>{lastVerifiedVisit?.location_confidence?.score ? '/100' : ''}</span>
          </p>
          <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-tertiary)' }}>Anti-spoofing score</p>
        </div>

        {/* Active Alerts */}
        <div style={{ background: 'var(--surface-primary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
            <BellRing size={14} color="var(--text-tertiary)" />
            <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Open Alerts</p>
          </div>
          <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '24px', fontWeight: 500, color: activeAlerts.length > 0 ? 'var(--status-critical)' : 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{activeAlerts.length}</p>
          <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-tertiary)' }}>Requires attention</p>
        </div>

        {/* Last Verified Visit */}
        <div style={{ background: 'var(--surface-primary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
            <CalendarCheck size={14} color="var(--text-tertiary)" />
            <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Latest Audit</p>
          </div>
          <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '18px', fontWeight: 500, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
            {lastVerifiedVisit?.server_timestamp 
              ? new Date(lastVerifiedVisit.server_timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) 
              : 'N/A'}
          </p>
          <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-tertiary)' }}>{lastVerifiedVisit?.worker_name ? `By ${lastVerifiedVisit.worker_name}` : 'System'}</p>
        </div>
      </section>

      {/* NDVI Chart Section */}
      <section style={{ background: 'var(--surface-primary)', padding: 'var(--space-6)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-default)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 var(--space-2) 0', color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Vegetation Health (NDVI)</h2>
            <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '13px', maxWidth: '600px' }}>Satellite-derived Normalized Difference Vegetation Index. Values below 0.3 indicate severe environmental stress.</p>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 'var(--space-2)' }}>
            {metadata.dataSource === 'sentinel2' ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)', background: 'rgba(59, 107, 138, 0.1)', color: '#3B6B8A', padding: '4px 10px', borderRadius: 'var(--radius-sm)', fontSize: '11px', fontWeight: 600, letterSpacing: '0.02em', textTransform: 'uppercase', border: '1px solid rgba(59, 107, 138, 0.2)' }}>
                SENTINEL-2 COPERNICUS
              </span>
            ) : (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)', background: 'var(--status-neutral-bg)', color: 'var(--status-neutral)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', fontSize: '11px', fontWeight: 600, letterSpacing: '0.02em', textTransform: 'uppercase', border: '1px solid var(--status-neutral)' }}>
                DEMO / FALLBACK DATA
              </span>
            )}
            
            {metadata.fallbackUsed && (
              <p style={{ margin: 0, fontSize: '11px', color: 'var(--status-attention)', maxWidth: '300px', textAlign: 'right' }}>
                Imagery unavailable: {metadata.failureReason || 'Failed to fetch API'}
              </p>
            )}
          </div>
        </div>

        {aggregatedData.length > 0 ? (
          <>
            <div style={{ display: 'flex', gap: 'var(--space-8)', marginBottom: 'var(--space-6)', padding: 'var(--space-4)', background: 'var(--surface-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Latest Index</p>
                <p style={{ margin: 0, fontSize: '24px', fontWeight: 500, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{latestNdvi}</p>
              </div>
              <div>
                <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Acquisition Date</p>
                <p style={{ margin: 0, fontSize: '16px', fontWeight: 500, color: 'var(--text-primary)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>{latestDate}</p>
              </div>
              <div>
                <p style={{ margin: '0 0 var(--space-1) 0', fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Trend</p>
                <p style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: trendColor, marginTop: '4px' }}>{trend}</p>
              </div>
            </div>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <NDVIChart data={aggregatedData as any} />
          </>
        ) : (
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--surface-secondary)', borderRadius: 'var(--radius-md)', color: 'var(--text-tertiary)', border: '1px dashed var(--border-default)' }}>
            <p style={{ fontWeight: 500, fontSize: '13px' }}>No telemetry data acquired for this site.</p>
          </div>
        )}
      </section>
    </main>
  );
}
