import { Link } from 'react-router-dom';

interface LandingPageProps {
  className?: string;
}

export function LandingPage(_props: LandingPageProps) {
  return (
    <div className="min-h-screen bg-obsidian-900 text-slate-100">
      {/* Hero Section */}
      <header className="container mx-auto px-6 py-16">
        <h1 className="text-5xl font-bold mb-4">
          AXIOMATIC
        </h1>
        <p className="text-xl text-slate-400 mb-8">
          Local-First Media Organization for Professionals
        </p>
        <Link 
          to="/dashboard" 
          className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
        >
          Open Dashboard →
        </Link>
      </header>

      {/* Features */}
      <section className="container mx-auto px-6 py-12">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="p-6 bg-slate-900 rounded-lg border border-slate-800">
            <h3 className="text-lg font-semibold mb-2">12 Specialized Agents</h3>
            <p className="text-slate-400">Orchestrated workflow for media processing</p>
          </div>
          <div className="p-6 bg-slate-900 rounded-lg border border-slate-800">
            <h3 className="text-lg font-semibold mb-2">100% Local Processing</h3>
            <p className="text-slate-400">Your data never leaves your machine</p>
          </div>
          <div className="p-6 bg-slate-900 rounded-lg border border-slate-800">
            <h3 className="text-lg font-semibold mb-2">Zero Cloud Dependencies</h3>
            <p className="text-slate-400">Complete privacy and control</p>
          </div>
        </div>
      </section>
    </div>
  );
}
