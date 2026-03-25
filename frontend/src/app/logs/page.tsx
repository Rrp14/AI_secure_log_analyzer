'use client';

import { useEffect, useState, useCallback, Fragment } from 'react';
import { fetchLogs } from '@/lib/api';

/* eslint-disable @typescript-eslint/no-explicit-any */

function getRiskClass(risk: string) {
  const r = (risk || '').toLowerCase();
  if (r.includes('critical')) return 'badge-critical';
  if (r.includes('high')) return 'badge-high';
  if (r.includes('medium') || r.includes('warning')) return 'badge-medium';
  if (r.includes('low')) return 'badge-low';
  return 'badge-info';
}

const PAGE_SIZE = 20;

export default function LogsPage() {
  // Backend: { logs: [{_id, ip, content, risk_level, created_at}], total: N }
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ipFilter, setIpFilter] = useState('');
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [page, setPage] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLogs(limit, page * limit, ipFilter || undefined);
      setLogs(data.logs || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  }, [limit, page, ipFilter]);

  useEffect(() => { loadLogs(); }, [loadLogs]);

  function handleFilterSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(0);
    loadLogs();
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <>
      <div className="page-header">
        <h2>Log Explorer</h2>
        <p>Browse and filter historical log entries ({total.toLocaleString()} total)</p>
      </div>

      {/* Filter Bar */}
      <form className="filter-bar" onSubmit={handleFilterSubmit}>
        <input
          className="input"
          type="text"
          placeholder="Filter by IP address..."
          value={ipFilter}
          onChange={(e) => setIpFilter(e.target.value)}
          style={{ maxWidth: '240px' }}
        />
        <select
          className="select"
          value={limit}
          onChange={(e) => { setLimit(Number(e.target.value)); setPage(0); }}
          style={{ maxWidth: '160px' }}
        >
          <option value={10}>10 per page</option>
          <option value={20}>20 per page</option>
          <option value={50}>50 per page</option>
          <option value={100}>100 per page</option>
        </select>
        <button type="submit" className="btn btn-secondary btn-sm">🔍 Search</button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => { setIpFilter(''); setLimit(PAGE_SIZE); setPage(0); }}
        >
          ✕ Clear
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading-spinner">
          <div className="spinner" />
          Loading logs...
        </div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>No logs found</h3>
          <p>No log entries match the current filters.</p>
        </div>
      ) : (
        <>
          <div className="glass-card">
            <div className="section-header">
              <h3 className="section-title">Log Entries</h3>
              <span className="section-badge">{logs.length} of {total.toLocaleString()}</span>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Source IP</th>
                  <th>Risk Level</th>
                  <th>Content</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, idx) => {
                  const id = log._id || `log-${idx}-${Date.now()}`;
                  const isExpanded = expandedId === id;
                  return (
                    <Fragment key={id}>
                      <tr onClick={() => setExpandedId(isExpanded ? null : id)} style={{ cursor: 'pointer' }}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                          {log.created_at ? new Date(log.created_at + 'Z').toLocaleString() : '—'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>{log.ip || '—'}</td>
                        <td>
                          {log.risk_level ? (
                            <span className={`badge ${getRiskClass(log.risk_level)}`}>{log.risk_level}</span>
                          ) : '—'}
                        </td>
                        <td style={{
                          maxWidth: '500px', overflow: 'hidden',
                          textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          fontFamily: 'var(--font-mono)', fontSize: '0.8rem',
                        }}>
                          {log.content || '—'}
                        </td>
                        <td style={{ fontSize: '0.75rem', color: 'var(--on-surface-variant)' }}>
                          {isExpanded ? '▲' : '▼'}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={5} style={{ padding: '0 16px 16px' }}>
                            <div className="results-panel" style={{ marginTop: 0 }}>
                              <h3 style={{ fontSize: '0.9rem' }}>Full Log Content</h3>
                              <pre style={{
                                fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
                                color: 'var(--on-surface-variant)', whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                              }}>
                                {log.content}
                              </pre>
                              <div style={{ marginTop: '12px', fontSize: '0.78rem', color: 'var(--outline)' }}>
                                <span>ID: {log._id}</span>
                                {log.ip && <span> • IP: {log.ip}</span>}
                                {log.risk_level && <span> • Risk: {log.risk_level}</span>}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Previous</button>
            <button className="active">Page {page + 1} of {totalPages}</button>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>Next →</button>
          </div>
        </>
      )}
    </>
  );
}
