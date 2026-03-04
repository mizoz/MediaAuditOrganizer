import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface PasswordGateProps {
  children: React.ReactNode;
}

const CORRECT_PASSWORD = 'axiomatic2026'; // In production, this would be env var

export default function PasswordGate({ children }: PasswordGateProps) {
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === CORRECT_PASSWORD) {
      setIsAuthenticated(true);
      setError('');
    } else {
      setError('Incorrect password');
      setPassword('');
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  if (isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-obsidian-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 rounded-lg border border-slate-800 p-8">
        <h2 className="text-2xl font-bold text-slate-100 mb-2">
          Dashboard Access
        </h2>
        <p className="text-slate-400 mb-6">
          Enter password to continue
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-600"
              placeholder="Password"
              autoFocus
            />
            {error && (
              <p className="mt-2 text-sm text-red-400">{error}</p>
            )}
          </div>
          
          <div className="flex gap-3">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
            >
              Continue
            </button>
            <button
              type="button"
              onClick={handleBack}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg font-medium transition-colors"
            >
              Back
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
