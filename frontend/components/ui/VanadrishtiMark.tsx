import React from 'react';

export default function VanadrishtiMark({ size = 24, className = "" }: { size?: number, className?: string }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
      className={className}
      style={{ color: 'var(--brand-primary)' }}
    >
      {/* Top Right Viewfinder */}
      <path d="M15 3h6v6" />
      {/* Bottom Left Viewfinder */}
      <path d="M9 21H3v-6" />
      
      {/* Terrain Contour */}
      <path d="M3 14c4 0 6-3 10-3s5 3 8 3" strokeWidth="1.5" />
      <path d="M3 18c5 0 7-4 12-4s4 2 6 2" strokeWidth="1.5" opacity="0.6" />
    </svg>
  );
}
