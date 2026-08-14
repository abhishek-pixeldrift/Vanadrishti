import React from 'react';

const MOCK_ACTIONS = [
  { id: 'a1', site: 'Goregaon MMRCL', issue: 'Vegetation loss reported', due: 'Today', owner: 'Field Team A', status: 'Pending' },
  { id: 'a2', site: 'Smriti Van', issue: 'Routine sensor maintenance', due: 'Tomorrow', owner: 'Tech Team', status: 'Scheduled' },
];

export default function FieldActions() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <h2 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Field Actions</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {MOCK_ACTIONS.map(action => (
          <div key={action.id} style={{
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-default)',
            background: 'var(--surface-primary)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)' }}>{action.site}</span>
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{action.due}</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>{action.issue}</p>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--space-1)' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>{action.owner}</span>
              <span className={`badge badge-${action.status === 'Pending' ? 'attention' : 'info'}`}>
                {action.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
