import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'mr', label: 'मराठी' },
];

export default function LandingPage() {
  const { t, i18n } = useTranslation();
  const [apiStatus, setApiStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const changeLanguage = (code) => {
    i18n.changeLanguage(code);
  };

  const checkApiHealth = async () => {
    setLoading(true);
    setApiStatus(null);
    try {
      const response = await fetch('/api/health/');
      if (!response.ok) throw new Error('Non-200 response');
      const data = await response.json();
      setApiStatus({
        ok: true,
        message: data.message,
        database: data.database,
        time: data.timestamp,
      });
    } catch (error) {
      setApiStatus({
        ok: false,
        message: t('common.error'),
      });
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: '🌿', titleKey: 'features.plant_id_title', descKey: 'features.plant_id_desc' },
    { icon: '🔬', titleKey: 'features.disease_title',  descKey: 'features.disease_desc'  },
    { icon: '🌾', titleKey: 'features.crop_title',     descKey: 'features.crop_desc'     },
    { icon: '💧', titleKey: 'features.irrigation_title', descKey: 'features.irrigation_desc' },
    { icon: '🌤️', titleKey: 'features.weather_title',  descKey: 'features.weather_desc'  },
    { icon: '🤖', titleKey: 'features.chatbot_title',  descKey: 'features.chatbot_desc'  },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* ── Navigation ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-950/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

          <div className="flex items-center gap-3">
            <span className="text-2xl">🌱</span>
            <span className="text-xl font-bold text-primary-400">CropGuard AI</span>
          </div>

          <div className="flex items-center gap-4">

            {/* Language Switcher */}
            <div className="flex items-center gap-1 bg-white/10 rounded-lg p-1">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => changeLanguage(lang.code)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-all duration-200 ${
                    i18n.language === lang.code
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {lang.label}
                </button>
              ))}
            </div>

            <a href="/login" className="text-gray-300 hover:text-white transition-colors text-sm font-medium">
              {t('nav.login')}
            </a>
            <a href="/register" className="btn-primary text-sm py-2 px-5">
              {t('nav.register')}
            </a>
          </div>
        </div>
      </nav>

      {/* ── Hero Section ── */}
      <section className="relative pt-36 pb-24 px-6 overflow-hidden">

        {/* Decorative background blobs */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-primary-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-48 left-10 w-64 h-64 bg-earth-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-20 right-10 w-48 h-48 bg-primary-800/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-4xl mx-auto text-center">

          <div className="inline-flex items-center gap-2 bg-primary-600/20 border border-primary-500/30 rounded-full px-4 py-2 text-primary-400 text-sm font-medium mb-8">
            <span>🚀</span>
            <span>{t('landing.badge')}</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
            {t('landing.headline_1')}{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-earth-400">
              {t('landing.headline_2')}
            </span>
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            {t('landing.subheadline')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="/register" className="btn-primary text-base">
              {t('landing.cta_primary')}
            </a>
            <button
              onClick={checkApiHealth}
              disabled={loading}
              className="btn-secondary text-base"
            >
              {loading ? t('landing.checking') : `⚡ ${t('landing.cta_api')}`}
            </button>
          </div>

          {/* API Status Result */}
          {apiStatus && (
            <div className={`mt-6 inline-flex flex-col items-center gap-2 px-6 py-4 rounded-xl border ${
              apiStatus.ok
                ? 'bg-primary-600/20 border-primary-500/40 text-primary-300'
                : 'bg-red-600/20 border-red-500/40 text-red-300'
            }`}>
              <div className="flex items-center gap-2 text-sm font-medium">
                <span>{apiStatus.ok ? '✅' : '❌'}</span>
                <span>{apiStatus.message}</span>
              </div>
              {apiStatus.ok && (
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span>🗄️ {apiStatus.database}</span>
                  <span>🕐 {new Date(apiStatus.time).toLocaleTimeString()}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* ── Features Grid ── */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">

          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              {t('landing.features_title')}
            </h2>
            <p className="text-gray-400 text-lg max-w-xl mx-auto">
              {t('landing.features_subtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="glass-card p-6 hover:bg-white/15 transition-all duration-300 group cursor-default"
              >
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300 select-none">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold mb-2 text-white">
                  {t(feature.titleKey)}
                </h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  {t(feature.descKey)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stats Section ── */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card p-10">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center divide-y md:divide-y-0 md:divide-x divide-white/10">
              <div className="pb-6 md:pb-0">
                <div className="text-4xl font-bold text-primary-400 mb-2">10K+</div>
                <div className="text-gray-400 text-sm">{t('landing.stats_scans')}</div>
              </div>
              <div className="py-6 md:py-0 md:px-8">
                <div className="text-4xl font-bold text-earth-400 mb-2">38+</div>
                <div className="text-gray-400 text-sm">{t('landing.stats_diseases')}</div>
              </div>
              <div className="pt-6 md:pt-0">
                <div className="text-4xl font-bold text-primary-400 mb-2">3</div>
                <div className="text-gray-400 text-sm">{t('landing.stats_languages')}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/10 py-8 px-6 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span>🌱</span>
            <span className="text-primary-400 font-semibold">CropGuard AI</span>
          </div>
          <p className="text-gray-500 text-sm">
            {t('landing.footer_tagline')} · English · हिंदी · मराठी
          </p>
        </div>
      </footer>

    </div>
  );
}