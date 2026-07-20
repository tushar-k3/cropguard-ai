import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';


function StatCard({ icon, label, value, sub, color = 'primary' }) {
  const colorMap = {
    primary: 'text-primary-400 bg-primary-600/20 border-primary-500/30',
    earth: 'text-earth-400 bg-earth-600/20 border-earth-500/30',
    blue: 'text-blue-400 bg-blue-600/20 border-blue-500/30',
    purple: 'text-purple-400 bg-purple-600/20 border-purple-500/30',
    red: 'text-red-400 bg-red-600/20 border-red-500/30',
  };

  return (
    <div className="glass-card p-6">
      <div
        className={`inline-flex items-center justify-center w-12 h-12 rounded-xl border text-2xl mb-4 ${
          colorMap[color] || colorMap.primary
        }`}
      >
        {icon}
      </div>

      <div className="text-3xl font-bold text-white mb-1">
        {value ?? 0}
      </div>

      <div className="text-gray-400 text-sm">
        {label}
      </div>

      {sub && (
        <div className="text-gray-600 text-xs mt-1">
          {sub}
        </div>
      )}
    </div>
  );
}


function TopList({ title, items, keyField, countField, icon }) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wide mb-4">
        {icon} {title}
      </h3>

      <div className="space-y-3">
        {items.map((item, i) => (
          <div
            key={`${item[keyField] || 'item'}-${i}`}
            className="flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <span className="text-gray-500 text-xs w-4">
                {i + 1}.
              </span>

              <span className="text-white text-sm capitalize">
                {item[keyField] || 'Unknown'}
              </span>
            </div>

            <span className="text-primary-400 text-sm font-semibold">
              {item[countField] ?? 0}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}


export default function AdminPage() {
  const { user } = useAuth();
  const { t } = useTranslation();

  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError('');

        const response = await api.get('/admin/stats/');
        setStats(response.data);
      } catch (err) {
        console.error('Failed to load admin statistics:', err);

        setError(
          err.response?.data?.error ||
          err.response?.data?.detail ||
          t('common.error')
        );
      } finally {
        setLoading(false);
      }
    };

    if (user?.is_staff) {
      fetchStats();
    } else {
      setLoading(false);
    }
  }, [user, t]);

  // Redirect non-staff users
  if (user && !user.is_staff) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-1">
            ⚙️ Admin Dashboard
          </h1>

          <p className="text-gray-400">
            Platform statistics and system overview
          </p>
        </div>


        {/* Django Admin link */}
        <div className="glass-card p-4 mb-8 flex items-center justify-between">
          <div>
            <p className="text-white font-medium text-sm">
              Django Admin Panel
            </p>

            <p className="text-gray-400 text-xs mt-1">
              Manage users, scans, and all database records
            </p>
          </div>

          <a
            href="http://127.0.0.1:8000/admin/"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-sm py-2 px-4"
          >
            Open Django Admin →
          </a>
        </div>


        {/* Error */}
        {error && (
          <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}


        {/* Loading */}
        {loading && (
          <div className="glass-card p-12 text-center">
            <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />

            <p className="text-gray-400">
              Loading statistics...
            </p>
          </div>
        )}


        {/* Dashboard Statistics */}
        {stats && !loading && (
          <>

            {/* Main Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">

              <StatCard
                icon="👥"
                label="Total Users"
                value={stats.users?.total ?? 0}
                sub={`${stats.users?.active ?? 0} active`}
                color="primary"
              />

              <StatCard
                icon="🔬"
                label="Total Scans"
                value={stats.scans?.total ?? 0}
                sub={`${stats.scans?.diseased ?? 0} diseased`}
                color="earth"
              />

              <StatCard
                icon="🌾"
                label="Crop Recs"
                value={stats.crops?.total_recommendations ?? 0}
                color="blue"
              />

              <StatCard
                icon="🧪"
                label="Fertilizer Recs"
                value={stats.fertilizers?.total_recommendations ?? 0}
                color="purple"
              />

            </div>


            {/* Scan Breakdown */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">

              <StatCard
                icon="✅"
                label="Healthy Scans"
                value={stats.scans?.healthy ?? 0}
                color="primary"
              />

              <StatCard
                icon="⚠️"
                label="Diseased Scans"
                value={stats.scans?.diseased ?? 0}
                color="red"
              />

              <StatCard
                icon="🌐"
                label="Kindwise Scans"
                value={stats.scans?.kindwise ?? 0}
                color="blue"
              />

              <StatCard
                icon="💻"
                label="Offline Scans"
                value={stats.scans?.offline ?? 0}
                color="earth"
              />

            </div>


            {/* Top Lists */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">

              <TopList
                title="Top Recommended Crops"
                items={stats.crops?.top_crops}
                keyField="recommended_crop"
                countField="count"
                icon="🌾"
              />

              <TopList
                title="Top Fertilizers"
                items={stats.fertilizers?.top_fertilizers}
                keyField="recommended_fertilizer"
                countField="count"
                icon="🧪"
              />

              <TopList
                title="Most Common Diseases"
                items={stats.top_diseases}
                keyField="plant_name"
                countField="count"
                icon="🦠"
              />

            </div>


            {/* Recent Users */}
            <div className="glass-card p-6">

              <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wide mb-4">
                👥 Recent Users
              </h3>

              <div className="overflow-x-auto">

                <table className="w-full text-sm">

                  <thead>
                    <tr className="border-b border-white/10">

                      <th className="text-left text-gray-400 font-medium pb-3 pr-4">
                        Username
                      </th>

                      <th className="text-left text-gray-400 font-medium pb-3 pr-4">
                        Email
                      </th>

                      <th className="text-left text-gray-400 font-medium pb-3 pr-4">
                        Joined
                      </th>

                      <th className="text-left text-gray-400 font-medium pb-3">
                        Role
                      </th>

                    </tr>
                  </thead>

                  <tbody className="divide-y divide-white/5">

                    {(stats.recent_users || []).map((u, i) => (
                      <tr key={u.id || u.username || i}>

                        <td className="py-3 pr-4 text-white font-medium">
                          {u.username}
                        </td>

                        <td className="py-3 pr-4 text-gray-400">
                          {u.email || '-'}
                        </td>

                        <td className="py-3 pr-4 text-gray-400">
                          {u.date_joined}
                        </td>

                        <td className="py-3">

                          <span
                            className={`px-2 py-1 rounded-lg text-xs font-medium ${
                              u.is_staff
                                ? 'bg-purple-600/20 text-purple-300'
                                : 'bg-primary-600/20 text-primary-300'
                            }`}
                          >
                            {u.is_staff ? 'Admin' : 'Farmer'}
                          </span>

                        </td>

                      </tr>
                    ))}

                  </tbody>

                </table>

              </div>
            </div>

          </>
        )}

      </main>
    </div>
  );
}