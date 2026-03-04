import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface WaitlistFormProps {
  onSubmit?: (email: string) => Promise<void>;
  apiEndpoint?: string;
}

type FormState = 'idle' | 'loading' | 'success' | 'error';

const WaitlistForm: React.FC<WaitlistFormProps> = ({
  onSubmit,
  apiEndpoint = '/api/waitlist',
}) => {
  const [email, setEmail] = useState('');
  const [state, setState] = useState<FormState>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const validateEmail = (email: string): boolean => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateEmail(email)) {
      setState('error');
      setErrorMessage('Please enter a valid email address');
      return;
    }

    setState('loading');
    setErrorMessage('');

    try {
      // Mock API call - replace with actual endpoint
      if (onSubmit) {
        await onSubmit(email);
      } else {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mock response (always success for demo)
        console.log(`Waitlist submission: ${email} → ${apiEndpoint}`);
      }
      
      setState('success');
      setEmail('');
    } catch (error) {
      setState('error');
      setErrorMessage('Something went wrong. Please try again.');
    }
  };

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {state === 'idle' || state === 'loading' || state === 'error' ? (
          <motion.form
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onSubmit={handleSubmit}
            className="flex flex-col sm:flex-row gap-3"
          >
            {/* Email input */}
            <div className="flex-1">
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (state === 'error') setState('idle');
                }}
                disabled={state === 'loading'}
                placeholder="you@studio.com"
                className={`w-full px-4 py-3 bg-slate/10 border rounded-md font-mono text-sm transition-all duration-200
                  ${state === 'error'
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
                    : 'border-slate focus:border-cyber-lime focus:ring-cyber-lime/20'
                  }
                  focus:outline-none focus:ring-2 text-white placeholder-slate-light
                  disabled:opacity-50 disabled:cursor-not-allowed`}
                aria-invalid={state === 'error'}
                aria-describedby={state === 'error' ? 'email-error' : undefined}
              />
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={state === 'loading' || !email}
              className="px-6 py-3 bg-cyber-lime hover:bg-cyber-lime-hover active:bg-cyber-lime-active 
                text-obsidian font-semibold rounded-md transition-all duration-150
                disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-cyber-lime
                whitespace-nowrap flex items-center justify-center gap-2 min-w-[160px]"
            >
              {state === 'loading' ? (
                <>
                  <svg
                    className="animate-spin w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>Joining...</span>
                </>
              ) : (
                <span>Join Alpha Waitlist</span>
              )}
            </button>
          </motion.form>
        ) : null}

        {/* Success state */}
        {state === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="p-4 border border-cyber-lime/30 bg-cyber-lime/10 rounded-md"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-cyber-lime flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-obsidian"
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
              </div>
              <div>
                <div className="font-semibold text-white">
                  You're on the list!
                </div>
                <div className="text-sm text-slate-light">
                  We'll notify you when alpha access opens.
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Error state message */}
        {state === 'error' && (
          <motion.p
            key="error"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            id="email-error"
            className="mt-2 text-sm text-red-400 font-mono"
          >
            {errorMessage}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
};

export default WaitlistForm;
