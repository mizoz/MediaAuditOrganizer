import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/data/snapshot.json').then(r => r.json()),
      fetch('/data/tasks.json').then(r => r.json())
    ]).then(([snapshotData, tasksData]) => {
      setSnapshot(snapshotData);
      setTasks(tasksData);
      setLoading(false);
    }).catch(err => {
      console.error('Failed to load dashboard data:', err);
      setLoading(false);
    });
  }, []);

  if (loading || !snapshot) {
    return <div className="min-h-screen bg-obsidian-900 flex items-center justify-center text-slate-100">Loading...</div>;
  }

  return (
    <div className="dashboard min-h-screen bg-obsidian-900 text-slate-100 p-8">
      {/* SECTION 1: Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-100">MediaAuditOrganizer</h1>
        <span className="inline-block mt-2 px-3 py-1 bg-green-600 text-white text-sm rounded badge">
          ALPHA_BATCH — LIVE
        </span>
        <p className="mt-2 text-slate-400">Last updated: {snapshot.generated_at}</p>
      </header>

      {/* SECTION 2: Stats Row (4 cards) */}
      <div className="stats-row grid grid-cols-4 gap-6 mb-8">
        <div className="card bg-slate-900 rounded-lg border border-slate-800 p-6">
          <h3 className="text-sm text-slate-400 mb-2">Total Files</h3>
          <p className="text-3xl font-bold text-slate-100">{snapshot.media.total_files.toLocaleString()}</p>
        </div>
        <div className="card bg-slate-900 rounded-lg border border-slate-800 p-6">
          <h3 className="text-sm text-slate-400 mb-2">Total Size</h3>
          <p className="text-3xl font-bold text-blue-400">{snapshot.media.size_gb.toLocaleString()} GB</p>
        </div>
        <div className="card bg-slate-900 rounded-lg border border-slate-800 p-6">
          <h3 className="text-sm text-slate-400 mb-2">DB Tasks</h3>
          <p className="text-3xl font-bold text-slate-100">{snapshot.database.total_tasks.toLocaleString()}</p>
        </div>
        <div className="card bg-slate-900 rounded-lg border border-slate-800 p-6">
          <h3 className="text-sm text-slate-400 mb-2">SHA256 Verified</h3>
          <p className="text-3xl font-bold text-green-400">{snapshot.media.sha256_verified.toLocaleString()}</p>
        </div>
      </div>

      {/* SECTION 3: Workflow Pipeline */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-100 mb-4">Workflow Pipeline</h2>
        <div className="space-y-2">
          {snapshot.workflow.map((phase: any, i: number) => (
            <div
              key={i}
              className={`phase p-3 rounded border ${
                phase.status === 'completed'
                  ? 'bg-green-900/20 border-green-700 text-green-400'
                  : phase.status === 'active'
                  ? 'bg-blue-900/20 border-blue-700 text-blue-400'
                  : 'bg-slate-900 border-slate-700 text-slate-400'
              }`}
            >
              {phase.phase} — <span className="font-medium">{phase.status}</span>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 4: Drive Status Table */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-100 mb-4">Drive Status</h2>
        <div className="overflow-x-auto">
          <table className="w-full bg-slate-900 rounded-lg border border-slate-800">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left p-3 text-slate-400 font-medium">Name</th>
                <th className="text-left p-3 text-slate-400 font-medium">Status</th>
                <th className="text-left p-3 text-slate-400 font-medium">Files</th>
                <th className="text-left p-3 text-slate-400 font-medium">Size</th>
                <th className="text-left p-3 text-slate-400 font-medium">Verified</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.drives.map((drive: any, i: number) => (
                <tr key={i} className="border-b border-slate-800 last:border-0">
                  <td className="p-3 text-slate-200">{drive.name}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      drive.status === 'connected' ? 'bg-green-900/50 text-green-400' : 'bg-slate-700 text-slate-400'
                    }`}>
                      {drive.status}
                    </span>
                  </td>
                  <td className="p-3 text-slate-200">{drive.files.toLocaleString()}</td>
                  <td className="p-3 text-slate-200">{drive.size_gb.toLocaleString()} GB</td>
                  <td className="p-3 text-slate-400 text-sm">{new Date(drive.verified_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* SECTION 5: Recent Tasks Table */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-100 mb-4">Recent Tasks</h2>
        <div className="overflow-x-auto">
          <table className="w-full bg-slate-900 rounded-lg border border-slate-800">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left p-3 text-slate-400 font-medium">ID</th>
                <th className="text-left p-3 text-slate-400 font-medium">Type</th>
                <th className="text-left p-3 text-slate-400 font-medium">Status</th>
                <th className="text-left p-3 text-slate-400 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {tasks.slice(0, 10).map((task: any) => (
                <tr key={task.task_id} className="border-b border-slate-800 last:border-0">
                  <td className="p-3 text-slate-200 font-mono text-sm">{task.task_id}</td>
                  <td className="p-3 text-slate-200">{task.task_type}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      task.status === 'completed'
                        ? 'bg-green-900/50 text-green-400'
                        : task.status === 'active'
                        ? 'bg-blue-900/50 text-blue-400'
                        : 'bg-slate-700 text-slate-400'
                    }`}>
                      {task.status}
                    </span>
                  </td>
                  <td className="p-3 text-slate-400 text-sm">{new Date(task.started_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* SECTION 6: System Info Footer */}
      <footer className="border-t border-slate-800 pt-6 mt-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
          <div>
            <span className="text-slate-400">OS: </span>
            <span className="text-slate-200">{snapshot.system.os}</span>
          </div>
          <div>
            <span className="text-slate-400">GPU: </span>
            <span className="text-slate-200">{snapshot.system.gpu}</span>
          </div>
          <div>
            <span className="text-slate-400">FFmpeg NVENC: </span>
            <span>{snapshot.system.ffmpeg_nvenc ? '✅' : '❌'}</span>
          </div>
          <div>
            <span className="text-slate-400">Tauri Backend: </span>
            <span className="text-slate-200">{snapshot.system.tauri_backend}</span>
          </div>
          <div>
            <span className="text-slate-400">Last Commit: </span>
            <span className="text-slate-200 font-mono text-xs">{snapshot.system.last_commit}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
