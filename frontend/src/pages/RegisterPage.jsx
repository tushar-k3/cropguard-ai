import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

export default function RegisterPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    phone: '',
    location: '',
    preferred_language: 'en',
    password: '',
    password2: '',
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    // Clear the error for this field when user starts typing
    if (errors[e.target.name]) {
      setErrors({ ...errors, [e.target.name]: '' });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const response = await api.post('/auth/register/', formData);
      const { access, refresh, user } = response.data;
      login(user, access, refresh);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      if (err.response?.data) {
        setErrors(err.response.data);
      } else {
        setErrors({ general: t('common.error') });
      }
    } finally {
      setLoading(false);
    }
  };

  const fieldError = (field) =>
    errors[field] ? (
      <p className="text-red-400 text-xs mt-1">{errors[field]}</p>
    ) : null;

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-12">

      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-lg">

        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3">
            <span className="text-3xl">🌱</span>
            <span className="text-2xl font-bold text-primary-400">CropGuard AI</span>
          </Link>
          <p className="text-gray-400 mt-2 text-sm">{t('auth.register_subtitle')}</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          <h1 className="text-2xl font-bold text-white mb-6">{t('auth.register_title')}</h1>

          {errors.general && (
            <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm mb-6">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Name row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('auth.first_name')}
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="input-field"
                  placeholder={t('auth.first_name_placeholder')}
                  required
                />
                {fieldError('first_name')}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('auth.last_name')}
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="input-field"
                  placeholder={t('auth.last_name_placeholder')}
                />
                {fieldError('last_name')}
              </div>
            </div>

            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.username')}
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className="input-field"
                placeholder={t('auth.username_placeholder')}
                required
                autoComplete="username"
              />
              {fieldError('username')}
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.email')}
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="input-field"
                placeholder={t('auth.email_placeholder')}
                required
                autoComplete="email"
              />
              {fieldError('email')}
            </div>

            {/* Phone */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.phone')}
                <span className="text-gray-500 font-normal ml-1">({t('common.optional')})</span>
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="input-field"
                placeholder={t('auth.phone_placeholder')}
              />
              {fieldError('phone')}
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.location')}
                <span className="text-gray-500 font-normal ml-1">({t('common.optional')})</span>
              </label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="input-field"
                placeholder={t('auth.location_placeholder')}
              />
              {fieldError('location')}
            </div>

            {/* Preferred language */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.preferred_language')}
              </label>
              <select
                name="preferred_language"
                value={formData.preferred_language}
                onChange={handleChange}
                className="input-field"
              >
                <option value="en">English</option>
                <option value="hi">हिंदी</option>
                <option value="mr">मराठी</option>
              </select>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.password')}
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="input-field"
                placeholder={t('auth.password_placeholder')}
                required
                autoComplete="new-password"
              />
              {fieldError('password')}
            </div>

            {/* Confirm password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.confirm_password')}
              </label>
              <input
                type="password"
                name="password2"
                value={formData.password2}
                onChange={handleChange}
                className="input-field"
                placeholder={t('auth.confirm_password_placeholder')}
                required
                autoComplete="new-password"
              />
              {fieldError('password2')}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {t('common.loading')}
                </>
              ) : (
                t('auth.register_button')
              )}
            </button>
          </form>

          <p className="text-center text-gray-400 text-sm mt-6">
            {t('auth.have_account')}{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
              {t('auth.login_link')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}