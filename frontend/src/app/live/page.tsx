'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { startProducer, stopProducer, getProducerStatus, fetchIncidents, WS_LIVE_LOGS_URL } from '@/lib/api';

/* eslint-disable @typescript-eslint/no-explicit-any */

function getRiskClass(risk: string) {
  const r = (risk || '').toLowerCase();
  if (r.includes('critical')) return 'badge-critical';
  if (r.includes('high')) return 'badge-high';
  if (r.includes('medium') || r.includes('warning')) return 'badge-medium';
  if (r.includes('low')) return 'badge-low';
  return 'badge-info';
}

interface LiveEntry {
  id: string;
  timestamp: string;
  ip: string;
  risk_level: string;
  severity: string;
  anomalies: any[];
  correlations: any[];
  log: string;
  ai_summary: string;
  source: 'ws' | 'poll';
}

export default function LiveDemoPage() {
  const [producerRunning, setProducerRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [liveEntries, setLiveEntries] = useState<LiveEntry[]>([]);
  const [demoActive, setDemoActive] = useState(false);

  // WebSocket state
  const wsRef = useRef<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsAttempted, setWsAttempted] = useState(false);
  const [wsUnavailable, setWsUnavailable] = useState(false);

  // Polling state
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const seenIdsRef = useRef<Set<string>>(new Set());
  const [pollCount, setPollCount] = useState(0);

  // Check producer status on mount
  useEffect(() => {
    getProducerStatus()
      .then((data) => setProducerRunning(data.status === 'running'))
      .catch(() => {});
  }, []);

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [liveEntries, autoScroll]);

  // ── WebSocket connection ──
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setWsAttempted(true);

    try {
      const ws = new WebSocket(WS_LIVE_LOGS_URL);

      const timeoutId = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close();
          setWsUnavailable(true);
        }
      }, 5000);

      ws.onopen = () => {
        clearTimeout(timeoutId);
        setWsConnected(true);
        setWsUnavailable(false);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const entry: LiveEntry = {
            id: `ws-${Date.now()}-${Math.random()}`,
            timestamp: data.timestamp || new Date().toISOString(),
            ip: data.ip || '—',
            risk_level: data.risk_level || 'info',
            severity: data.severity || data.risk_level || 'info',
            anomalies: data.anomalies || [],
            correlations: data.correlations || [],
            log: data.log || data.message || JSON.stringify(data),
            ai_summary: data.ai_analysis?.summary || '',
            source: 'ws',
          };
          setLiveEntries(prev => [...prev.slice(-200), entry]);
        } catch {
          // raw text message
          setLiveEntries(prev => [...prev.slice(-200), {
            id: `ws-${Date.now()}`,
            timestamp: new Date().toISOString(),
            ip: '—', risk_level: 'info', severity: 'info',
            anomalies: [], correlations: [],
            log: event.data, ai_summary: '', source: 'ws',
          }]);
        }
      };

      ws.onerror = () => {
        clearTimeout(timeoutId);
        setWsUnavailable(true);
      };

      ws.onclose = () => {
        setWsConnected(false);
      };

      wsRef.current = ws;
    } catch {
      setWsUnavailable(true);
    }
  }, []);

  const disconnectWs = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setWsConnected(false);
  }, []);

  // ── Polling fallback ──
  const startPolling = useCallback(() => {
    if (pollingRef.current) return;

    // Initial load of existing incidents to seed "seen" set
    fetchIncidents().then(data => {
      (data.data || []).forEach((inc: any) => {
        const incId = inc.created_at + inc.ip;
        seenIdsRef.current.add(incId);
      });
    }).catch(() => {});

    pollingRef.current = setInterval(async () => {
      try {
        const data = await fetchIncidents();
        const incidents = data.data || [];
        const newEntries: LiveEntry[] = [];

        for (const inc of incidents) {
          const incId = inc.created_at + inc.ip;
          if (!seenIdsRef.current.has(incId)) {
            seenIdsRef.current.add(incId);
            // Expand each log line in the incident as a separate feed entry
            const logs: string[] = inc.logs || [];
            if (logs.length > 0) {
              for (const logLine of logs) {
                newEntries.push({
                  id: `poll-${incId}-${Math.random()}`,
                  timestamp: inc.created_at || new Date().toISOString(),
                  ip: inc.ip || '—',
                  risk_level: inc.risk_level || 'info',
                  severity: inc.severity || inc.risk_level || 'info',
                  anomalies: inc.anomalies || [],
                  correlations: inc.correlations || [],
                  log: logLine,
                  ai_summary: inc.ai_analysis?.summary || '',
                  source: 'poll',
                });
              }
            } else {
              newEntries.push({
                id: `poll-${incId}`,
                timestamp: inc.created_at || new Date().toISOString(),
                ip: inc.ip || '—',
                risk_level: inc.risk_level || 'info',
                severity: inc.severity || inc.risk_level || 'info',
                anomalies: inc.anomalies || [],
                correlations: inc.correlations || [],
                log: `Incident detected from ${inc.ip}`,
                ai_summary: inc.ai_analysis?.summary || '',
                source: 'poll',
              });
            }
          }
        }

        if (newEntries.length > 0) {
          setLiveEntries(prev => [...prev.slice(-200), ...newEntries]);
          setPollCount(prev => prev + newEntries.length);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 4000); // Poll every 4 seconds
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWs();
      stopPolling();
    };
  }, [disconnectWs, stopPolling]);

  // ── Demo control ──
  const handleStart = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await startProducer();
      setProducerRunning(true);
      setDemoActive(true);

      // Try WebSocket first
      connectWs();

      // Always start polling as fallback/complement
      setTimeout(() => startPolling(), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start producer');
    } finally {
      setLoading(false);
    }
  }, [connectWs, startPolling]);

  const handleStop = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await stopProducer();
      setProducerRunning(false);
      setDemoActive(false);
      disconnectWs();
      stopPolling();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop producer');
    } finally {
      setLoading(false);
    }
  }, [disconnectWs, stopPolling]);

  function handleScroll() {
    if (!feedRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = feedRef.current;
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 50);
  }

  const connectionMode = wsConnected ? 'WebSocket' : (demoActive ? 'Polling' : 'Disconnected');

  return (
    <>
      <div className="page-header">
        <h2>Live Demo</h2>
        <p>Real-time log analysis stream — Kafka → AI Pipeline → WebSocket + Polling</p>
      </div>

      {/* Status & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
        {/* Producer Status */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          background: 'var(--surface-container)', padding: '10px 20px',
          borderRadius: 'var(--radius-md)',
        }}>
          <span className={`status-dot ${producerRunning ? 'online' : 'offline'}`} />
          <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>
            Producer: {producerRunning ? 'Running' : 'Stopped'}
          </span>
        </div>

        {/* Connection Status */}
        <div className={`connection-status ${wsConnected ? 'connected' : demoActive ? 'connected' : 'disconnected'}`}>
          {wsConnected && '🔗 WebSocket'}
          {!wsConnected && demoActive && '📡 Polling Mode'}
          {!wsConnected && !demoActive && '⛓️‍💥 Disconnected'}
        </div>

        {wsAttempted && wsUnavailable && (
          <div style={{ fontSize: '0.75rem', color: 'var(--severity-medium)', maxWidth: '250px' }}>
            ⚠️ WebSocket unavailable — using polling fallback
          </div>
        )}

        <div style={{ flex: 1 }} />

        {/* Controls */}
        <button className="btn btn-secondary" onClick={handleStart} disabled={loading || demoActive}>
          {loading ? '⏳ Starting...' : '▶ Start Demo'}
        </button>
        <button className="btn btn-danger" onClick={handleStop} disabled={loading || !demoActive}>
          ⏹ Stop Demo
        </button>
        <button className="btn btn-ghost btn-sm" onClick={() => { setLiveEntries([]); setPollCount(0); }}>
          🗑️ Clear
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Info Banner */}
      {demoActive && !wsConnected && wsUnavailable && (
        <div style={{
          background: 'rgba(255, 165, 2, 0.08)', border: '1px solid rgba(255, 165, 2, 0.2)',
          borderRadius: 'var(--radius-md)', padding: '12px 20px', marginBottom: '20px',
          fontSize: '0.82rem', color: 'var(--severity-medium)',
        }}>
          📡 <strong>Polling Mode Active</strong> — New incidents appear as the Kafka consumer processes logs.
          WebSocket is unavailable (network/firewall restriction). The feed refreshes every ~4 seconds.
        </div>
      )}

      {/* Log Feed */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden', position: 'relative' }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid rgba(70, 69, 85, 0.15)',
        }}>
          <h3 className="section-title" style={{ margin: 0, fontSize: '1rem' }}>
            ⚡ Real-Time Feed
          </h3>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <span className="section-badge">{liveEntries.length} entries</span>
            <span className="section-badge">{connectionMode}</span>
          </div>
        </div>

        <div
          ref={feedRef}
          className="log-feed"
          onScroll={handleScroll}
          style={{
            borderRadius: 0,
            maxHeight: '550px',
            minHeight: '400px',
          }}
        >
          {liveEntries.length === 0 ? (
            <div className="empty-state" style={{ padding: '100px 32px' }}>
              <div className="empty-icon">📡</div>
              <h3>{demoActive ? 'Waiting for new incidents...' : 'Waiting for data...'}</h3>
              <p>{demoActive
                ? 'The producer is running. New incidents will appear as the AI pipeline detects threats.'
                : 'Click "Start Demo" to begin the real-time log producer and analysis pipeline.'
              }</p>
            </div>
          ) : (
            liveEntries.map((entry) => (
              <div className="log-entry" key={entry.id} style={{
                borderLeft: `3px solid ${
                  entry.severity === 'critical' ? 'var(--severity-critical)' :
                  entry.severity === 'high' ? 'var(--severity-high)' :
                  entry.severity === 'medium' ? 'var(--severity-medium)' :
                  'var(--severity-low)'
                }`,
              }}>
                <span className="log-timestamp" style={{ minWidth: '80px' }}>
                  {new Date(entry.timestamp + 'Z').toLocaleTimeString()}
                </span>
                <span className={`badge ${getRiskClass(entry.severity)}`} style={{ flexShrink: 0 }}>
                  {entry.severity}
                </span>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
                  color: 'var(--on-surface-variant)', flexShrink: 0,
                  minWidth: '120px',
                }}>
                  {entry.ip}
                </span>
                {entry.anomalies.length > 0 && (
                  <span style={{ display: 'flex', gap: '3px', flexShrink: 0 }}>
                    {entry.anomalies.map((a: any, i: number) => (
                      <span key={i} className={`badge ${getRiskClass(a.risk || 'medium')}`}
                        style={{ fontSize: '0.6rem', padding: '1px 6px' }}>
                        {(a.type || '').replace(/_/g, ' ')}
                      </span>
                    ))}
                  </span>
                )}
                <span className="log-message">{entry.log}</span>
              </div>
            ))
          )}
        </div>

        {/* Scroll to bottom FAB */}
        {!autoScroll && liveEntries.length > 0 && (
          <button
            onClick={() => {
              if (feedRef.current) {
                feedRef.current.scrollTop = feedRef.current.scrollHeight;
                setAutoScroll(true);
              }
            }}
            style={{
              position: 'absolute', bottom: '24px', right: '24px',
              background: 'var(--primary-container)', color: 'var(--on-primary)',
              border: 'none', borderRadius: 'var(--radius-full)',
              padding: '10px 16px', fontSize: '0.8rem', fontWeight: 500,
              cursor: 'pointer', zIndex: 10,
              boxShadow: '0 4px 20px rgba(135, 129, 255, 0.3)',
            }}
          >
            ↓ Scroll to Bottom
          </button>
        )}
      </div>

      {/* AI Summary Panel (show latest AI-analyzed incident) */}
      {liveEntries.filter(e => e.ai_summary).length > 0 && (
        <div className="ai-insights" style={{ marginTop: '24px' }}>
          <h4>✨ Latest AI Threat Analysis</h4>
          <p style={{ color: 'var(--on-surface)', fontSize: '0.88rem', lineHeight: 1.7 }}>
            {liveEntries.filter(e => e.ai_summary).slice(-1)[0]?.ai_summary}
          </p>
        </div>
      )}
    </>
  );
}
