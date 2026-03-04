import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [tickerIndex, setTickerIndex] = useState(0);

  const statusMessages = [
    'SYS: All Services Operational',
    'CHK: Integrity Verified 100%',
    'VOL: 500+ Files Indexed',
    'LOG: Last Audit 2026-03-04',
    'NET: Zero Conflicts Detected'
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % statusMessages.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setSubmitted(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    }
  };

  return (
    <div className="lp-root">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');

        :root {
          --amber: #E8A020;
          --green: #3DCC78;
          --bg: #0A0A0A;
          --surface: #121212;
          --surface-elev: #1A1A1A;
          --text: #E5E5E5;
          --text-muted: #888888;
          --border: #2A2A2A;
          --font-mono: 'IBM Plex Mono', monospace;
          --font-display: 'Syne', sans-serif;
        }

        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        .lp-root {
          min-height: 100vh;
          background: var(--bg);
          color: var(--text);
          font-family: var(--font-mono);
          position: relative;
          overflow-x: hidden;
        }

        .lp-grain {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          opacity: 0.03;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
          z-index: 0;
        }

        .lp-scan {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--amber), transparent);
          animation: scanline 8s linear infinite;
          z-index: 1;
          opacity: 0.3;
        }

        @keyframes scanline {
          0% { transform: translateY(-100vh); }
          100% { transform: translateY(100vh); }
        }

        .lp-canvas {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-image: 
            linear-gradient(var(--border) 1px, transparent 1px),
            linear-gradient(90deg, var(--border) 1px, transparent 1px);
          background-size: 60px 60px;
          opacity: 0.1;
          z-index: 0;
          pointer-events: none;
        }

        .lp-nav {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: 64px;
          background: rgba(10, 10, 10, 0.95);
          backdrop-filter: blur(8px);
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 48px;
          z-index: 100;
        }

        .lp-brand {
          font-family: var(--font-display);
          font-size: 16px;
          font-weight: 800;
          letter-spacing: 3px;
          color: var(--amber);
          text-transform: uppercase;
        }

        .lp-nav-status {
          font-family: var(--font-mono);
          font-size: 12px;
          color: var(--green);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .lp-nav-status::before {
          content: '';
          width: 8px;
          height: 8px;
          background: var(--green);
          border-radius: 50%;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .lp-hero {
          padding: 180px 48px 100px;
          text-align: center;
          position: relative;
          z-index: 1;
        }

        .lp-hero-title {
          font-family: var(--font-display);
          font-size: 72px;
          font-weight: 800;
          letter-spacing: -3px;
          margin-bottom: 24px;
          line-height: 1.1;
        }

        .lp-hero-title .line-1 {
          display: block;
          background: linear-gradient(135deg, var(--text) 0%, var(--text-muted) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .lp-hero-title .line-2 {
          display: block;
          color: var(--amber);
        }

        .lp-hero-subtitle {
          font-size: 16px;
          color: var(--text-muted);
          max-width: 600px;
          margin: 0 auto 48px;
          line-height: 1.7;
        }

        .lp-status {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 20px 32px;
          max-width: 700px;
          margin: 0 auto 64px;
          font-family: var(--font-mono);
        }

        .lp-status-ticker {
          font-size: 13px;
          color: var(--green);
          min-height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          letter-spacing: 1px;
        }

        .lp-ticker-labels {
          display: flex;
          justify-content: center;
          gap: 24px;
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid var(--border);
        }

        .lp-ticker-label {
          font-size: 11px;
          color: var(--text-muted);
          letter-spacing: 2px;
        }

        .lp-ticker-label.active {
          color: var(--amber);
        }

        .lp-stats {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 24px;
          max-width: 1000px;
          margin: 0 auto 80px;
        }

        .lp-stat {
          background: var(--surface-elev);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 24px;
          text-align: center;
        }

        .lp-stat-value {
          font-family: var(--font-display);
          font-size: 36px;
          font-weight: 700;
          color: var(--amber);
          margin-bottom: 8px;
        }

        .lp-stat-label {
          font-size: 11px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .lp-features {
          padding: 80px 48px;
          background: var(--surface);
          border-top: 1px solid var(--border);
          border-bottom: 1px solid var(--border);
        }

        .lp-features-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 32px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .lp-feature {
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 32px;
        }

        .lp-feature-icon {
          font-family: var(--font-mono);
          font-size: 24px;
          color: var(--amber);
          margin-bottom: 16px;
        }

        .lp-feature-title {
          font-family: var(--font-display);
          font-size: 18px;
          font-weight: 700;
          margin-bottom: 12px;
        }

        .lp-feature-desc {
          font-size: 14px;
          color: var(--text-muted);
          line-height: 1.6;
        }

        .lp-pipeline {
          padding: 80px 48px;
          text-align: center;
        }

        .lp-pipeline-title {
          font-family: var(--font-display);
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 48px;
          letter-spacing: 2px;
        }

        .lp-pipeline-steps {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
          max-width: 1000px;
          margin: 0 auto;
        }

        .lp-step {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 16px 24px;
          font-family: var(--font-mono);
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 2px;
          text-transform: uppercase;
          color: var(--text-muted);
          position: relative;
        }

        .lp-step::after {
          content: '→';
          position: absolute;
          right: -20px;
          color: var(--amber);
        }

        .lp-step:last-child::after {
          display: none;
        }

        .lp-step.active {
          border-color: var(--amber);
          color: var(--amber);
          box-shadow: 0 0 20px rgba(232, 160, 32, 0.2);
        }

        .lp-request {
          padding: 80px 48px;
          background: var(--surface);
          border-top: 1px solid var(--border);
        }

        .lp-request-form {
          max-width: 500px;
          margin: 0 auto;
        }

        .lp-request-title {
          font-family: var(--font-display);
          font-size: 20px;
          font-weight: 700;
          text-align: center;
          margin-bottom: 32px;
          letter-spacing: 1px;
        }

        .lp-input-group {
          margin-bottom: 16px;
        }

        .lp-input {
          width: 100%;
          padding: 16px;
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 4px;
          color: var(--text);
          font-family: var(--font-mono);
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s;
        }

        .lp-input:focus {
          border-color: var(--amber);
        }

        .lp-btn {
          width: 100%;
          padding: 16px;
          background: var(--amber);
          border: none;
          border-radius: 4px;
          color: var(--bg);
          font-family: var(--font-mono);
          font-size: 14px;
          font-weight: 700;
          letter-spacing: 1px;
          text-transform: uppercase;
          cursor: pointer;
          transition: opacity 0.2s;
        }

        .lp-btn:hover {
          opacity: 0.9;
        }

        .lp-confirmation {
          text-align: center;
          padding: 32px;
          background: var(--bg);
          border: 1px solid var(--green);
          border-radius: 4px;
          font-family: var(--font-mono);
          font-size: 14px;
          color: var(--green);
        }

        .lp-footer {
          padding: 48px;
          text-align: center;
          border-top: 1px solid var(--border);
        }

        .lp-footer-text {
          font-family: var(--font-mono);
          font-size: 12px;
          color: var(--text-muted);
          letter-spacing: 1px;
        }

        @media (max-width: 1024px) {
          .lp-stats {
            grid-template-columns: repeat(2, 1fr);
          }
          .lp-features-grid {
            grid-template-columns: 1fr;
          }
          .lp-hero-title {
            font-size: 56px;
          }
        }

        @media (max-width: 768px) {
          .lp-nav {
            padding: 0 24px;
          }
          .lp-hero {
            padding: 140px 24px 60px;
          }
          .lp-hero-title {
            font-size: 42px;
          }
          .lp-stats {
            grid-template-columns: 1fr;
          }
          .lp-pipeline-steps {
            flex-direction: column;
          }
          .lp-step::after {
            display: none;
          }
        }
      `}</style>

      <div className="lp-grain" />
      <div className="lp-scan" />
      <div className="lp-canvas" />

      <nav className="lp-nav">
        <div className="lp-brand">AXIOMATIC</div>
        <div className="lp-nav-status">SYSTEM OPERATIONAL</div>
      </nav>

      <section className="lp-hero">
        <h1 className="lp-hero-title">
          <span className="line-1">Every</span>
          <span className="line-2">Accounted</span>
        </h1>
        <p className="lp-hero-subtitle">
          Industrial-grade photo workflow automation with cryptographic sidecar architecture.
          Built for photographers who demand absolute integrity and chain-of-custody verification.
        </p>

        <div className="lp-status">
          <div className="lp-status-ticker">
            {statusMessages[tickerIndex]}
          </div>
          <div className="lp-ticker-labels">
            <span className="lp-ticker-label active">SYS</span>
            <span className="lp-ticker-label">CHK</span>
            <span className="lp-ticker-label">VOL</span>
            <span className="lp-ticker-label">LOG</span>
            <span className="lp-ticker-label">NET</span>
          </div>
        </div>

        <div className="lp-stats">
          <div className="lp-stat">
            <div className="lp-stat-value">500+</div>
            <div className="lp-stat-label">RAW Files</div>
          </div>
          <div className="lp-stat">
            <div className="lp-stat-value">16</div>
            <div className="lp-stat-label">Audit Sessions</div>
          </div>
          <div className="lp-stat">
            <div className="lp-stat-value">0</div>
            <div className="lp-stat-label">Conflicts</div>
          </div>
          <div className="lp-stat">
            <div className="lp-stat-value">100%</div>
            <div className="lp-stat-label">Integrity</div>
          </div>
        </div>
      </section>

      <section className="lp-features">
        <div className="lp-features-grid">
          <div className="lp-feature">
            <div className="lp-feature-icon">⚡</div>
            <div className="lp-feature-title">Automated Ingestion</div>
            <div className="lp-feature-desc">
              Mount any drive and instantly scan for RAW files. Automatic format detection,
              checksum generation, and metadata extraction without manual intervention.
            </div>
          </div>
          <div className="lp-feature">
            <div className="lp-feature-icon">🔐</div>
            <div className="lp-feature-title">Sidecar Architecture</div>
            <div className="lp-feature-desc">
              JSON sidecars store all audit metadata separately from source files.
              Non-destructive workflow with full rollback capability and version tracking.
            </div>
          </div>
          <div className="lp-feature">
            <div className="lp-feature-icon">🛡️</div>
            <div className="lp-feature-title">Hardened Dashboard</div>
            <div className="lp-feature-desc">
              Real-time monitoring of all audit sessions. Conflict detection, integrity
              verification, and comprehensive logging for professional accountability.
            </div>
          </div>
        </div>
      </section>

      <section className="lp-pipeline">
        <h2 className="lp-pipeline-title">AUDIT PIPELINE</h2>
        <div className="lp-pipeline-steps">
          <div className="lp-step active">MOUNT</div>
          <div className="lp-step active">SCAN</div>
          <div className="lp-step active">SIDECAR</div>
          <div className="lp-step active">VERIFY</div>
          <div className="lp-step active">ARCHIVE</div>
        </div>
      </section>

      <section className="lp-request">
        <div className="lp-request-form">
          <h2 className="lp-request-title">REQUEST ACCESS</h2>
          {submitted ? (
            <div className="lp-confirmation">
              ✓ Access granted. Redirecting to dashboard...
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="lp-input-group">
                <input
                  type="email"
                  className="lp-input"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="lp-btn">
                Authenticate
              </button>
            </form>
          )}
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-footer-text">
          AXIOMATIC MEDIA AUDIT ORGANIZER © 2026
        </div>
        <div className="lp-footer-text" style={{ marginTop: '8px' }}>
          CHAIN OF CUSTODY VERIFIED · INTEGRITY PROTECTED
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
