import React, { useState } from 'react';
import { motion } from 'framer-motion';
import WaitlistForm from './WaitlistForm';

// Brand config — swap name in one place
const BRAND = {
  NAME: 'AXIOMATIC', // CHANGE THIS ONE VARIABLE
  TAGLINE: 'Local-First Media Organization',
};

interface HeroProps {
  onWaitlistSubmit?: (email: string) => Promise<void>;
}

const Hero: React.FC<HeroProps> = ({ onWaitlistSubmit }) => {
  return (
    <section className="relative min-h-screen flex items-center justify-center bg-obsidian overflow-hidden">
      {/* Background grid pattern */}
      <div className="absolute inset-0 opacity-10">
        <div
          className="w-full h-full"
          style={{
            backgroundImage: `
              linear-gradient(rgba(74, 85, 104, 0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(74, 85, 104, 0.3) 1px, transparent 1px)
            `,
            backgroundSize: '48px 48px',
          }}
        />
      </div>

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-obsidian via-obsidian/95 to-obsidian" />

      {/* Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-8 border border-slate rounded-md bg-slate/10">
            <span className="w-2 h-2 rounded-full bg-cyber-lime animate-pulse" />
            <span className="text-sm text-slate-light font-mono">
              ALPHA WAITLIST OPEN
            </span>
          </div>

          {/* Headline */}
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white leading-tight mb-6">
            Your Drive is{' '}
            <span className="text-slate-light">Chaos</span>.
            <br />
            We Build{' '}
            <span className="text-cyber-lime">Order</span>.
          </h1>

          {/* Subhead */}
          <p className="text-lg md:text-xl text-slate-light max-w-2xl mb-8 leading-relaxed">
            {BRAND.NAME} is a professional media management system that audits, 
            deduplicates, and organizes your photo/video libraries.{' '}
            <span className="text-white font-medium">
              Everything runs locally on your machine. We never see your data.
            </span>
          </p>

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-6 mb-12 max-w-xl">
            <div className="border-l-2 border-cyber-lime pl-4">
              <div className="text-2xl font-bold text-white font-mono">12</div>
              <div className="text-sm text-slate-light">Specialized Agents</div>
            </div>
            <div className="border-l-2 border-slate pl-4">
              <div className="text-2xl font-bold text-white font-mono">0</div>
              <div className="text-sm text-slate-light">Cloud Uploads</div>
            </div>
            <div className="border-l-2 border-slate pl-4">
              <div className="text-2xl font-bold text-white font-mono">100%</div>
              <div className="text-sm text-slate-light">Local Processing</div>
            </div>
          </div>

          {/* Waitlist CTA */}
          <div className="max-w-md">
            <WaitlistForm onSubmit={onWaitlistSubmit} />
          </div>

          {/* Privacy reassurance */}
          <p className="mt-6 text-sm text-slate-light flex items-center gap-2">
            <svg
              className="w-4 h-4 text-cyber-lime"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
            No spam. Unsubscribe anytime. Your email stays local.
          </p>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 border-2 border-slate rounded-full flex justify-center pt-2"
        >
          <div className="w-1 h-2 bg-slate rounded-full" />
        </motion.div>
      </motion.div>
    </section>
  );
};

export default Hero;
