'use client';

import { useState, useRef } from 'react';
import { analyzeLogs } from '@/lib/api';

/* eslint-disable @typescript-eslint/no-explicit-any */

function getRiskClass(risk: string) {
  const r = (risk || '').toLowerCase();
  if (r.includes('critical')) return 'badge-critical';
  if (r.includes('high')) return 'badge-high';
  if (r.includes('medium') || r.includes('warning')) return 'badge-medium';
  if (r.includes('low')) return 'badge-low';
  return 'badge-info';
}

function getRiskColor(level: string) {
  const l = (level || '').toLowerCase();
  if (l.includes('critical')) return 'var(--severity-critical)';
  if (l.includes('high')) return 'var(--severity-high)';
  if (l.includes('medium')) return 'var(--severity-medium)';
  return 'var(--severity-low)';
}

// These finding types are informational, not truly "sensitive data"
const INFORMATIONAL_TYPES = ['ip_address', 'ip', 'hostname', 'url', 'domain'];

export default function AnalyzePage() {
  const [inputType, setInputType] = useState<'text' | 'file'>('text');
  const [textContent, setTextContent] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  async function handleAnalyze() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      if (inputType === 'text') {
        if (!textContent.trim()) { setError('Please enter log text to analyze.'); setLoading(false); return; }
        setResult(await analyzeLogs('text', textContent));
      } else {
        if (!selectedFile) { setError('Please select a file to upload.'); setLoading(false); return; }
        setResult(await analyzeLogs('file', selectedFile));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) { setSelectedFile(e.dataTransfer.files[0]); setInputType('file'); }
  }

  // Parse result fields
  const riskScore: number | null = result?.risk_score ?? null;
  const riskLevel: string = result?.risk_level || '';
  const allFindings: any[] = result?.findings || [];
  const insights: string[] = result?.insights || [];
  const anomalies: any[] = result?.anomalies || [];
  const correlations: any[] = result?.correlations || [];
  const aiAnalysis: any = result?.ai_analysis || null;
  const action: string = result?.action || '';
  const maskedOutput: string | null = result?.masked_output || null;

  // Split findings: real sensitive data vs informational
  const sensitiveFindings = allFindings.filter(f => !INFORMATIONAL_TYPES.includes((f.type || '').toLowerCase()));
  const infoFindings = allFindings.filter(f => INFORMATIONAL_TYPES.includes((f.type || '').toLowerCase()));

  // Check if AI analysis has real content
  const hasAiContent = aiAnalysis && aiAnalysis.summary && aiAnalysis.summary !== 'Skipped for performance' && aiAnalysis.summary !== 'AI failed';

  return (
    <>
      <div className="page-header">
        <h2>Analyze Logs</h2>
        <p>Paste text or upload a log file for on-demand security analysis</p>
      </div>

      {/* Input Type Toggle */}
      <div className="tab-bar" style={{ maxWidth: '320px' }}>
        <button className={inputType === 'text' ? 'active' : ''} onClick={() => setInputType('text')}>📝 Paste Text</button>
        <button className={inputType === 'file' ? 'active' : ''} onClick={() => setInputType('file')}>📁 Upload File</button>
      </div>

      {inputType === 'text' ? (
        <textarea
          className="textarea"
          placeholder={`Paste your raw logs here for analysis...\n\nExample:\n2024-01-15 10:30:45 Failed login attempt from 192.168.1.100 user=admin password=secret123\n2024-01-15 10:30:46 API key exposed: sk-1234567890abcdefg`}
          value={textContent}
          onChange={(e) => setTextContent(e.target.value)}
          rows={10}
        />
      ) : (
        <div
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="dropzone-icon">📄</div>
          <div className="dropzone-text">
            {selectedFile ? (
              <><strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(1)} KB)</>
            ) : (
              <><strong>Click to upload</strong> or drag and drop<br />Log files (.log, .txt, .csv)</>
            )}
          </div>
          <input ref={fileInputRef} type="file" accept=".log,.txt,.csv,.json" style={{ display: 'none' }}
            onChange={(e) => { if (e.target.files?.[0]) setSelectedFile(e.target.files[0]); }}
          />
        </div>
      )}

      {error && <div className="error-message" style={{ marginTop: '16px' }}>{error}</div>}

      <div style={{ marginTop: '20px' }}>
        <button className="btn btn-primary btn-lg" onClick={handleAnalyze} disabled={loading}>
          {loading ? (<><div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} /> Analyzing...</>) : (<>🔍 Analyze Logs</>)}
        </button>
      </div>

      {/* ══════════════════ RESULTS ══════════════════ */}
      {result && (
        <div style={{ marginTop: '32px' }}>

          {/* ── 1. AI ANALYSIS FIRST (hero section) ──── */}
          {hasAiContent && (
            <div className="ai-insights" style={{ marginBottom: '24px' }}>
              <h4>✨ AI-Powered Threat Analysis</h4>
              <p style={{ color: 'var(--on-surface)', fontSize: '0.9rem', lineHeight: 1.8, marginBottom: '16px' }}>
                {aiAnalysis.summary}
              </p>
              {aiAnalysis.attack_narrative && (
                <div style={{ marginBottom: '14px' }}>
                  <strong style={{ color: 'var(--secondary)', fontSize: '0.85rem' }}>🎯 Attack Narrative</strong>
                  <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.85rem', marginTop: '6px', lineHeight: 1.7 }}>{aiAnalysis.attack_narrative}</p>
                </div>
              )}
              {aiAnalysis.root_cause && (
                <div style={{ marginBottom: '14px' }}>
                  <strong style={{ color: 'var(--secondary)', fontSize: '0.85rem' }}>🔍 Root Cause</strong>
                  <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.85rem', marginTop: '6px', lineHeight: 1.7 }}>{aiAnalysis.root_cause}</p>
                </div>
              )}
              {Array.isArray(aiAnalysis.risks) && aiAnalysis.risks.length > 0 && (
                <div>
                  <strong style={{ color: 'var(--secondary)', fontSize: '0.85rem' }}>⚠️ Identified Risks</strong>
                  <ul style={{ paddingLeft: '20px', marginTop: '6px' }}>
                    {aiAnalysis.risks.map((r: string, i: number) => (
                      <li key={i} style={{ color: 'var(--on-surface-variant)', fontSize: '0.85rem', marginBottom: '4px', lineHeight: 1.6 }}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* ── 2. RISK SCORE + LEVEL + INSIGHTS ──── */}
          <div className="results-panel" style={{ display: 'flex', alignItems: 'center', gap: '32px', flexWrap: 'wrap', marginBottom: '20px' }}>
            {riskScore !== null && (
              <div className="risk-gauge">
                <div className="gauge-circle" style={{
                  /* Color the gauge by risk_level, not the raw score */
                  background: `radial-gradient(circle at center, var(--surface-container) 45%, transparent 45%), conic-gradient(${getRiskColor(riskLevel)} 100%, var(--surface-container-highest) 0%)`,
                  color: getRiskColor(riskLevel),
                  boxShadow: `0 0 30px ${getRiskColor(riskLevel)}33`,
                }}>
                  {riskScore}
                </div>
                <div className="gauge-label">Risk Score</div>
              </div>
            )}
            <div style={{ flex: 1 }}>
              {riskLevel && (
                <p style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '12px' }}>
                  <span className={`badge ${getRiskClass(riskLevel)}`} style={{ fontSize: '0.85rem', padding: '6px 16px' }}>
                    {riskLevel.toUpperCase()}
                  </span>
                  {' '}Risk Level
                </p>
              )}
              {action && action !== 'allowed' && (
                <p style={{ fontSize: '0.85rem', color: 'var(--severity-critical)', marginBottom: '8px' }}>
                  ⚡ Action: <strong>{action}</strong>
                </p>
              )}
              {insights.length > 0 && (
                <div>
                  {insights.map((insight, i) => (
                    <p key={i} style={{ fontSize: '0.85rem', color: 'var(--on-surface-variant)', marginBottom: '4px' }}>• {insight}</p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ── 3. ANOMALIES ──── */}
          {anomalies.length > 0 && (
            <div className="results-panel" style={{ marginBottom: '20px' }}>
              <h3>⚡ Anomalies Detected ({anomalies.length})</h3>
              <div className="findings-list">
                {anomalies.map((a: any, idx: number) => (
                  <div className="finding-item" key={idx}>
                    <span className={`badge ${getRiskClass(a.risk || 'high')}`}>{a.risk || 'Anomaly'}</span>
                    <span style={{ fontWeight: 500, color: 'var(--secondary)' }}>{a.type || 'Anomaly'}</span>
                    <span>{a.description || a.details || ''}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── 4. CORRELATIONS ──── */}
          {correlations.length > 0 && (
            <div className="results-panel" style={{ marginBottom: '20px' }}>
              <h3>🔗 Attack Correlations ({correlations.length})</h3>
              <div className="findings-list">
                {correlations.map((c: any, idx: number) => (
                  <div className="finding-item" key={idx}>
                    <span className={`badge ${getRiskClass(c.risk || 'critical')}`}>{c.risk || 'Pattern'}</span>
                    <span style={{ fontWeight: 500, color: 'var(--secondary)' }}>{c.type || 'Correlation'}</span>
                    <span>{c.description || c.details || ''}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── 5. SENSITIVE DATA (excluding IP addresses) ──── */}
          {sensitiveFindings.length > 0 && (
            <div className="results-panel" style={{ marginBottom: '20px' }}>
              <h3>🔐 Sensitive Data Exposed ({sensitiveFindings.length})</h3>
              <div className="findings-list">
                {sensitiveFindings.map((f: any, idx: number) => (
                  <div className="finding-item" key={idx}>
                    <span className={`badge ${getRiskClass(f.risk)}`}>{f.risk}</span>
                    <span style={{ color: 'var(--secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', flexShrink: 0 }}>
                      [{f.type}] Line {f.line}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', wordBreak: 'break-all' }}>{f.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── 6. INFORMATIONAL (IPs etc — collapsed by default) ──── */}
          {infoFindings.length > 0 && (
            <div className="results-panel" style={{ marginBottom: '20px' }}>
              <details>
                <summary style={{ cursor: 'pointer', fontSize: '0.9rem', fontWeight: 500, color: 'var(--on-surface-variant)' }}>
                  📌 Informational — IPs & Identifiers ({infoFindings.length})
                </summary>
                <div className="findings-list" style={{ marginTop: '12px' }}>
                  {infoFindings.map((f: any, idx: number) => (
                    <div className="finding-item" key={idx} style={{ opacity: 0.7 }}>
                      <span className="badge badge-info">{f.type}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>Line {f.line}: {f.value}</span>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* ── 7. MASKED OUTPUT ──── */}
          {maskedOutput && (
            <div className="results-panel">
              <h3>🔒 Masked Output</h3>
              <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--on-surface-variant)', whiteSpace: 'pre-wrap' }}>{maskedOutput}</pre>
            </div>
          )}
        </div>
      )}
    </>
  );
}
