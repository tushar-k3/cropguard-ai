import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

export default function ProfilePage() {
  const { t }          = useTranslation();
  const { user, updateUser } = useAuth();

  const [form, setForm] = useState({
    first_name: '',
    last_name:  '',
    phone:      '',
    location:   '',
    farm_size:  '',
    preferred_language: 'en',
  });

  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [success,  setSuccess]  = useState('');
  const [error,    setError]    = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await api.get('/auth/profile/');
        const data     = response.data;
        setForm({
          first_name:         data.first_name  || '',
          last_name:          data.last_name   || '',
          phone:              data.phone       || '',
          location:           data.location    || '',
          farm_size:          data.farm_size   || '',
          preferred_language: data.preferred_language || 'en',
        });
      } catch {
        setError(t('common.error'));
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setSuccess('');
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await api.patch('/auth/profile/', form);
      updateUser({ first_name: form.first_name, last_name: form.last_name });
      setSuccess(t('profile.save_success'));
    } catch {
      setError(t('common.error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-2xl mx-auto px-6 pt-28 pb-16">

        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-primary-600/30 border-2 border-primary-500/50 rounded-full flex items-center justify-center text-4xl mx-auto mb-4">
            👤
          </div>
          <h1 className="text-2xl font-bold">{t('profile.title')}</h1>
          <p className="text-gray-400 text-sm mt-1">@{user?.username}</p>
        </div>

        {success && (
          <div className="bg-primary-600/20 border border-primary-500/40 text-primary-300 rounded-xl px-4 py-3 text-sm mb-6 text-center">
            ✅ {success}
          </div>
        )}

        {error && (
          <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="glass-card p-12 text-center">
            <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="glass-card p-8 space-y-5">

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  {t('auth.first_name')}
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={form.first_name}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  {t('auth.last_name')}
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={form.last_name}
                  onChange={handleChange}
                  className="input-field"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('auth.phone')}
              </label>
              <input
                type="tel"
                name="phone"
                value={form.phone}
                onChange={handleChange}
                className="input-field"
                placeholder="+91 98765 43210"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('auth.location')}
              </label>
              <input
                type="text"
                name="location"
                value={form.location}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g. Nashik, Maharashtra"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('profile.farm_size')}
              </label>
              <input
                type="text"
                name="farm_size"
                value={form.farm_size}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g. 5 acres"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('auth.preferred_language')}
              </label>
              <select
                name="preferred_language"
                value={form.preferred_language}
                onChange={handleChange}
                className="input-field"
                style={{ colorScheme: 'dark' }}
              >
                <option value="en" style={{ backgroundColor: '#111827', color: '#f3f4f6' }}>English</option>
                <option value="hi" style={{ backgroundColor: '#111827', color: '#f3f4f6' }}>हिंदी</option>
                <option value="mr" style={{ backgroundColor: '#111827', color: '#f3f4f6' }}>मराठी</option>
              </select>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={saving}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {saving ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {t('profile.saving')}
                  </>
                ) : (
                  `💾 ${t('profile.save_btn')}`
                )}
              </button>
            </div>

          </form>
        )}

        {/* Account info */}
        <div className="glass-card p-6 mt-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
            {t('profile.account_info')}
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">{t('auth.username')}</span>
              <span className="text-white font-medium">@{user?.username}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">{t('auth.email')}</span>
              <span className="text-white font-medium">{user?.email}</span>
            </div>
            {user?.is_staff && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">{t('profile.role')}</span>
                <span className="text-purple-300 font-medium">⚙️ Admin</span>
              </div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}