'use client';

import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-defaulticon-compatibility';
import 'leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css';
import { Plantation } from '@/lib/types';
import L from 'leaflet';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import styles from './Map.module.css';

interface PlantationMapProps {
  plantations: Plantation[];
}

const STATUS_COLORS = {
  healthy: '#3D7A5F',
  warning: '#B47A2C',
  critical: '#A04040',
  demo: '#6F6B64'
};

const getMarkerIcon = (status: string, siteClass?: string) => {
  let color = STATUS_COLORS.healthy;
  if (siteClass === 'synthetic_demo') {
    color = STATUS_COLORS.demo;
  } else if (status === 'warning') {
    color = STATUS_COLORS.warning;
  } else if (status === 'critical') {
    color = STATUS_COLORS.critical;
  }
  
  const svgIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <!-- White halo for high contrast against satellite map -->
      <rect x="3" y="3" width="18" height="18" rx="2" transform="rotate(45 12 12)" fill="white" opacity="0.3"/>
      <!-- Main diamond marker -->
      <rect x="4" y="4" width="16" height="16" rx="2" transform="rotate(45 12 12)" fill="${color}" fill-opacity="0.95" stroke="#ffffff" stroke-width="2"/>
      <!-- Center dot -->
      <circle cx="12" cy="12" r="3.5" fill="#ffffff"/>
    </svg>
  `;
  
  return L.divIcon({
    html: svgIcon,
    className: 'custom-svg-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
};

function MapLegend() {
  return (
    <div className={styles.legend}>
      <div className={styles.legendItem}>
        <div className={styles.legendMarker} style={{ borderColor: STATUS_COLORS.healthy }}></div>
        <span>Stable</span>
      </div>
      <div className={styles.legendItem}>
        <div className={styles.legendMarker} style={{ borderColor: STATUS_COLORS.warning }}></div>
        <span>Attention</span>
      </div>
      <div className={styles.legendItem}>
        <div className={styles.legendMarker} style={{ borderColor: STATUS_COLORS.critical }}></div>
        <span>Critical</span>
      </div>
      <div className={styles.legendItem}>
        <div className={styles.legendMarker} style={{ borderColor: STATUS_COLORS.demo, borderStyle: 'dashed' }}></div>
        <span>Demonstration</span>
      </div>
    </div>
  );
}

function PlantationLayer({ p }: { p: Plantation }) {
  const map = useMap();
  
  const handleMarkerClick = () => {
    map.flyTo([p.latitude, p.longitude], 16, { duration: 0.8 });
  };
  
  const handleGeoJSONClick = (e: unknown) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const event = e as any;
    if (event.layer && event.layer.getBounds) {
      map.flyToBounds(event.layer.getBounds(), { maxZoom: 18, duration: 0.8 });
    }
  };

  const getBoundaryStyle = () => {
    const style: L.PathOptions = { color: '#3B6B8A', weight: 1.5, fillOpacity: 0.08, fillColor: '#3B6B8A' };
    
    if (p.site_class === 'synthetic_demo') {
      style.color = '#8B8680';
      style.weight = 1;
      style.dashArray = '3, 3';
      style.fillOpacity = 0;
    } else if (p.boundary_status === 'mvp_proxy') {
      style.color = '#9A6D38';
      style.dashArray = '6, 4';
      style.fillOpacity = 0;
    }
    
    return style;
  };

  return (
    <>
      {p.boundary_geojson && (
        <GeoJSON 
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          data={p.boundary_geojson as any} 
          style={getBoundaryStyle()}
          eventHandlers={{
            click: handleGeoJSONClick,
            mouseover: (e) => {
              const layer = e.target;
              if (p.site_class !== 'synthetic_demo') {
                layer.setStyle({
                  weight: 2.5,
                  fillOpacity: p.boundary_status === 'mvp_proxy' ? 0.08 : 0.15,
                  fillColor: p.boundary_status === 'mvp_proxy' ? '#9A6D38' : '#3B6B8A'
                });
              }
            },
            mouseout: (e) => {
              const layer = e.target;
              layer.setStyle(getBoundaryStyle());
            }
          }}
        />
      )}
      <Marker 
        position={[p.latitude, p.longitude]} 
        icon={getMarkerIcon(p.status, p.site_class)}
        eventHandlers={{
          click: handleMarkerClick,
          mouseover: function(e) {
            const icon = e.target.getElement();
            if (icon) {
              icon.style.transform = icon.style.transform.replace(/scale\([^)]*\)/, '') + ' scale(1.2)';
            }
          },
          mouseout: function(e) {
            const icon = e.target.getElement();
            if (icon) {
              icon.style.transform = icon.style.transform.replace(/scale\([^)]*\)/, '');
            }
          }
        }}
      >
        <Popup className={styles.customPopup}>
          <div className={styles.popupContent}>
            <h3 className={styles.popupTitle}>{p.name}</h3>
            <div className={styles.popupLocation}>{p.district}, {p.state}</div>
            
            <div className={styles.statusWrapper}>
                <div className={`${styles.statusDot} ${p.status === 'healthy' ? styles.statusHealthyDot : p.status === 'warning' ? styles.statusWarningDot : styles.statusCriticalDot}`}></div>
                <span className={styles.statusLabel}>
                    {p.status === 'healthy' ? 'Stable' : p.status === 'warning' ? 'Attention' : 'Critical'}
                </span>
            </div>
            
            <p className={styles.statsText}>{p.area_hectares} ha</p>

            {p.boundary_status === 'mvp_proxy' && p.site_class !== 'synthetic_demo' && (
              <div className={`${styles.badge} ${styles.badgeProxy}`}>
                Traced Boundary
              </div>
            )}
            
            {p.site_class === 'synthetic_demo' && (
              <div className={`${styles.badge} ${styles.badgeDemo}`}>
                Demonstration Site
              </div>
            )}
            
            <Link href={`/plantations/${p.id}`} className={styles.detailsLink}>
                Open Site <ArrowRight size={14} />
            </Link>
          </div>
        </Popup>
      </Marker>
    </>
  );
}

function MapBounds({ plantations }: { plantations: Plantation[] }) {
  const map = useMap();
  
  useEffect(() => {
    if (plantations.length === 0) return;
    const bounds = L.latLngBounds(plantations.map(p => [p.latitude, p.longitude]));
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
  }, [plantations, map]);

  useEffect(() => {
    const container = map.getContainer();
    if (!container) return;
    
    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize();
    });
    
    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, [map]);

  return null;
}

export default function PlantationMap({ plantations }: PlantationMapProps) {
  const center: [number, number] = [19.5, 73.5];

  return (
    <div className={styles.mapWrapper}>
      <MapContainer 
        center={center} 
        zoom={9} 
        scrollWheelZoom={true} 
        className={styles.mapContainer}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />
        
        <MapBounds plantations={plantations} />
        <MapLegend />
        
        {plantations.map(p => (
          <PlantationLayer key={p.id} p={p} />
        ))}
      </MapContainer>
    </div>
  );
}
