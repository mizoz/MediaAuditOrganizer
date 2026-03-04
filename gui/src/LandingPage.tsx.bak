import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [tickerIndex, setTickerIndex] = useState(0);

  const statusMessages = [
    'System Ready — All Services Operational',
    'Last Audit: 2026-03-03 23:47 MST',
    'Sidecar Sync: 100% Integrity Verified',
    'Checksum Validation: PASSED',
    'Archive Status: 0 Conflicts Detected'
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
    <div className="axm-root">
      <style>{`
        :root {
          --amber: #E8A020;
          --green: #3DCC78;
          --bg: #0A0A0A;
          --surface: #121212;
          --surface-elev: #1A1A1A;
          --text: #E5E5E5;
          --text-muted: #888888;
          --border: #2A2A2A;
          --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
          --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        .axm-root {
          min-height: 100vh;
          background: var(--bg);
          color: var(--text);
          font-family: var(--font-sans);
          position: relative;
          overflow-x: hidden;
        }

        .axm-grain {
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

        .axm-nav {
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

        .axm-brand {
          font-family: var(--font-mono);
          font-size: 14px;
          font-weight: 700;
          letter-spacing: 2px;
          color: var(--amber);
          text-transform: uppercase;
        }

        .axm-nav-status {
          font-family: var(--font-mono);
          font-size: 12px;
          color: var(--green);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .axm-nav-status::before {
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

        .axm-hero {
          padding: 160px 48px 80px;
          text-align: center;
          position: relative;
          z-index: 1;
        }

        .axm-hero-title {
          font-family: var(--font-mono);
          font-size: 48px;
          font-weight: 700;
          letter-spacing: -2px;
          margin-bottom: 16px;
          background: linear-gradient(135deg, var(--text) 0%, var(--text-muted) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .axm-hero-subtitle {
          font-size: 18px;
          color: var(--text-muted);
          max-width: 600px;
          margin: 0 auto 48px;
          line-height: 1.6;
        }

        .axm-status {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 24px;
          max-width: 800px;
          margin: 0 auto 64px;
          font-family: var(--font-mono);
        }

        .axm-status-ticker {
          font-size: 13px;
          color: var(--green);
          min-height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .axm-stats {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 24px;
          max-width: 1000px;
          margin: 0 auto 80px;
        }

        .axm-stat {
          background: var(--surface-elev);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 24px;
          text-align: center;
        }

        .axm-stat-value {
          font-family: var(--font-mono);
          font-size: 32px;
          font-weight: 700;
          color: var(--amber);
          margin-bottom: 8px;
        }

        .axm-stat-label {
          font-size: 12px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .axm-features {
          padding: 80px 48px;
          background: var(--surface);
          border-top: 1px solid var(--border);
          border-bottom: 1px solid var(--border);
        }

        .axm-features-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 32px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .axm-feature {
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 32px;
        }

        .axm-feature-icon {
          font-family: var(--font-mono);
          font-size: 24px;
          color: var(--amber);
          margin-bottom: 16px;
        }

        .axm-feature-title {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 12px;
        }

        .axm-feature-desc {
          font-size: 14px;
          color: var(--text-muted);
          line-height: 1.6;
        }

        .axm-pipeline {
          padding: 80px 48px;
          text-align: center;
        }

        .axm-pipeline-title {
          font-family: var(--font-mono);
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 48px;
          letter-spacing: 1px;
        }

        .axm-pipeline-steps {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
          max-width: 1000px;
          margin: 0 auto;
        }

        .axm-step {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 4px;
          padding: 16px 24px;
          font-family: var(--font-mono);
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 1px;
          text-transform: uppercase;
          color: var(--text-muted);
          position: relative;
        }

        .axm-step::after {
          content: '→';
          position: absolute;
          right: -20px;
          color: var(--amber);
        }

        .axm-step:last-child::after {
          display: none;
        }

        .axm-step.active {
          border-color: var(--amber);
          color: var(--amber);
        }

        .axm-request {
          padding: 80px 48px;
          background: var(--surface);
          border-top: 1px solid var(--border);
        }

        .axm-request-form {
          max-width: 500px;
          margin: 0 auto;
        }

        .axm-request-title {
          font-family: var(--font-mono);
          font-size: 20px;
          font-weight: 700;
          text-align: center;
          margin-bottom: 32px;
          letter-spacing: 1px;
        }

        .axm-input-group {
          margin-bottom: 16px;
        }

        .axm-input {
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

        .axm-input:focus {
          border-color: var(--amber);
        }

        .axm-btn {
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

        .axm-btn:hover {
          opacity: 0.9;
        }

        .axm-confirmation {
          text-align: center;
          padding: 32px;
          background: var(--bg);
          border: 1px solid var(--green);
          border-radius: 4px;
          font-family: var(--font-mono);
          font-size: 14px;
          color: var(--green);
        }

        .axm-footer {
          padding: 48px;
          text-align: center;
          border-top: 1px solid var(--border);
        }

        .axm-footer-text {
          font-family: var(--font-mono);
          font-size: 12px;
          color: var(--text-muted);
          letter-spacing: 1px;
        }

        @media (max-width: 1024px) {
          .axm-stats {
            grid-template-columns: repeat(2, 1fr);
          }
          .axm-features-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 768px) {
          .axm-nav {
            padding: 0 24px;
          }
          .axm-hero {
            padding: 120px 24px 60px;
          }
          .axm-hero-title {
            font-size: 32px;
          }
          .axm-stats {
            grid-template-columns: 1fr;
          }
          .axm-pipeline-steps {
            flex-direction: column;
          }
          .axm-step::after {
            display: none;
          }
        }
      `}</style>

      <div className="axm-grain" />

      <nav className="axm-nav">
        <div className="axm-brand">AXIOMATIC</div>
        <div className="axm-nav-status">SYSTEM OPERATIONAL</div>
      </nav>

      <section className="axm-hero">
        <h1 className="axm-hero-title">MEDIA AUDIT ORGANIZER</h1>
        <p className="axm-hero-subtitle">
          Industrial-grade photo workflow automation with cryptographic sidecar architecture.
          Built for photographers who demand absolute integrity and chain-of-custody verification.
        </p>

        <div className="axm-status">
          <div className="axm-status-ticker">
            {statusMessages[tickerIndex]}
          </div>
        </div>

        <div className="axm-stats">
          <div className="axm-stat">
            <div className="axm-stat-value">500+</div>
            <div className="axm-stat-label">RAW Files</div>
          </div>
          <div className="axm-stat">
            <div className="axm-stat-value">16</div>
            <div className="axm-stat-label">Audit Sessions</div>
          </div>
          <div className="axm-stat">
            <div className="axm-stat-value">0</div>
            <div className="axm-stat-label">Sidecar Conflicts</div>
          </div>
          <div className="axm-stat">
            <div className="axm-stat-value">100%</div>
            <div className="axm-stat-label">CoC Integrity</div>
          </div>
        </div>
      </section>

      <section className="axm-features">
        <div className="axm-features-grid">
          <div className="axm-feature">
            <div className="axm-feature-icon">⚡</div>
            <div className="axm-feature-title">Automated Ingestion</div>
            <div className="axm-feature-desc">
              Mount any drive and instantly scan for RAW files. Automatic format detection,
              checksum generation, and metadata extraction without manual intervention.
            </div>
          </div>
          <div className="axm-feature">
            <div className="axm-feature-icon">🔐</div>
            <div className="axm-feature-title">Sidecar Architecture</div>
            <div className="axm-feature-desc">
              JSON sidecars store all audit metadata separately from source files.
              Non-destructive workflow with full rollback capability and version tracking.
            </div>
          </div>
          <div className="axm-feature">
            <div className="axm-feature-icon">🛡️</div>
            <div className="axm-feature-title">Hardened Dashboard</div>
            <div className="axm-feature-desc">
              Real-time monitoring of all audit sessions. Conflict detection, integrity
              verification, and comprehensive logging for professional accountability.
            </div>
          </div>
        </div>
      </section>

      <section className="axm-pipeline">
        <h2 className="axm-pipeline-title">AUDIT PIPELINE</h2>
        <div className="axm-pipeline-steps">
          <div className="axm-step active">MOUNT DRIVE</div>
          <div className="axm-step active">SCAN FILES</div>
          <div className="axm-step active">GEN SIDECARS</div>
          <div className="axm-step active">VERIFY CHECKSUMS</div>
          <div className="axm-step active">ARCHIVE</div>
        </div>
      </section>

      <section className="axm-request">
        <div className="axm-request-form">
          <h2 className="axm-request-title">REQUEST ACCESS</h2>
          {submitted ? (
            <div className="axm-confirmation">
              ✓ Access granted. Redirecting to dashboard...
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="axm-input-group">
                <input
                  type="email"
                  className="axm-input"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="axm-btn">
                Authenticate
              </button>
            </form>
          )}
        </div>
      </section>

      <footer className="axm-footer">
        <div className="axm-footer-text">
          AXIOMATIC MEDIA AUDIT ORGANIZER © 2026
        </div>
        <div className="axm-footer-text" style={{ marginTop: '8px' }}>
          CHAIN OF CUSTODY VERIFIED · INTEGRITY PROTECTED
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
