import React from 'react';
import { motion } from 'framer-motion';

// Subagent data from SUBAGENT_ORCHESTRATION_PLAN.md
const SUBAGENTS = [
  { id: 'SA-01', name: 'env-validator', purpose: 'Verify tool installations & dependencies', phase: 'Init' },
  { id: 'SA-02', name: 'config-auditor', purpose: 'Validate settings.yaml & paths', phase: 'Init' },
  { id: 'SA-03', name: 'db-init', purpose: 'Initialize SQLite schema', phase: 'Init' },
  { id: 'SA-04', name: 'drive-scanner', purpose: 'Detect mounted drives', phase: 'Detect' },
  { id: 'SA-05', name: 'audit-executor', purpose: 'Extract metadata & compute hashes', phase: 'Audit' },
  { id: 'SA-06', name: 'dedupe-analyzer', purpose: 'Find exact & near-duplicates', phase: 'Dedupe' },
  { id: 'SA-07', name: 'rename-planner', purpose: 'Generate rename preview', phase: 'Rename' },
  { id: 'SA-08', name: 'transfer-executor', purpose: 'Move files with checksum verification', phase: 'Transfer' },
  { id: 'SA-09', name: 'backup-verifier', purpose: 'Cross-check local/cloud hashes', phase: 'Verify' },
  { id: 'SA-10', name: 'report-generator', purpose: 'Generate PDF/HTML reports', phase: 'Report' },
  { id: 'SA-11', name: 'lightroom-reconciler', purpose: 'Reconcile catalog paths', phase: 'Reconcile' },
  { id: 'SA-12', name: 'cleanup-archiver', purpose: 'Archive duplicates, rotate logs', phase: 'Cleanup' },
];

const PHASE_COLORS: Record<string, string> = {
  Init: 'bg-slate',
  Detect: 'bg-blue-500',
  Audit: 'bg-purple-500',
  Dedupe: 'bg-orange-500',
  Rename: 'bg-yellow-500',
  Transfer: 'bg-green-500',
  Verify: 'bg-cyan-500',
  Report: 'bg-pink-500',
  Reconcile: 'bg-indigo-500',
  Cleanup: 'bg-red-500',
};

interface EnginePreviewProps {
  title?: string;
  subtitle?: string;
}

const EnginePreview: React.FC<EnginePreviewProps> = ({
  title = 'The Engine',
  subtitle = '12 specialized subagents working in orchestration',
}) => {
  return (
    <section className="py-24 bg-obsidian border-t border-slate/30">
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

        {/* Workflow diagram */}
        <div className="mb-16">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="flex flex-wrap items-center gap-4 text-sm font-mono text-slate-light mb-8"
          >
            <span className="text-cyber-lime">AUDIT</span>
            <span>→</span>
            <span className="text-cyber-lime">DEDUPE</span>
            <span>→</span>
            <span className="text-cyber-lime">RENAME</span>
            <span>→</span>
            <span className="text-cyber-lime">TRANSFER</span>
            <span>→</span>
            <span className="text-cyber-lime">BACKUP</span>
            <span>→</span>
            <span className="text-cyber-lime">REPORT</span>
          </motion.div>
        </div>

        {/* Subagent grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {SUBAGENTS.map((agent, index) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="group relative p-5 border border-slate/50 rounded-lg bg-slate/5 hover:border-cyber-lime/50 transition-all duration-200"
            >
              {/* Phase indicator */}
              <div className={`absolute top-0 right-0 w-16 h-16 overflow-hidden rounded-tr-lg opacity-20`}>
                <div className={`absolute -top-8 -right-8 w-20 h-20 rotate-45 ${PHASE_COLORS[agent.phase] || 'bg-slate'}`} />
              </div>

              {/* Agent ID */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-mono text-cyber-lime bg-cyber-lime/10 px-2 py-0.5 rounded">
                  {agent.id}
                </span>
                <span className="text-xs font-mono text-slate-light">
                  {agent.phase}
                </span>
              </div>

              {/* Agent name */}
              <h3 className="text-base font-semibold text-white mb-2 font-mono">
                {agent.name}
              </h3>

              {/* Purpose */}
              <p className="text-sm text-slate-light leading-relaxed">
                {agent.purpose}
              </p>

              {/* Hover effect */}
              <div className="absolute inset-0 border border-cyber-lime/0 group-hover:border-cyber-lime/30 rounded-lg transition-all duration-200 pointer-events-none" />
            </motion.div>
          ))}
        </div>

        {/* Summary stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 p-6 border border-slate/50 rounded-lg bg-slate/5"
        >
          <div>
            <div className="text-3xl font-bold text-white font-mono mb-1">12</div>
            <div className="text-sm text-slate-light">Specialized Agents</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-white font-mono mb-1">6</div>
            <div className="text-sm text-slate-light">Max Concurrent</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-white font-mono mb-1">11</div>
            <div className="text-sm text-slate-light">Workflow Phases</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-cyber-lime font-mono mb-1">0</div>
            <div className="text-sm text-slate-light">Cloud Dependencies</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default EnginePreview;
