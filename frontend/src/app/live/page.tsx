'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { startProducer, stopProducer, getProducerStatus, WS_LIVE_LOGS_URL } from '@/lib/api';

/* eslint-disable @typescript-eslint/no-explicit-any */

// Each WebSocket message from consumer.py:
interface LiveEntry {
  id: string;
  timestamp: string;
  ip: string;
  risk_level: string;
  anomalies: any[];
  correlations: any[];
  log: string;
  action: string;
  ai_summary: string;
}

export default function LiveDemoPage() {
  const [producerRunning, setProducerRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [liveEntries, setLiveEntries] = useState<LiveEntry[]>([]);
  const [demoActive, setDemoActive] = useState(false);
  const [warmupProgress, setWarmupProgress] = useState(0);

  // WebSocket
  const wsRef = useRef<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const demoActiveRef = useRef(false);

  useEffect(() => {
    demoActiveRef.current = demoActive;
  }, [demoActive]);

  useEffect(() => {
    getProducerStatus().then((data) => {
      const running = data.status === 'running';
      setProducerRunning(running);
      if (running) setDemoActive(true);
    });
  }, []);

  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [liveEntries, autoScroll]);

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    try {
      const ws = new WebSocket(WS_LIVE_LOGS_URL);
      ws.onopen = () => { setWsConnected(true); setError(null); };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Track warmup (estimate based on entry count if backend doesn't send it)
          setWarmupProgress(prev => Math.min(100, prev + 1));

          const entry: LiveEntry = {
            id: data.id || `ws-${Date.now()}-${Math.random()}`,
            timestamp: data.timestamp || new Date().toISOString(),
            ip: data.ip || '—',
            risk_level: data.risk_level || 'low',
            anomalies: data.anomalies || [],
            correlations: data.correlations || [],
            log: data.log || '',
            action: data.action || 'allowed',
            ai_summary: data.ai_analysis?.summary || '',
          };
          setLiveEntries(prev => [...prev.slice(-500), entry]);
        } catch {
          setLiveEntries(prev => [...prev.slice(-500), {
            id: `ws-${Date.now()}`, timestamp: new Date().toISOString(),
            ip: '—', risk_level: 'info', anomalies: [], correlations: [],
            log: event.data, action: 'allowed', ai_summary: '',
          }] as LiveEntry[]);
        }
      };
      ws.onclose = () => {
        setWsConnected(false);
        if (demoActiveRef.current) reconnectRef.current = setTimeout(() => connectWs(), 2000);
      };
      wsRef.current = ws;
    } catch { setError('Failed to connect to Security Pipeline'); }
  }, []);

  const disconnectWs = useCallback(() => {
    if (reconnectRef.current) clearTimeout(reconnectRef.current);
    if (wsRef.current) { wsRef.current.onclose = null; wsRef.current.close(); }
    setWsConnected(false);
  }, []);

  useEffect(() => {
    if (demoActive) connectWs();
    return () => disconnectWs();
  }, [demoActive, connectWs, disconnectWs]);

  const handleStart = async () => {
    setLoading(true);
    try {
      await startProducer();
      setProducerRunning(true);
      setDemoActive(true);
      setWarmupProgress(0);
      setLiveEntries([]);
    } catch (err) { setError('Failed to initialize Log Stream'); }
    finally { setLoading(false); }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await stopProducer();
      setProducerRunning(false);
      setDemoActive(false);
      disconnectWs();
    } catch (err) { setError('Failed to stop Log Stream'); }
    finally { setLoading(false); }
  };

  const threatCount = liveEntries.filter(e => e.anomalies.length > 0).length;
  const isMLReady = warmupProgress >= 100;

  return (
    <div className="terminal-theme" style={{ color: '#00ff41', background: '#0a0a0c', minHeight: '100vh', padding: '24px' }}>
      {/* Terminal Header */}
      <div style={{ borderBottom: '1px solid #00ff41', paddingBottom: '16px', marginBottom: '24px' }}>
        <h1 style={{ fontFamily: 'var(--font-mono)', fontSize: '1.5rem', textTransform: 'uppercase', letterSpacing: '2px' }}>
          {">"} SECURITY_LOG_ANALYZER_V3.0
        </h1>
        <div style={{ display: 'flex', gap: '20px', fontSize: '0.8rem', opacity: 0.8 }}>
          <span>STATUS: {wsConnected ? '[ ONLINE ]' : '[ OFFLINE ]'}</span>
          <span>PIPELINE: {producerRunning ? '[ ACTIVE ]' : '[ IDLE ]'}</span>
          <span>MODELS: {isMLReady ? '[ ML_ARMED ]' : `[ TRAINING_${warmupProgress}% ]`}</span>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
        <button className={`terminal-btn ${demoActive ? 'active' : ''}`} onClick={handleStart} disabled={loading || demoActive}>
          {loading ? 'INIT...' : 'START_STREAM'}
        </button>
        <button className="terminal-btn-danger" onClick={handleStop} disabled={loading || !demoActive}>
          TERMINATE
        </button>
        <div style={{ flex: 1 }} />
        <div style={{ color: '#ff4757', fontWeight: 600 }}>
          {threatCount > 0 && `!!! ${threatCount} ANOMALIES DETECTED !!!`}
        </div>
      </div>

      {/* Terminal Viewport */}
      <div className="terminal-viewport">
        <div className="terminal-scanline" />
        <div
          ref={feedRef}
          onScroll={() => {
            if (!feedRef.current) return;
            const { scrollTop, scrollHeight, clientHeight } = feedRef.current;
            setAutoScroll(scrollHeight - scrollTop - clientHeight < 50);
          }}
          style={{ height: '600px', overflowY: 'auto', padding: '20px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: 1.5 }}
        >
          {liveEntries.length === 0 && (
            <div style={{ opacity: 0.5 }}>
              Waiting for uplink...<br />
              Execute START_STREAM to begin log ingestion.
            </div>
          )}
          
          {liveEntries.map((entry) => {
            const isThreat = entry.anomalies.length > 0 || entry.correlations.length > 0;
            const hasAI = !!entry.ai_summary;
            
            return (
              <div key={entry.id} style={{ marginBottom: '4px', borderLeft: isThreat ? '2px solid #ff4757' : 'none', paddingLeft: isThreat ? '10px' : '0' }}>
                <span style={{ opacity: 0.4 }}>[{new Date(entry.timestamp).toLocaleTimeString()}]</span>
                {' '}
                <span style={{ color: '#00bcff' }}>{entry.ip.padEnd(15)}</span>
                {' | '}
                <span style={{ 
                  color: entry.risk_level === 'critical' ? '#ff4757' : entry.risk_level === 'high' ? '#ffa502' : '#00ff41',
                  fontWeight: isThreat ? 600 : 400
                }}>
                  {entry.risk_level.toUpperCase().padEnd(8)}
                </span>
                {' | '}
                <span style={{ color: isThreat ? '#fff' : '#00ff41', opacity: isThreat ? 1 : 0.8 }}>
                  {entry.log}
                </span>

                {isThreat && (
                  <div style={{ marginLeft: '20px', fontSize: '0.75rem', color: '#ffa502' }}>
                    {">>"} DETECTED: {entry.anomalies.map(a => `<${a.type}>`).join(' ')}
                    {entry.action === 'blocked' && ' [ !! BLOCKED !! ]'}
                  </div>
                )}

                {hasAI && (
                  <div className="terminal-ai-alert">
                    <div style={{ fontWeight: 700, marginBottom: '4px' }}>AI_INCIDENT_SUMMARY:</div>
                    <div style={{ fontStyle: 'italic', color: '#fff' }}>"{entry.ai_summary}"</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <style jsx>{`
        .terminal-theme {
          background-color: #0a0a0c;
          background-image: radial-gradient(rgba(0, 150, 0, 0.1), black);
        }
        .terminal-btn {
          background: transparent;
          border: 1px solid #00ff41;
          color: #00ff41;
          padding: 8px 16px;
          cursor: pointer;
          font-family: var(--font-mono);
          transition: all 0.2s;
        }
        .terminal-btn:hover:not(:disabled) {
          background: rgba(0, 255, 65, 0.1);
          box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
        }
        .terminal-btn-danger {
          background: transparent;
          border: 1px solid #ff4757;
          color: #ff4757;
          padding: 8px 16px;
          cursor: pointer;
          font-family: var(--font-mono);
        }
        .terminal-viewport {
          position: relative;
          background: rgba(0, 20, 0, 0.5);
          border: 1px solid rgba(0, 255, 65, 0.2);
          box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.9);
          border-radius: 4px;
        }
        .terminal-scanline {
          position: absolute;
          top: 0; left: 0; right: 0; bottom: 0;
          background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
          background-size: 100% 4px, 3px 100%;
          pointer-events: none;
          z-index: 2;
          opacity: 0.15;
        }
        .terminal-ai-alert {
          margin: 10px 0;
          padding: 12px;
          background: rgba(0, 188, 255, 0.1);
          border: 1px dashed #00bcff;
          color: #00bcff;
          animation: terminal-flicker 0.1s infinite alternate;
        }
        @keyframes terminal-flicker {
          from { opacity: 0.95; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

