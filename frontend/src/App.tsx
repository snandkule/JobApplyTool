import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { LayoutDashboard, List, MessageSquare, Settings, Play } from 'lucide-react';
import Dashboard from './components/Dashboard';
import ApplicationQueue from './components/ApplicationQueue';
import PendingQuestions from './components/PendingQuestions';
import DaemonControl from './components/DaemonControl';

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-md">
          <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-800">Job Apply Tool</h1>
            <p className="text-sm text-gray-500">AI-Powered Automation</p>
          </div>

          <nav className="mt-6">
            <NavLink to="/" icon={<LayoutDashboard size={20} />}>
              Dashboard
            </NavLink>
            <NavLink to="/queue" icon={<List size={20} />}>
              Application Queue
            </NavLink>
            <NavLink to="/questions" icon={<MessageSquare size={20} />}>
              Pending Questions
            </NavLink>
            <NavLink to="/daemon" icon={<Play size={20} />}>
              Daemon Control
            </NavLink>
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/queue" element={<ApplicationQueue />} />
            <Route path="/questions" element={<PendingQuestions />} />
            <Route path="/daemon" element={<DaemonControl />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

function NavLink({ to, icon, children }: { to: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 px-6 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}

export default App;
