'use client';

import { useEffect, useState } from 'react';
import { fetchIncidents } from '@/lib/api';

/* eslint-disable @typescript-eslint/no-explicit-any */

function getRiskClass(risk: string) {
  const r = (risk || '').toLowerCase();
  if (r.includes('critical')) return 'badge-critical';
  if (r.includes('high')) return 'badge-high';
  if (r.includes('medium') || r.includes('warning')) return 'badge-medium';
  if (r.includes('low')) return 'badge-low';
  return 'badge-info';
}

export default function IncidentsPage() {
  // Backend: { count: N, data: [{ip, risk_level, severity, anomalies, correlations, logs, ai_analysis, created_at}] }
  const [incidents, setIncidents] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchIncidents();
        setIncidents(data.data || []);
        setTotal(data.count || 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load incidents');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Security Incidents</h2>
        <p>Browse and investigate detected security incidents ({total} total)</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading-spinner">
          <div className="spinner" />
          Loading incidents...
        </div>
      ) : incidents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🛡️</div>
          <h3>No incidents found</h3>
          <p>No security incidents have been recorded yet.</p>
        </div>
      ) : (
        <div className="glass-card">
          <div className="section-header">
            <h3 className="section-title">All Incidents</h3>
            <span className="section-badge">{total} total</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Source IP</th>
                <th>Risk Level</th>
                <th>Severity</th>
                <th>Anomalies</th>
                <th>Correlations</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc, idx) => {
                const isExpanded = expandedIdx === idx;
                return (
                  <>
                    <tr key={idx} onClick={() => setExpandedIdx(isExpanded ? null : idx)}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                        {inc.created_at ? new Date(inc.created_at + 'Z').toLocaleString() : '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{inc.ip || '—'}</td>
                      <td>
                        <span className={`badge ${getRiskClass(inc.risk_level || '')}`}>
                          {inc.risk_level || '—'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${getRiskClass(inc.severity || '')}`}>
                          {inc.severity || '—'}
                        </span>
                      </td>
                      <td>{Array.isArray(inc.anomalies) ? inc.anomalies.length : 0}</td>
                      <td>{Array.isArray(inc.correlations) ? inc.correlations.length : 0}</td>
                      <td style={{ fontSize: '0.75rem', color: 'var(--on-surface-variant)' }}>
                        {isExpanded ? '▲' : '▼'}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${idx}-detail`}>
                        <td colSpan={7} style={{ padding: '0 16px 16px' }}>
                          <div className="results-panel" style={{ marginTop: 0 }}>
                            {/* AI Analysis */}
                            {inc.ai_analysis && inc.ai_analysis.summary && inc.ai_analysis.summary !== 'Skipped for performance' && (
                              <div className="ai-insights" style={{ marginBottom: '16px' }}>
                                <h4>✨ AI Analysis</h4>
                                <p style={{ fontSize: '0.85rem', color: 'var(--on-surface-variant)' }}>{inc.ai_analysis.summary}</p>
                                {inc.ai_analysis.attack_narrative && (
                                  <p style={{ fontSize: '0.82rem', color: 'var(--on-surface-variant)', marginTop: '8px' }}>
                                    <strong>Attack Narrative:</strong> {inc.ai_analysis.attack_narrative}
                                  </p>
                                )}
                              </div>
                            )}
                            {/* Raw Logs */}
                            {Array.isArray(inc.logs) && inc.logs.length > 0 && (
                              <div style={{ marginBottom: '12px' }}>
                                <strong style={{ fontSize: '0.8rem', color: 'var(--on-surface-variant)' }}>Raw Logs:</strong>
                                <div className="log-feed" style={{ maxHeight: '200px', marginTop: '8px' }}>
                                  {inc.logs.map((log: string, i: number) => (
                                    <div key={i} className="log-entry" style={{ padding: '4px 8px' }}>
                                      <span className="log-message">{log}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {/* Full JSON */}
                            <details style={{ marginTop: '8px' }}>
                              <summary style={{ cursor: 'pointer', fontSize: '0.8rem', color: 'var(--outline)' }}>
                                View Full JSON
                              </summary>
                              <pre style={{
                                fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
                                color: 'var(--on-surface-variant)', whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word', marginTop: '8px',
                              }}>
                                {JSON.stringify(inc, null, 2)}
                              </pre>
                            </details>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
