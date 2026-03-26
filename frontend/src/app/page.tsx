'use client';

import { useEffect, useState } from 'react';
import {  fetchIncidents, fetchLogs,startProducer, stopProducer, getProducerStatus } from '@/lib/api';

import Link from 'next/link';

/* eslint-disable @typescript-eslint/no-explicit-any */

function getRiskClass(risk: string) {
  const r = (risk || '').toLowerCase();
  if (r.includes('critical')) return 'badge-critical';
  if (r.includes('high')) return 'badge-high';
  if (r.includes('medium') || r.includes('warning')) return 'badge-medium';
  if (r.includes('low')) return 'badge-low';
  return 'badge-info';
}

export default function DashboardPage() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [incidentCount, setIncidentCount] = useState(0);
  const [logTotal, setLogTotal] = useState(0);
  const [producerStatus, setProducerStatus] = useState('unknown');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [incRes, logRes, statusRes] = await Promise.allSettled([
          fetchIncidents(),
          fetchLogs(1),
          getProducerStatus(),
        ]);
        if (incRes.status === 'fulfilled') {
          setIncidents(incRes.value.data || []);
          setIncidentCount(incRes.value.count || 0);
        }
        if (logRes.status === 'fulfilled') {
          setLogTotal(logRes.value.total || 0);
        }
        if (statusRes.status === 'fulfilled') {
          setProducerStatus(statusRes.value.status || 'stopped');
        }
      } catch (e) {
        console.error('Dashboard load error:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // ── Compute ALL stats from real incident data ──
  const criticalCount = incidents.filter(i => (i.severity || '').toLowerCase() === 'critical').length;
  const highCount = incidents.filter(i => (i.severity || '').toLowerCase() === 'high').length;
  const mediumCount = incidents.filter(i => (i.severity || '').toLowerCase() === 'medium').length;

  // Unique attacker IPs
  const uniqueIps = [...new Set(incidents.map(i => i.ip).filter(Boolean).filter((ip: string) => ip !== 'unknown'))];

  // Aggregate anomaly types across all incidents
  const anomalyMap: Record<string, number> = {};
  incidents.forEach(i => {
    (i.anomalies || []).forEach((a: any) => {
      anomalyMap[a.type] = (anomalyMap[a.type] || 0) + 1;
    });
  });

  // Correlation types
  const correlationCount = incidents.reduce((sum: number, i: any) => sum + (i.correlations?.length || 0), 0);

  // Incidents with AI analysis
  const aiAnalyzedCount = incidents.filter(i => i.ai_analysis?.summary && i.ai_analysis.summary.length > 0).length;

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
        Loading dashboard...
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Security operations overview — real-time data from AI analysis pipeline</p>
      </div>

      {/* ── Stat Cards (all computed from real data) ── */}
      <div className="stats-grid">
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(135, 129, 255, 0.15)', color: '#8781ff' }}>🚨</div>
          <div className="stat-value" style={{ color: 'var(--primary)' }}>{incidentCount}</div>
          <div className="stat-label">Total Incidents</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(255, 71, 87, 0.15)', color: '#ff4757' }}>⚠️</div>
          <div className="stat-value" style={{ color: 'var(--severity-critical)' }}>{criticalCount}</div>
          <div className="stat-label">Critical Severity</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(255, 107, 53, 0.15)', color: '#ff6b35' }}>🔥</div>
          <div className="stat-value" style={{ color: 'var(--severity-high)' }}>{highCount}</div>
          <div className="stat-label">High Severity</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(0, 210, 253, 0.15)', color: '#00d2fd' }}>📋</div>
          <div className="stat-value" style={{ color: 'var(--secondary)' }}>{logTotal.toLocaleString()}</div>
          <div className="stat-label">Logs Recorded</div>
        </div>
      </div>

      {/* ── Threat Intelligence Summary ── */}
      <div className="stats-grid" style={{ marginBottom: '32px' }}>
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(255, 165, 2, 0.15)', color: '#ffa502' }}>🌐</div>
          <div className="stat-value" style={{ color: 'var(--severity-medium)' }}>{uniqueIps.length}</div>
          <div className="stat-label">Unique Attacker IPs</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(255, 165, 2, 0.12)', color: '#ffa502' }}>🎯</div>
          <div className="stat-value" style={{ color: 'var(--severity-medium)' }}>{mediumCount}</div>
          <div className="stat-label">Medium Severity</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(46, 213, 115, 0.15)', color: '#2ed573' }}>🔗</div>
          <div className="stat-value" style={{ color: 'var(--severity-low)' }}>{correlationCount}</div>
          <div className="stat-label">Attack Correlations</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ background: 'rgba(135, 129, 255, 0.12)', color: '#c4c0ff' }}>✨</div>
          <div className="stat-value" style={{ color: 'var(--primary)' }}>{aiAnalyzedCount}</div>
          <div className="stat-label">AI Analyzed</div>
        </div>
      </div>

      {/* ── Anomaly Breakdown ── */}
      {Object.keys(anomalyMap).length > 0 && (
        <div style={{ marginBottom: '32px' }}>
          <div className="section-header">
            <h3 className="section-title">Detected Anomaly Types</h3>
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {Object.entries(anomalyMap)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <div key={type} className="glass-card" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className={`badge ${type === 'destructive_command' ? 'badge-critical' : type === 'brute_force' ? 'badge-high' : 'badge-medium'}`}>
                    {type.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>{count}</span>
                </div>
              ))
            }
          </div>
        </div>
      )}

      {/* ── Quick Actions ── */}
      <div style={{ marginBottom: '32px' }}>
        <div className="section-header">
          <h3 className="section-title">Quick Actions</h3>
          <span className={`connection-status ${producerStatus === 'running' ? 'connected' : 'disconnected'}`}>
            Producer: {producerStatus}
          </span>
        </div>
        <div className="quick-actions">
          <Link href="/live"><button className="btn btn-secondary">⚡ Live Demo</button></Link>
          <Link href="/analyze"><button className="btn btn-primary">🔍 Analyze Logs</button></Link>
          <Link href="/incidents"><button className="btn btn-ghost">🚨 View All Incidents</button></Link>
          <Link href="/logs"><button className="btn btn-ghost">📋 Browse Logs</button></Link>
        </div>
      </div>

      {/* ── Unique Attacker IPs ── */}
      {uniqueIps.length > 0 && (
        <div className="glass-card" style={{ marginBottom: '24px' }}>
          <div className="section-header">
            <h3 className="section-title">Attacker IP Addresses</h3>
            <span className="section-badge">{uniqueIps.length} unique</span>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {uniqueIps.map((ip: string) => {
              const ipIncidents = incidents.filter(i => i.ip === ip);
              const worstSeverity = ipIncidents.some(i => (i.severity || '').toLowerCase() === 'critical') ? 'critical'
                : ipIncidents.some(i => (i.severity || '').toLowerCase() === 'high') ? 'high' : 'medium';
              return (
                <div key={ip} style={{
                  background: 'var(--surface-container-high)', padding: '8px 16px',
                  borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '10px',
                }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 500 }}>{ip}</span>
                  <span className={`badge ${getRiskClass(worstSeverity)}`}>{ipIncidents.length} incidents</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Recent Incidents (real data) ── */}
      <div className="glass-card">
        <div className="section-header">
          <h3 className="section-title">Recent Security Incidents</h3>
          <Link href="/incidents">
            <span className="section-badge" style={{ cursor: 'pointer' }}>View All →</span>
          </Link>
        </div>
        {incidents.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Source IP</th>
                <th>Severity</th>
                <th>Anomalies</th>
                <th>AI Summary</th>
              </tr>
            </thead>
            <tbody>
              {incidents.slice(0, 8).map((inc, idx) => (
                <tr key={idx}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                    {inc.created_at ? new Date(inc.created_at + 'Z').toLocaleString() : '—'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{inc.ip || '—'}</td>
                  <td>
                    <span className={`badge ${getRiskClass(inc.severity || '')}`}>{inc.severity || '—'}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {(inc.anomalies || []).map((a: any, i: number) => (
                        <span key={i} className={`badge ${getRiskClass(a.risk || 'medium')}`} style={{ fontSize: '0.6rem', padding: '2px 8px' }}>
                          {(a.type || '').replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ maxWidth: '350px', fontSize: '0.8rem', color: 'var(--on-surface-variant)' }}>
                    {inc.ai_analysis?.summary
                      ? (inc.ai_analysis.summary.length > 120
                        ? inc.ai_analysis.summary.slice(0, 120) + '...'
                        : inc.ai_analysis.summary)
                      : <span style={{ opacity: 0.4 }}>—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">🛡️</div>
            <h3>No incidents found</h3>
            <p>Start the live demo producer to generate real-time security incidents.</p>
          </div>
        )}
      </div>
    </>
  );
}
