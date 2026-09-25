import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { healthService } from '@/services/health';
import { LogOut, Activity, Landmark } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dbLatency, setDbLatency] = useState<number | null>(null);
  const [dbHealthy, setDbHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = () => {
      healthService
        .getHealth()
        .then((res) => {
          if (isMounted) {
            setDbHealthy(res.status === 'healthy');
            setDbLatency(res.db_latency_ms);
          }
        })
        .catch(() => {
          if (isMounted) setDbHealthy(false);
        });
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const getScopeBadge = () => {
    if (!user) return null;
    switch (user.role) {
      case 'MINISTRY':
        return {
          title: 'Central Governance Oversight',
          sub: 'All-India National Portfolio (36 States/UTs)',
          color: 'bg-blue-50/90 text-blue-950 border-blue-200/80',
          iconColor: 'text-blue-600',
        };
      case 'STATE_OFFICER':
        return {
          title: `State Nodal • ${user.assigned_state || 'Uttar Pradesh'}`,
          sub: 'State-Level Inter-District Monitoring',
          color: 'bg-indigo-50/90 text-indigo-950 border-indigo-200/80',
          iconColor: 'text-indigo-600',
        };
      case 'DISTRICT_OFFICER':
        return {
          title: `District Authority • ${user.assigned_district || 'PATNA'}, ${user.assigned_state || 'Bihar'}`,
          sub: 'Local Operational Queue & Sanctions',
          color: 'bg-emerald-50/90 text-emerald-950 border-emerald-200/80',
          iconColor: 'text-emerald-600',
        };
      case 'MP':
        return {
          title: `MP Portfolio • ${user.assigned_mp_name || 'SARABJEET SINGH KHALSA'}`,
          sub: 'Faridkot (SC) Parliamentary Constituency',
          color: 'bg-amber-50/90 text-amber-950 border-amber-200/80',
          iconColor: 'text-amber-600',
        };
      default:
        return { title: user.role, sub: '', color: 'bg-slate-50 text-slate-700 border-slate-200', iconColor: 'text-slate-600' };
    }
  };

  const scope = getScopeBadge();

  return (
    <header className="h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Scope Badge */}
      <div className="flex items-center gap-3">
        {scope && (
          <div className={`px-3 py-1.5 rounded-xl border text-xs flex items-center gap-2.5 shadow-xs ${scope.color}`}>
            <Landmark className={`w-4 h-4 shrink-0 ${scope.iconColor}`} />
            <div>
              <p className="font-bold leading-none tracking-tight">{scope.title}</p>
              <p className="text-[10px] opacity-75 mt-0.5">{scope.sub}</p>
            </div>
          </div>
        )}
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Live Backend Connection Indicator */}
        <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-50 border border-slate-200/90 rounded-lg text-xs text-slate-600 font-mono shadow-xs">
          <Activity className="w-3.5 h-3.5 text-slate-400" />
          <span>API:</span>
          <span
            className={`w-2 h-2 rounded-full ${
              dbHealthy === true ? 'bg-emerald-500 animate-pulse' : dbHealthy === false ? 'bg-rose-500' : 'bg-amber-400'
            }`}
          />
          <span className="font-semibold text-slate-800">
            {dbHealthy === true ? (dbLatency ? `${dbLatency}ms` : 'Online') : dbHealthy === false ? 'Offline' : 'Connecting...'}
          </span>
        </div>

        {/* User Profile & Logout */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
          <div className="text-right">
            <p className="text-xs font-bold text-slate-900 leading-tight">{user?.full_name}</p>
            <p className="text-[10px] text-slate-500 font-mono">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
