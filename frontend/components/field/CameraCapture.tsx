'use client';
import { useState, useRef } from 'react';
import { Camera } from 'lucide-react';

interface CameraCaptureProps {
  onImageCaptured: (file: File) => void;
}

export default function CameraCapture({ onImageCaptured }: CameraCaptureProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageCaptured(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div style={{ marginBottom: 'var(--space-6)', fontFamily: 'var(--font-sans)' }}>
      <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Plant Photo Evidence</label>
      
      <input
        type="file"
        accept="image/*"
        capture="environment" // Suggests mobile devices to use rear camera
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      
      {preview ? (
        <div style={{ position: 'relative', width: '100%', height: '300px', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-default)' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview} alt="Captured" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          <div style={{ position: 'absolute', bottom: 'var(--space-3)', right: 'var(--space-3)', display: 'flex', gap: 'var(--space-2)' }}>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              style={{ background: 'var(--surface-primary)', color: 'var(--text-primary)', padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontWeight: 500 }}
            >
              <Camera size={16} /> Retake/Replace
            </button>
          </div>
        </div>
      ) : (
        <button 
          type="button"
          onClick={() => fileInputRef.current?.click()}
          style={{ width: '100%', height: '200px', background: 'var(--surface-secondary)', border: '1px dashed var(--border-strong)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }}
        >
          <Camera size={40} strokeWidth={1.5} style={{ marginBottom: 'var(--space-4)' }} />
          <p style={{ margin: 0, fontWeight: 500, fontSize: '14px', color: 'var(--text-primary)' }}>Take Photo</p>
        </button>
      )}
    </div>
  );
}
