import { Plantation, DashboardStats, NDVIObservation, FieldVisit, AIVerification, Alert, RiskResult } from './types';

const getBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
};

const API_BASE_URL = getBaseUrl();

export async function getPlantations(): Promise<Plantation[]> {
  const res = await fetch(`${API_BASE_URL}/plantations/`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error('Failed to fetch plantations');
  }
  
  const plantations: Plantation[] = await res.json();
  
  // Fetch boundary for each plantation using the backend endpoint
  const withBoundaries = await Promise.all(plantations.map(async (p) => {
    try {
      const bRes = await fetch(`${API_BASE_URL}/plantations/${p.id}/boundary`, { cache: 'no-store' });
      if (bRes.ok) {
        const bData = await bRes.json();
        p.boundary_status = bData.boundary_status;
        p.boundary_geojson = bData.boundary;
      }
    } catch {
      console.warn(`Could not fetch boundary for ${p.id}`);
    }
    return p;
  }));
  
  return withBoundaries;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE_URL}/plantations/stats`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error('Failed to fetch dashboard stats');
  }
  return res.json();
}

export async function getPlantation(id: string): Promise<Plantation> {
  const res = await fetch(`${API_BASE_URL}/plantations/${id}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch plantation ${id}`);
  }
  return res.json();
}

export interface NDVIMetadata {
  dataSource: string;
  fallbackUsed: boolean;
  failureReason: string | null;
}

export interface NDVIResponse {
  data: NDVIObservation[];
  metadata: NDVIMetadata;
}

export async function getNDVIObservations(plantationId: string): Promise<NDVIResponse> {
  const res = await fetch(`${API_BASE_URL}/ndvi/${plantationId}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch NDVI observations for ${plantationId}`);
  }
  
  const data = await res.json();
  
  return {
    data,
    metadata: {
      dataSource: res.headers.get('x-data-source') || 'seed',
      fallbackUsed: res.headers.get('x-fallback-used') === 'true',
      failureReason: res.headers.get('x-failure-reason') || null,
    }
  };
}

export async function submitFieldVisit(formData: FormData): Promise<FieldVisit> {
  const res = await fetch(`${API_BASE_URL}/field-visits/`, {
    method: 'POST',
    body: formData, // Don't set Content-Type header, browser sets it automatically with boundary for FormData
  });
  if (!res.ok) {
    throw new Error('Failed to submit field visit');
  }
  return res.json();
}

export async function verifyFieldVisit(visitId: string): Promise<AIVerification> {
  const res = await fetch(`${API_BASE_URL}/field-visits/${visitId}/verify`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to run AI verification');
  }
  return res.json();
}

export async function getAlerts(): Promise<Alert[]> {
  const res = await fetch(`${API_BASE_URL}/alerts/`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error('Failed to fetch alerts');
  }
  return res.json();
}

export async function getLastVerifiedVisit(plantationId: string): Promise<FieldVisit | null> {
  const res = await fetch(`${API_BASE_URL}/plantations/${plantationId}/last-verified-visit`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`Failed to fetch last verified visit for ${plantationId}`);
  }
  const data = await res.text();
  return data ? JSON.parse(data) : null;
}

export async function getActiveAlerts(plantationId: string): Promise<Alert[]> {
  const res = await fetch(`${API_BASE_URL}/plantations/${plantationId}/active-alerts`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch active alerts for ${plantationId}`);
  }
  return res.json();
}

export async function acknowledgeAlert(alertId: string): Promise<unknown> {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to acknowledge alert');
  }
  return res.json();
}

export async function triggerRiskEngineScan(): Promise<{ status: string; new_alerts: number }> {
  const res = await fetch(`${API_BASE_URL}/alerts/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to run Risk Engine');
  }
  return res.json();
}

export async function getRiskScore(plantationId: string): Promise<RiskResult> {
  const res = await fetch(`${API_BASE_URL}/risk/${plantationId}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch risk score for ${plantationId}`);
  }
  return res.json();
}
