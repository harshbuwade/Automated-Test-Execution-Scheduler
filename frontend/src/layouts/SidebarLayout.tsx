import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Calendar,
  ChevronRight,
  FileCode,
  LayoutDashboard,
  Menu,
  PlaySquare,
  User as UserIcon,
  X,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const SidebarLayout: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const getPageTitle = (path: string) => {
    if (path === '/') return 'Dashboard Overview';
    if (path.startsWith('/tests')) return 'Test Script Definitions';
    if (path.startsWith('/schedules')) return 'Automated Schedules';
    if (path.startsWith('/executions/') && path !== '/executions') return 'Execution Details';
    if (path.startsWith('/executions')) return 'Execution Logs & History';
    return 'Test Execution Scheduler';
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Tests', path: '/tests', icon: FileCode },
    { name: 'Schedules', path: '/schedules', icon: Calendar },
    { name: 'Executions', path: '/executions', icon: PlaySquare },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      {/* Mobile Top Header */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-lg text-white">
            <PlaySquare className="w-5 h-5" />
          </div>
          <span className="font-bold text-slate-100 tracking-tight text-sm">TestScheduler</span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 text-slate-400 hover:text-white rounded-lg focus:outline-none"
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar Overlay for Mobile */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 bg-slate-900/90 backdrop-blur-xl border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-300 ease-in-out ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div>
          {/* Logo Branding */}
          <div className="p-6 flex items-center space-x-3 border-b border-slate-800/60">
            <div className="p-2 bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-cyan-500/20 text-white">
              <PlaySquare className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-slate-100 text-base leading-tight tracking-tight">Test Scheduler</h1>
              <p className="text-xs font-mono text-cyan-400">v1.0.0 • Automation</p>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="p-4 space-y-1.5">
            <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Navigation</div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path);

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-5 h-5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span>{item.name}</span>
                  </div>
                  {isActive && <ChevronRight className="w-4 h-4 text-cyan-400" />}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Card */}
        <div className="p-4 border-t border-slate-800/60">
          <div className="bg-slate-950/60 rounded-xl p-3.5 border border-slate-800/80 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
              {user?.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-200 truncate">{user?.name || 'Default User'}</p>
              <p className="text-xs text-slate-400 truncate">{user?.email || 'demo@scheduler.local'}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content View */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/60 px-6 flex items-center justify-between sticky top-0 z-30">
          <div>
            <h2 className="text-lg font-bold text-slate-100 tracking-tight">{getPageTitle(location.pathname)}</h2>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>API Connected</span>
            </div>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
