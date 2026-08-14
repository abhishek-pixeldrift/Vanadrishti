'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { NDVIObservation } from '@/lib/types';

interface NDVIChartProps {
  data: NDVIObservation[];
}

export default function NDVIChart({ data }: NDVIChartProps) {
  const chartData = data.map(d => {
    const dateObj = new Date(d.observation_date);
    return {
      date: dateObj.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
      rawDate: d.observation_date,
      ndvi: d.ndvi_value !== null ? Number(d.ndvi_value) : null,
      status: d.health_status,
    };
  });

  return (
    <div style={{ width: '100%', height: 350, fontFamily: 'var(--font-sans)' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{
            top: 5,
            right: 10,
            left: -20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 11, fill: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}
            tickMargin={12}
            axisLine={{ stroke: 'var(--border-default)' }}
            tickLine={false}
          />
          <YAxis 
            domain={[0, 1.0]} 
            tick={{ fontSize: 11, fill: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => value.toFixed(2)}
          />
          <Tooltip 
            contentStyle={{ borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', boxShadow: 'var(--shadow-md)', padding: 'var(--space-3)', background: 'var(--surface-primary)' }}
            labelStyle={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-1)', fontSize: '12px' }}
            itemStyle={{ fontSize: '13px', color: 'var(--brand-primary)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any) => [value !== null ? Number(value).toFixed(3) : 'Missing Data', 'NDVI Index']}
          />
          <ReferenceLine y={0.3} stroke="var(--status-critical)" strokeDasharray="3 4" label={{ position: 'insideBottomLeft', value: 'CRITICAL THRESHOLD (0.3)', fill: 'var(--status-critical)', fontSize: 10, fontWeight: 600, fontFamily: 'var(--font-mono)' }} />
          <Line 
            type="monotone" 
            dataKey="ndvi" 
            name="NDVI Value"
            stroke="var(--brand-primary)" 
            strokeWidth={2.5}
            dot={{ r: 3, strokeWidth: 1.5, fill: 'var(--surface-primary)', stroke: 'var(--brand-primary)' }}
            activeDot={{ r: 6, strokeWidth: 0, fill: 'var(--brand-hover)' }} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
