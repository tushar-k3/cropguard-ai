import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

const ADVICE_COLORS = {
  good:    'bg-primary-600/20 border-primary-500/40 text-primary-300',
  caution: 'bg-earth-600/20 border-earth-500/40 text-earth-300',
  warning: 'bg-red-600/20 border-red-500/40 text-red-300',
};

const QUICK_CITIES = [
  'Nashik', 'Pune', 'Mumbai', 'Nagpur', 'Aurangabad',
  'Malegaon', 'Solapur', 'Kolhapur', 'Amravati', 'Delhi',
];

function WeatherStatCard({ icon, label, value, unit }) {
  return (
    <div className="bg-white/5 rounded-xl p-4 text-center">
      <div className="text-2xl mb-1">{icon}</div>
      <p className="text-gray-500 text-xs mb-1">{label}</p>
      <p className="text-white font-bold text-lg">
        {value !== null && value !== undefined ? `${value}${unit || ''}` : '—'}
      </p>
    </div>
  );
}

function ForecastCard({ day }) {
  const date = new Date(day.date);
  const dayName = date.toLocaleDateString('en-IN', { weekday: 'short' });
  const dateStr = date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

  return (
    <div className="bg-white/5 rounded-xl p-4 text-center flex-1 min-w-0">
      <p className="text-gray-400 text-xs font-medium">{dayName}</p>
      <p className="text-gray-500 text-xs">{dateStr}</p>
      <div className="text-2xl my-2">{day.icon}</div>
      <p className="text-white text-sm font-bold">{Math.round(day.temp_max)}°</p>
      <p className="text-gray-500 text-xs">{Math.round(day.temp_min)}°</p>
      {day.precipitation > 0 && (
        <p className="text-blue-400 text-xs mt-1">
          💧 {day.precipitation}mm
        </p>
      )}
    </div>
  );
}

export default function WeatherPage() {
  const { t } = useTranslation();

  const [searchCity, setSearchCity] = useState('');
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [error, setError] = useState('');

  // Auto-load last searched city on first visit
  useEffect(() => {
    const savedCity = localStorage.getItem('weather_city');
    if (savedCity) {
      fetchWeatherByCity(savedCity);
    }
  }, []);

  const fetchWeatherByCity = async (cityName) => {
    if (!cityName.trim()) return;
    setLoading(true);
    setError('');
    setWeather(null);
    try {
      const response = await api.get(
        `/weather/?city=${encodeURIComponent(cityName.trim())}`
      );
      setWeather(response.data);
      localStorage.setItem('weather_city', cityName.trim());
    } catch (err) {
      setError(err.response?.data?.error || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const fetchWeatherByLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }

    setLocationLoading(true);
    setError('');
    setWeather(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const response = await api.get(
            `/weather/?lat=${latitude}&lon=${longitude}`
          );
          setWeather(response.data);
          localStorage.removeItem('weather_city');
        } catch (err) {
          setError(err.response?.data?.error || t('common.error'));
        } finally {
          setLocationLoading(false);
        }
      },
      (geoError) => {
        setLocationLoading(false);
        if (geoError.code === 1) {
          setError(
            'Location access denied. Please allow location permission or search by city name.'
          );
        } else {
          setError('Could not get your location. Please search by city name.');
        }
      },
      { timeout: 10000 }
    );
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchCity.trim()) {
      fetchWeatherByCity(searchCity.trim());
    }
  };

  const current = weather?.current;
  const isLoading = loading || locationLoading;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-4xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🌤️</div>
          <h1 className="text-3xl font-bold mb-2">{t('weather.title')}</h1>
          <p className="text-gray-400">{t('weather.subtitle')}</p>
        </div>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex gap-3 mb-3">
          <input
            type="text"
            value={searchCity}
            onChange={(e) => setSearchCity(e.target.value)}
            className="input-field flex-1"
            placeholder={t('weather.search_placeholder')}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary px-5 flex items-center gap-2 flex-shrink-0"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : '🔍'}
            {t('weather.search_btn')}
          </button>
        </form>

        {/* Current location button */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={fetchWeatherByLocation}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-blue-300 rounded-xl text-sm font-medium transition-all duration-200 disabled:opacity-50"
          >
            {locationLoading ? (
              <div className="w-4 h-4 border-2 border-blue-300/30 border-t-blue-300 rounded-full animate-spin" />
            ) : '📍'}
            {t('weather.use_location')}
          </button>
          <p className="text-gray-600 text-xs">
            {t('weather.location_hint')}
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="glass-card p-12 text-center">
            <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">
              {locationLoading ? t('weather.getting_location') : t('weather.loading')}
            </p>
          </div>
        )}

        {/* Weather data */}
        {weather && !isLoading && (
          <div className="space-y-6">

            {/* Current conditions */}
            <div className="glass-card p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    📍 {weather.city}
                  </h2>
                  <p className="text-gray-400 text-sm mt-1">
                    {t('weather.current_conditions')}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-6xl">{current?.icon}</div>
                  <p className="text-gray-400 text-sm mt-1">
                    {current?.description}
                  </p>
                </div>
              </div>

              <div className="text-center mb-6">
                <div className="text-7xl font-bold text-white">
                  {Math.round(current?.temperature)}°C
                </div>
                <p className="text-gray-400 text-sm mt-1">
                  {t('weather.feels_like')} {Math.round(current?.feels_like)}°C
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <WeatherStatCard
                  icon="💧"
                  label={t('weather.humidity')}
                  value={current?.humidity}
                  unit="%"
                />
                <WeatherStatCard
                  icon="🌧️"
                  label={t('weather.rainfall')}
                  value={current?.rain}
                  unit=" mm"
                />
                <WeatherStatCard
                  icon="💨"
                  label={t('weather.wind')}
                  value={Math.round(current?.wind_speed)}
                  unit=" km/h"
                />
                <WeatherStatCard
                  icon="☁️"
                  label={t('weather.cloud_cover')}
                  value={current?.cloud_cover}
                  unit="%"
                />
              </div>
            </div>

            {/* 7-day forecast */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wide mb-4">
                📅 {t('weather.forecast_7day')}
              </h3>
              <div className="flex gap-2 overflow-x-auto pb-2">
                {weather.forecast?.map((day, i) => (
                  <ForecastCard key={i} day={day} />
                ))}
              </div>
            </div>

            {/* Farming advice */}
            {weather.farming_advice?.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-earth-400 uppercase tracking-wide mb-4">
                  🌾 {t('weather.farming_advice')}
                </h3>
                <div className="space-y-3">
                  {weather.farming_advice.map((advice, i) => (
                    <div
                      key={i}
                      className={`flex gap-3 px-4 py-3 rounded-xl border text-sm ${
                        ADVICE_COLORS[advice.type] || ADVICE_COLORS.caution
                      }`}
                    >
                      <span className="flex-shrink-0 text-lg">{advice.icon}</span>
                      <span>{advice.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}

        {/* Empty state */}
        {!weather && !isLoading && !error && (
          <div className="glass-card p-10 text-center">
            <div className="text-6xl mb-4">🌍</div>
            <p className="text-gray-400 text-sm max-w-xs mx-auto mb-6">
              {t('weather.empty_state')}
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {QUICK_CITIES.map((c) => (
                <button
                  key={c}
                  onClick={() => { setSearchCity(c); fetchWeatherByCity(c); }}
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-sm text-gray-300 hover:text-white transition-all"
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}