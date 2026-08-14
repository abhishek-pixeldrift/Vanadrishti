'use client';
import { useState } from 'react';
import { MapPin } from 'lucide-react';

interface GPSData {
  lat: number;
  lng: number;
  accuracy: number;
}

interface GPSLocatorProps {
  onLocationFound: (data: GPSData) => void;
}

export default function GPSLocator({ onLocationFound }: GPSLocatorProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState<GPSData | null>(null);

  const handleGetLocation = () => {
    setLoading(true);
    setError(null);
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const data = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy,
        };
        setLocation(data);
        onLocationFound(data);
        setLoading(false);
      },
      (err) => {
        setError(err.message);
        setLoading(false);
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
    );
  };

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Location (GPS)</label>
      {location ? (
        <div style={{ padding: '1rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#166534', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MapPin size={20} />
          <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>
            {location.lat.toFixed(6)}, {location.lng.toFixed(6)} (±{Math.round(location.accuracy)}m)
          </span>
        </div>
      ) : (
        <button
          type="button"
          onClick={handleGetLocation}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            width: '100%',
            padding: '0.75rem',
            background: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            borderRadius: '8px',
            color: 'var(--foreground)',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          <MapPin size={20} />
          {loading ? 'Locating...' : 'Capture GPS Coordinates'}
        </button>
      )}
      {error && (
        <div style={{ marginTop: '0.5rem' }}>
          <p style={{ color: '#ef4444', fontSize: '0.75rem', marginBottom: '0.5rem' }}>{error}</p>
          <button
            type="button"
            onClick={() => {
              const mockData = { lat: 19.9975, lng: 73.7898, accuracy: 5 }; // Mock coordinates
              setLocation(mockData);
              onLocationFound(mockData);
              setError(null);
            }}
            style={{
              padding: '0.5rem 1rem',
              background: 'var(--background)',
              border: '1px solid var(--card-border)',
              borderRadius: '6px',
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Use Mock GPS Data (Dev Mode)
          </button>
        </div>
      )}
    </div>
  );
}
