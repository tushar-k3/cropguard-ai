import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import api from '../api/axios';

function StatCard({ icon, label, value, color = 'primary' }) {
  const colorMap = {
    primary: 'text-primary-400 bg-primary-600/20 border-primary-500/30',
    earth:   'text-earth-400 bg-earth-600/20 border-earth-500/30',
    blue:    'text-blue-400 bg-blue-600/20 border-blue-500/30',
    purple:  'text-purple-400 bg-purple-600/20 border-purple-500/30',
  };
  return (
    <div className="glass-card p-6">
      <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl border text-2xl mb-4 ${colorMap[color]}`}>
        {icon}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-gray-400 text-sm">{label}</div>
    </div>
  );
}

function ActionCard({ icon, title, description, to, badge }) {
  return (
    <Link to={to} className="glass-card p-6 hover:bg-white/15 transition-all duration-300 group block">
      <div className="flex items-start justify-between mb-4">
        <div className="text-3xl group-hover:scale-110 transition-transform duration-300">
          {icon}
        </div>
        {badge && (
          <span className="bg-primary-600/30 text-primary-300 text-xs font-medium px-2 py-1 rounded-full border border-primary-500/30">
            {badge}
          </span>
        )}
      </div>
      <h3 className="text-white font-semibold mb-1">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
    </Link>
  );
}

export default function DashboardPage() {
  const { t }    = useTranslation();
  const { user } = useAuth();

  const [stats,   setStats]   = useState({ scans: 0, diseases: 0, crops: 0, reports: 0 });
  const [profile, setProfile] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [profileRes, scansRes, cropRes, fertRes] = await Promise.all([
          api.get('/auth/profile/'),
          api.get('/scan/history/'),
          api.get('/crop/history/'),
          api.get('/fertilizer/history/'),
        ]);

        setProfile(profileRes.data);

        const scans    = scansRes.data.results || [];
        const diseases = scans.filter(s => !s.is_healthy).length;
        const crops    = cropRes.data.count || 0;
        const reports  = scans.length;

        setStats({ scans: scans.length, diseases, crops, reports });
        setRecentScans(scans.slice(0, 3));
      } catch {
        // Non-critical
      } finally {
        setLoadingStats(false);
      }
    };
    fetchData();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('dashboard.good_morning');
    if (hour < 17) return t('dashboard.good_afternoon');
    return t('dashboard.good_evening');
  };

  const quickActions = [
    { icon: '🔬', title: t('dashboard.action_scan'),       description: t('dashboard.action_scan_desc'),       to: '/scanner',    badge: t('dashboard.badge_ai') },
    { icon: '🌾', title: t('dashboard.action_crop'),       description: t('dashboard.action_crop_desc'),       to: '/crop' },
    { icon: '🧪', title: t('dashboard.action_fertilizer'), description: t('dashboard.action_fertilizer_desc'), to: '/fertilizer' },
    { icon: '💧', title: t('dashboard.action_irrigation'), description: t('dashboard.action_irrigation_desc'), to: '/irrigation' },
    { icon: '🌤️', title: t('dashboard.action_weather'),    description: t('dashboard.action_weather_desc'),    to: '/weather' },
    { icon: '🤖', title: t('dashboard.action_chatbot'),    description: t('dashboard.action_chatbot_desc'),    to: '/chatbot' },
    { icon: '📈', title: t('dashboard.action_market'),     description: t('dashboard.action_market_desc'),     to: '/market' },
    { icon: '📄', title: t('dashboard.action_reports'),    description: t('dashboard.action_reports_desc'),    to: '/reports' },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 pt-28 pb-16">

        {/* Welcome Banner */}
        <div className="glass-card p-8 mb-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative">
            <p className="text-primary-400 font-medium mb-1">{getGreeting()}</p>
            <h1 className="text-3xl font-bold text-white mb-2">
              {user?.first_name || user?.username} 👋
            </h1>
            <p className="text-gray-400">
              {profile?.location
                ? `📍 ${profile.location}`
                : t('dashboard.welcome_subtitle')}
            </p>
          </div>
        </div>

        {/* Real Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon="🔬" label={t('dashboard.stat_scans')}    value={loadingStats ? '...' : stats.scans}    color="primary" />
          <StatCard icon="🦠" label={t('dashboard.stat_diseases')} value={loadingStats ? '...' : stats.diseases} color="earth" />
          <StatCard icon="🌾" label={t('dashboard.stat_crops')}    value={loadingStats ? '...' : stats.crops}    color="blue" />
          <StatCard icon="📄" label={t('dashboard.stat_reports')}  value={loadingStats ? '...' : stats.reports}  color="purple" />
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">{t('dashboard.quick_actions')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action, index) => (
              <ActionCard key={index} {...action} />
            ))}
          </div>
        </div>

        {/* Recent Scans */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">{t('dashboard.recent_activity')}</h2>
            {recentScans.length > 0 && (
              <Link to="/reports" className="text-primary-400 text-sm hover:text-primary-300">
                {t('dashboard.view_all')} →
              </Link>
            )}
          </div>

          {recentScans.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="text-5xl mb-4">🌱</div>
              <p className="text-gray-400 text-sm max-w-xs">
                {t('dashboard.no_activity')}
              </p>
              <Link to="/scanner" className="btn-primary mt-6 text-sm py-2 px-5">
                {t('dashboard.start_scanning')}
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentScans.map((scan) => (
                <div key={scan.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                  <div className="flex items-center gap-4">
                    <span className="text-2xl">
                      {scan.is_healthy ? '🌿' : '⚠️'}
                    </span>
                    <div>
                      <p className="text-white text-sm font-medium">
                        {scan.plant_name || 'Unknown Plant'}
                      </p>
                      <p className="text-gray-500 text-xs">
                        {new Date(scan.created_at).toLocaleDateString('en-IN')}
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-3 py-1 rounded-full ${
                    scan.is_healthy
                      ? 'bg-primary-600/20 text-primary-300'
                      : 'bg-red-600/20 text-red-300'
                  }`}>
                    {scan.is_healthy ? 'Healthy' : 'Diseased'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

      </main>
    </div>
  );
}