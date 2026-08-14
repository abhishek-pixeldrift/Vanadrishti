'use client';

import { useState, useEffect, useRef } from 'react';
import { MapPin, RefreshCw, AlertTriangle } from 'lucide-react';

export interface ExtendedGPSData {
  lat: number;
  lng: number;
  accuracy: number;
  altitude?: number;
  heading?: number;
  speed?: number;
  client_timestamp: string;
  user_agent: string;
}

interface GpsCaptureProps {
  onLocationFound: (data: ExtendedGPSData) => void;
}

export default function GpsCapture({ onLocationFound }: GpsCaptureProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState<ExtendedGPSData | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const MAX_RETRIES = 5;

  const handleGetLocation = (isRetry = false) => {
    if (!isRetry) {
      setLoading(true);
      setRetryCount(0);
    }
    setError(null);
    
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const data: ExtendedGPSData = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude || undefined,
          heading: position.coords.heading || undefined,
          speed: position.coords.speed || undefined,
          client_timestamp: new Date(position.timestamp).toISOString(),
          user_agent: navigator.userAgent
        };
        
        setLocation(data);
        onLocationFound(data);
        
        if (data.accuracy > 100) {
          handleAutoRetry(isRetry);
        } else {
          setLoading(false);
        }
      },
      (err) => {
        setError(err.message);
        handleAutoRetry(isRetry);
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
    );
  };

  const handleAutoRetry = (isRetry: boolean) => {
    setRetryCount(prev => {
      const nextCount = isRetry ? prev + 1 : 1;
      if (nextCount < MAX_RETRIES) {
        if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = setTimeout(() => {
          handleGetLocation(true);
        }, 3000);
      } else {
        setLoading(false); // Stop retrying after max attempts
      }
      return nextCount;
    });
  };

  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
    };
  }, []);

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy <= 50) return { bg: 'var(--status-stable-bg)', border: 'var(--status-stable)', text: 'var(--status-stable)' };
    if (accuracy <= 100) return { bg: 'var(--status-attention-bg)', border: 'var(--status-attention)', text: 'var(--status-attention)' };
    return { bg: 'var(--status-critical-bg)', border: 'var(--status-critical)', text: 'var(--status-critical)' };
  };

  return (
    <div style={{ marginBottom: 'var(--space-6)', fontFamily: 'var(--font-sans)' }}>
      <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Location (GPS)</label>
      
      {!location && !loading && (
        <button
          type="button"
          onClick={() => handleGetLocation(false)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 'var(--space-2)',
            width: '100%',
            padding: '12px',
            background: 'var(--surface-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-primary)',
            fontWeight: 500,
            fontSize: '14px',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <MapPin size={18} />
          Capture GPS Coordinates
        </button>
      )}

      {loading && (!location || location.accuracy > 100) && (
        <div style={{ padding: '16px', background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)', justifyContent: 'center' }}>
          <RefreshCw size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite', color: 'var(--brand-primary)' }} />
          <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)' }}>
            {location ? `Retrying GPS... (${retryCount}/${MAX_RETRIES})` : 'Acquiring GPS Signal...'}
          </span>
        </div>
      )}

      {location && (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <div style={{ 
            padding: '16px', 
            background: getAccuracyColor(location.accuracy).bg, 
            border: `1px solid ${getAccuracyColor(location.accuracy).border}`, 
            borderRadius: 'var(--radius-md)', 
            color: getAccuracyColor(location.accuracy).text, 
            display: 'flex', 
            flexDirection: 'column',
            gap: 'var(--space-3)' 
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <MapPin size={18} />
                <span style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                  {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
                </span>
              </div>
              <span style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                Accuracy: {Math.round(location.accuracy)}m
              </span>
            </div>
            
            <div style={{ fontSize: '11px', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-4)', opacity: 0.8, fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.02em' }}>
              <span>Alt: {location.altitude ? `${Math.round(location.altitude)}m` : 'N/A'}</span>
              <span>Time: {new Date(location.client_timestamp).toLocaleTimeString()}</span>
            </div>
          </div>

          {location.accuracy > 500 && !loading && (
            <div style={{ marginTop: 'var(--space-2)', padding: '16px', background: 'var(--surface-primary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
              <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><AlertTriangle size={16} color="var(--status-critical)" /> Location accuracy is insufficient</h3>
              <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>Current accuracy: {Math.round(location.accuracy)} m</p>
              <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>Move to a clearer location and try again.</p>
              
              <button
                type="button"
                onClick={() => handleGetLocation(false)}
                style={{ marginTop: '0.5rem', padding: '8px 16px', background: 'var(--surface-primary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', fontSize: '13px', cursor: 'pointer', fontWeight: 500, color: 'var(--text-primary)' }}
              >
                Retry Location
              </button>
            </div>
          )}
          
          {location.accuracy <= 500 && location.accuracy > 50 && !loading && (
            <button
                 type="button"
                 onClick={() => handleGetLocation(false)}
                 style={{
                   display: 'flex',
                   alignItems: 'center',
                   gap: '4px',
                   padding: '6px 12px',
                   fontSize: '12px',
                   fontWeight: 500,
                   background: 'transparent',
                   border: `1px solid var(--border-default)`,
                   borderRadius: 'var(--radius-sm)',
                   color: 'var(--text-secondary)',
                   cursor: 'pointer',
                   marginTop: '0.5rem'
                 }}
               >
                 <RefreshCw size={12} /> Retry Location
               </button>
          )}
        </div>
      )}

      {error && !location && (
        <div style={{ marginTop: 'var(--space-2)', padding: '16px', background: 'var(--surface-primary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
          <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><AlertTriangle size={16} color="var(--status-critical)" /> Unable to capture location</h3>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>Check location permissions and try again.</p>
          <button
             type="button"
             onClick={() => handleGetLocation(false)}
             style={{ marginTop: '0.5rem', padding: '8px 16px', background: 'var(--surface-primary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', fontSize: '13px', cursor: 'pointer', fontWeight: 500, color: 'var(--text-primary)' }}
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
