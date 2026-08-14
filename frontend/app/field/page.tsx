'use client';

import { useState, useEffect } from 'react';
import { getPlantations, submitFieldVisit, verifyFieldVisit } from '@/lib/api';
import { Plantation, AIVerification } from '@/lib/types';
import CameraCapture from '@/components/field/CameraCapture';
import GpsCapture, { ExtendedGPSData } from '@/components/field/GpsCapture';
import { Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function FieldCapturePage() {
  const [plantations, setPlantations] = useState<Plantation[]>([]);
  const [selectedPlantation, setSelectedPlantation] = useState('');
  const [workerName, setWorkerName] = useState('');
  const [gpsData, setGpsData] = useState<ExtendedGPSData | null>(null);
  const [photo, setPhoto] = useState<File | null>(null);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<AIVerification | null>(null);
  
  // Specific error states instead of generic banner
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [missingFields, setMissingFields] = useState<{site?: boolean; name?: boolean; gps?: boolean; photo?: boolean}>({});

  useEffect(() => {
    getPlantations().then(data => {
      // Filter out archived sites instead of relying on exact string matches
      const activeSites = data.filter(p => p.site_class !== 'archived');
      
      // Ensure the display names match the requested format precisely, 
      // regardless of DB truncation or encoding issues
      const formattedSites = activeSites.map(p => {
        let displayName = p.name;
        if (p.name.includes('Smriti Van')) {
          displayName = 'Smriti Van Urban Forest — Warje';
        } else if (p.name.includes('Miyawaki')) {
          displayName = 'MMRCL Compensatory Miyawaki — Goregaon';
        } else if (p.name.includes('Nashik')) {
          displayName = 'Nashik Hills Block A';
        } else if (p.name.includes('Pune')) {
          displayName = 'Pune Western Ghats B';
        }
        return { ...p, name: displayName };
      });
      
      setPlantations(formattedSites);
    }).catch(e => console.error(e));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Inline validation
    const missing = {
      site: !selectedPlantation,
      name: !workerName,
      gps: !gpsData,
      photo: !photo
    };
    
    setMissingFields(missing);
    
    if (missing.site || missing.name || missing.gps || missing.photo) {
      return;
    }
    
    setSubmitError(null);
    setIsSubmitting(true);
    
    try {
      const formData = new FormData();
      formData.append('plantation_id', selectedPlantation);
      formData.append('worker_name', workerName);
      formData.append('gps_lat', gpsData!.lat.toString());
      formData.append('gps_lng', gpsData!.lng.toString());
      formData.append('gps_accuracy', gpsData!.accuracy.toString());
      if (gpsData!.altitude !== undefined) formData.append('gps_altitude', gpsData!.altitude.toString());
      if (gpsData!.heading !== undefined) formData.append('gps_heading', gpsData!.heading.toString());
      if (gpsData!.speed !== undefined) formData.append('gps_speed', gpsData!.speed.toString());
      formData.append('client_timestamp', gpsData!.client_timestamp);
      formData.append('user_agent', gpsData!.user_agent);
      formData.append('photo', photo!);
      
      const visit = await submitFieldVisit(formData);
      
      if (visit.verification_status === 'rejected') {
        setResult({
          status: 'rejected',
          message: 'FRAUD FLAG: Location is too far outside the plantation boundary. Rejected.',
          tree_detected: false,
          health_assessment: 'poor',
          condition_notes: 'Rejected by geofence.',
          confidence: 0
        });
        setIsSubmitting(false);
        return;
      }
      
      setIsSubmitting(false);
      setIsVerifying(true);
      
      const verification = await verifyFieldVisit(visit.id);
      setResult(verification);
      
    } catch (err) {
      console.error(err);
      setSubmitError('Field visit could not be recorded.');
    } finally {
      setIsSubmitting(false);
      setIsVerifying(false);
    }
  };

  if (result) {
    if (result.status === 'rejected') {
      return (
        <main style={{ padding: '2rem 1.5rem', maxWidth: '600px', margin: '0 auto', background: 'var(--surface-ground)', minHeight: '100vh', fontFamily: 'var(--font-sans)' }}>
          <div style={{ background: 'var(--surface-primary)', padding: '2rem', borderRadius: '12px', textAlign: 'center', border: '1px solid var(--border-default)' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Location outside selected site</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '14px' }}>Move closer to the selected plantation boundary and try again.</p>
            <button onClick={() => { setResult(null); setGpsData(null); }} style={{ display: 'block', width: '100%', padding: '0.75rem', background: 'var(--surface-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-strong)', borderRadius: '8px', fontWeight: 500, cursor: 'pointer', marginBottom: '1rem' }}>
              Retry Location
            </button>
            <Link href="/" style={{ display: 'block', padding: '0.75rem', background: 'transparent', color: 'var(--text-secondary)', borderRadius: '8px', fontWeight: 500, textDecoration: 'none' }}>
              Back to Dashboard
            </Link>
          </div>
        </main>
      );
    }

    // Success (Verification in progress or complete)
    return (
      <main style={{ padding: '2rem 1.5rem', maxWidth: '600px', margin: '0 auto', background: 'var(--surface-ground)', minHeight: '100vh', fontFamily: 'var(--font-sans)' }}>
        <div style={{ background: 'var(--surface-primary)', padding: '2rem', borderRadius: '12px', textAlign: 'center', border: '1px solid var(--border-default)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Field Visit Recorded</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '14px' }}>Verification in progress.</p>
          
          <Link href="/" style={{ display: 'block', padding: '0.75rem', background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)', borderRadius: '8px', fontWeight: 500, textDecoration: 'none' }}>
            Back to Dashboard
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main style={{ padding: '0', maxWidth: '600px', margin: '0 auto', background: 'var(--surface-ground)', minHeight: '100vh', fontFamily: 'var(--font-sans)', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: '1.5rem', background: 'var(--surface-primary)', borderBottom: '1px solid var(--border-default)', position: 'sticky', top: 0, zIndex: 10 }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0, textAlign: 'center' }}>Record Field Visit</h1>
      </header>

      <form onSubmit={handleSubmit} style={{ padding: '1.5rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recorded By</label>
          <input 
            type="text" 
            value={workerName}
            onChange={(e) => setWorkerName(e.target.value)}
            placeholder="Your name"
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${missingFields.name ? 'var(--status-critical)' : 'var(--border-default)'}`, background: 'var(--surface-primary)', color: 'var(--text-primary)', fontSize: '16px' }}
          />
          {missingFields.name && <p style={{ color: 'var(--status-critical)', fontSize: '12px', marginTop: '4px', marginBottom: 0 }}>Name is required</p>}
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Plantation Site</label>
          <select 
            value={selectedPlantation}
            onChange={(e) => setSelectedPlantation(e.target.value)}
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: `1px solid ${missingFields.site ? 'var(--status-critical)' : 'var(--border-default)'}`, background: 'var(--surface-primary)', color: 'var(--text-primary)', fontSize: '16px', appearance: 'none' }}
          >
            <option value="">Select site</option>
            {plantations.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          {missingFields.site && <p style={{ color: 'var(--status-critical)', fontSize: '12px', marginTop: '4px', marginBottom: 0 }}>Select a plantation site</p>}
        </div>

        <GpsCapture onLocationFound={setGpsData} />
        {missingFields.gps && !gpsData && <p style={{ color: 'var(--status-critical)', fontSize: '12px', marginTop: '-1rem', marginBottom: '1.5rem' }}>Location is required</p>}

        <CameraCapture onImageCaptured={setPhoto} />
        {missingFields.photo && !photo && <p style={{ color: 'var(--status-critical)', fontSize: '12px', marginTop: '-1rem', marginBottom: '1.5rem' }}>Photo is required</p>}

        {submitError && (
          <div style={{ marginBottom: '1.5rem', padding: '16px', background: 'var(--surface-primary)', border: '1px solid var(--border-default)', borderRadius: '12px', textAlign: 'center' }}>
             <p style={{ color: 'var(--status-critical)', fontWeight: 500, fontSize: '14px', margin: '0 0 0.5rem 0' }}>{submitError}</p>
             <button type="button" onClick={() => setSubmitError(null)} style={{ padding: '8px 16px', background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', borderRadius: '8px', color: 'var(--text-primary)', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}>Try Again</button>
          </div>
        )}

        <div style={{ marginTop: 'auto', paddingTop: '2rem' }}>
          <button 
            type="submit" 
            disabled={isSubmitting || isVerifying || (gpsData !== null && gpsData.accuracy > 500)}
            style={{ 
              width: '100%', 
              padding: '16px', 
              background: (isSubmitting || isVerifying || (gpsData !== null && gpsData.accuracy > 500)) ? 'var(--border-default)' : 'var(--brand-primary)', 
              color: (isSubmitting || isVerifying || (gpsData !== null && gpsData.accuracy > 500)) ? 'var(--text-secondary)' : 'var(--text-inverse)', 
              borderRadius: '8px', 
              fontWeight: 500, 
              fontSize: '16px',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              cursor: (isSubmitting || isVerifying || (gpsData !== null && gpsData.accuracy > 500)) ? 'not-allowed' : 'pointer',
              transition: 'background var(--duration-sm)'
            }}
          >
            {(isSubmitting || isVerifying) && <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />}
            {(isSubmitting || isVerifying) ? 'Recording...' : 'Record Field Visit'}
          </button>
        </div>
      </form>
    </main>
  );
}
