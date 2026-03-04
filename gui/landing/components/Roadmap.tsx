import React from 'react';
import { motion } from 'framer-motion';

const PHASES = [
  {
    phase: 'Phase 1',
    title: 'Local Alpha',
    timeframe: 'Q1 2026',
    status: 'current',
    features: [
      'Core audit & metadata extraction',
      'Hash-based duplicate detection',
      'Batch rename with patterns',
      'Local transfer with verification',
      'SQLite database tracking',
      'PDF/HTML report generation',
    ],
    icon: '🎯',
  },
  {
    phase: 'Phase 2',
    title: 'GPU Acceleration',
    timeframe: 'Q2 2026',
    status: 'upcoming',
    features: [
      'GPU-accelerated hash computation',
      'Perceptual duplicate detection (near-dupes)',
      'Video thumbnail generation',
      '10x faster processing on large libraries',
      'CUDA/Metal support',
      'Progressive scan optimization',
    ],
    icon: '⚡',
  },
  {
    phase: 'Phase 3',
    title: 'Team/Studio Sync',
    timeframe: 'Q4 2026',
    status: 'planned',
    features: [
      'Multi-user workflow coordination',
      'Shared catalog synchronization',
      'Conflict resolution for team edits',
      'Studio network deployment',
      'Role-based access control',
      'Centralized backup management',
    ],
    icon: '👥',
  },
];

interface RoadmapProps {
  title?: string;
  subtitle?: string;
}

const Roadmap: React.FC<RoadmapProps> = ({
  title = 'The Roadmap',
  subtitle = '6-month vision: from local alpha to studio-grade workflow',
}) => {
  return (
    <section className="py-24 bg-obsidian/50 border-t border-slate/30">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {title}
          </h2>
          <p className="text-lg text-slate-light max-w-2xl">
            {subtitle}
          </p>
        </motion.div>

        {/* Timeline */}
        <div className="relative">
          {/* Connection line */}
          <div className="absolute top-8 left-0 right-0 h-0.5 bg-gradient-to-r from-cyber-lime via-slate to-slate/30 hidden lg:block" />

          {/* Phases */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {PHASES.map((phase, index) => (
              <motion.div
                key={phase.phase}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-100px' }}
                transition={{ duration: 0.5, delay: index * 0.15 }}
                className={`relative p-6 rounded-lg border ${
                  phase.status === 'current'
                    ? 'border-cyber-lime/50 bg-cyber-lime/5'
                    : 'border-slate/50 bg-slate/5'
                }`}
              >
                {/* Phase indicator dot */}
                <div className="absolute -top-3 left-6 w-6 h-6 rounded-full bg-obsidian border-2 flex items-center justify-center
                  ${phase.status === 'current' ? 'border-cyber-lime' : 'border-slate'}">
                  <div className={`w-2.5 h-2.5 rounded-full ${
                    phase.status === 'current' ? 'bg-cyber-lime' : 'bg-slate'
                  }`} />
                </div>

                {/* Phase label */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">{phase.icon}</span>
                  <div>
                    <div className="text-xs font-mono text-cyber-lime uppercase tracking-wide">
                      {phase.phase}
                    </div>
                    <div className="text-sm text-slate-light font-mono">
                      {phase.timeframe}
                    </div>
                  </div>
                </div>

                {/* Title */}
                <h3 className={`text-xl font-bold mb-4 ${
                  phase.status === 'current' ? 'text-white' : 'text-slate-light'
                }`}>
                  {phase.title}
                </h3>

                {/* Features list */}
                <ul className="space-y-2">
                  {phase.features.map((feature, featureIndex) => (
                    <li
                      key={featureIndex}
                      className="flex items-start gap-2 text-sm text-slate-light"
                    >
                      <svg
                        className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                          phase.status === 'current'
                            ? 'text-cyber-lime'
                            : 'text-slate'
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* Status badge */}
                {phase.status === 'current' && (
                  <div className="mt-6 inline-flex items-center gap-2 px-3 py-1.5 bg-cyber-lime/10 border border-cyber-lime/30 rounded-md">
                    <span className="w-2 h-2 rounded-full bg-cyber-lime animate-pulse" />
                    <span className="text-xs font-mono text-cyber-lime">
                      IN DEVELOPMENT
                    </span>
                  </div>
                )}

                {phase.status === 'upcoming' && (
                  <div className="mt-6 inline-flex items-center gap-2 px-3 py-1.5 bg-slate/10 border border-slate/30 rounded-md">
                    <span className="text-xs font-mono text-slate-light">
                      NEXT
                    </span>
                  </div>
                )}

                {phase.status === 'planned' && (
                  <div className="mt-6 inline-flex items-center gap-2 px-3 py-1.5 bg-slate/10 border border-slate/30 rounded-md">
                    <span className="text-xs font-mono text-slate-light">
                      PLANNED
                    </span>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-16 text-center"
        >
          <p className="text-lg text-slate-light mb-6">
            Join the waitlist to get early access to each phase.
          </p>
          <div className="inline-flex items-center gap-2 text-cyber-lime font-mono text-sm">
            <span>Alpha access opens Q1 2026</span>
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 8l4 4m0 0l-4 4m4-4H3"
              />
            </svg>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Roadmap;
