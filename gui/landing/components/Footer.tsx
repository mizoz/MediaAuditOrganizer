import React from 'react';

// Brand config — swap name in one place
const BRAND = {
  NAME: 'AXIOMATIC', // CHANGE THIS ONE VARIABLE
  TAGLINE: 'Local-First Media Organization',
};

interface FooterProps {
  className?: string;
}

const Footer: React.FC<FooterProps> = ({ className = '' }) => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={`py-12 bg-obsidian border-t border-slate/30 ${className}`}>
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* Brand */}
          <div>
            <h3 className="text-lg font-bold text-white mb-2">{BRAND.NAME}</h3>
            <p className="text-sm text-slate-light">{BRAND.TAGLINE}</p>
          </div>

          {/* Links */}
          <div className="flex flex-wrap gap-6 text-sm">
            <a
              href="#"
              className="text-slate-light hover:text-cyber-lime transition-colors"
            >
              Documentation
            </a>
            <a
              href="#"
              className="text-slate-light hover:text-cyber-lime transition-colors"
            >
              GitHub
            </a>
            <a
              href="#"
              className="text-slate-light hover:text-cyber-lime transition-colors"
            >
              Privacy
            </a>
            <a
              href="#"
              className="text-slate-light hover:text-cyber-lime transition-colors"
            >
              Contact
            </a>
          </div>

          {/* Status */}
          <div className="text-right">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate/10 border border-slate/30 rounded-md">
              <span className="w-2 h-2 rounded-full bg-cyber-lime animate-pulse" />
              <span className="text-xs font-mono text-slate-light">
                ALPHA WAITLIST OPEN
              </span>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-slate/30 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-slate-light">
            © {currentYear} {BRAND.NAME}. All rights reserved.
          </p>
          <p className="text-xs text-slate-light font-mono">
            Built for professionals who value privacy.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
