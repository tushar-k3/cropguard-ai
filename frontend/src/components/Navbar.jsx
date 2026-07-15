import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'mr', label: 'मराठी' },
];

export default function Navbar() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinks = [
    { path: '/dashboard', label: t('nav.dashboard') },
    { path: '/scanner', label: t('nav.scanner') },
    { path: '/crop', label: t('nav.crop') },
    { path: '/weather', label: t('nav.weather') },
    { path: '/chatbot', label: t('nav.chatbot') },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-950/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

        {/* Logo */}
        <Link to={user ? '/dashboard' : '/'} className="flex items-center gap-3">
          <span className="text-2xl">🌱</span>
          <span className="text-xl font-bold text-primary-400">CropGuard AI</span>
        </Link>

        {/* Desktop nav links — only shown when logged in */}
        {user && (
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  location.pathname === link.path
                    ? 'bg-primary-600/20 text-primary-400'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}

        {/* Right side */}
        <div className="flex items-center gap-3">

          {/* Language switcher */}
          <div className="flex items-center gap-1 bg-white/10 rounded-lg p-1">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => i18n.changeLanguage(lang.code)}
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

          {user ? (
            <div className="flex items-center gap-3">
              {/* User greeting */}
              <span className="hidden md:block text-sm text-gray-400">
                👤 {user.first_name || user.username}
              </span>
              <button
                onClick={handleLogout}
                className="btn-secondary text-sm py-2 px-4"
              >
                {t('nav.logout')}
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link to="/login" className="text-gray-300 hover:text-white text-sm font-medium transition-colors">
                {t('nav.login')}
              </Link>
              <Link to="/register" className="btn-primary text-sm py-2 px-5">
                {t('nav.register')}
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}