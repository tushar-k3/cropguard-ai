import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

const SOIL_TYPES = [
  { value: 'sandy',    label: 'Sandy Soil' },
  { value: 'loamy',    label: 'Loamy Soil' },
  { value: 'clay',     label: 'Clay Soil' },
  { value: 'silt',     label: 'Silt Soil' },
  { value: 'black',    label: 'Black Soil' },
  { value: 'red',      label: 'Red Soil' },
  { value: 'alluvial', label: 'Alluvial Soil' },
];

const COMMON_CROPS = [
  'rice', 'wheat', 'maize', 'cotton', 'sugarcane', 'potato',
  'tomato', 'onion', 'banana', 'soybean', 'groundnut', 'mustard',
  'chilli', 'chickpea', 'lentil', 'millet', 'sorghum', 'barley',
  'sunflower', 'vegetables', 'tea', 'coffee',
];

function InputField({ label, name, value, onChange, min, max, step, unit, hint }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">
        {label}
        {unit && (
          <span className="text-gray-500 ml-1 font-normal">({unit})</span>
        )}
      </label>
      <input
        type="number"
        name={name}
        value={value}
        onChange={onChange}
        min={min}
        max={max}
        step={step || '0.1'}
        className="input-field"
        placeholder={hint}
        required
      />
      {hint && <p className="text-gray-500 text-xs mt-1">{hint}</p>}
    </div>
  );
}

function ResultCard({ result }) {
  const { t } = useTranslation();

  return (
    <div className="space-y-4">

      {/* Warnings */}
      {(result.unknown_crop || result.unknown_soil) && (
        <div className="warning-banner flex gap-3">
          <span className="flex-shrink-0">⚠️</span>
          <span>{t('irrigation.unknown_warning')}</span>
        </div>
      )}

      {/* Main result */}
      <div className="glass-card p-8 text-center">
        <div className="text-6xl mb-4">{result.icon}</div>
        <p className="text-gray-400 text-sm mb-2">
          {t('irrigation.water_requirement')}
        </p>
        <h2 className="text-2xl font-bold text-white mb-3 leading-tight">
          {result.label}
        </h2>
        <div className="inline-flex items-center gap-2 bg-primary-600/20 border border-primary-500/40 text-primary-300 px-4 py-2 rounded-full text-sm font-medium">
          ✅ {result.confidence}% {t('irrigation.confidence')}
        </div>
      </div>

      {/* Schedule details */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wide mb-4">
          📅 {t('irrigation.schedule')}
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-1">
              {t('irrigation.per_day')}
            </p>
            <p className="text-white font-semibold text-lg">
              {result.water_per_day}
            </p>
          </div>
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-1">
              {t('irrigation.frequency')}
            </p>
            <p className="text-white font-semibold">{result.frequency}</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-1">
              {t('irrigation.per_week')}
            </p>
            <p className="text-white font-semibold">{result.total_per_week}</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-1">
              {t('irrigation.best_time')}
            </p>
            <p className="text-white font-semibold text-sm">{result.best_time}</p>
          </div>
        </div>
        <div className="mt-3 bg-white/5 rounded-xl p-4">
          <p className="text-gray-500 text-xs mb-1">
            {t('irrigation.method')}
          </p>
          <p className="text-white font-semibold">{result.method}</p>
        </div>
      </div>

      {/* Tips */}
      {result.tips && result.tips.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-earth-400 uppercase tracking-wide mb-4">
            💡 {t('irrigation.tips')}
          </h3>
          <div className="space-y-3">
            {result.tips.map((tip, i) => (
              <div key={i} className="flex gap-3 text-sm text-gray-300">
                <span className="text-primary-500 flex-shrink-0 mt-0.5">✓</span>
                <span>{tip}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function IrrigationPage() {
  const { t } = useTranslation();

  const [form, setForm] = useState({
    crop: '',
    soil_type: 'loamy',
    temperature: '',
    humidity: '',
    rainfall: '',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const payload = {
        crop: form.crop.toLowerCase().trim(),
        soil_type: form.soil_type,
        temperature: parseFloat(form.temperature),
        humidity: parseFloat(form.humidity),
        rainfall: parseFloat(form.rainfall),
      };
      const response = await api.post('/irrigation/recommend/', payload);
      setResult(response.data);
    } catch (err) {
      if (err.response?.data) {
        const errors = err.response.data;
        const firstError = Object.values(errors)[0];
        setError(Array.isArray(firstError) ? firstError[0] : firstError);
      } else {
        setError(t('common.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm({
      crop: '',
      soil_type: 'loamy',
      temperature: '',
      humidity: '',
      rainfall: '',
    });
    setResult(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-5xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="text-5xl mb-4">💧</div>
          <h1 className="text-3xl font-bold mb-2">{t('irrigation.title')}</h1>
          <p className="text-gray-400">{t('irrigation.subtitle')}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Form */}
          <form onSubmit={handleSubmit} className="glass-card p-6 space-y-5">

            {/* Crop */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('irrigation.crop_name')}
              </label>
              <input
                type="text"
                name="crop"
                value={form.crop}
                onChange={handleChange}
                className="input-field"
                placeholder={t('irrigation.crop_placeholder')}
                required
                list="irrigation-crop-suggestions"
              />
              <datalist id="irrigation-crop-suggestions">
                {COMMON_CROPS.map((crop) => (
                  <option key={crop} value={crop} />
                ))}
              </datalist>
            </div>

            {/* Soil type */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('irrigation.soil_type')}
              </label>
              <select
                name="soil_type"
                value={form.soil_type}
                onChange={handleChange}
                className="input-field"
                style={{ colorScheme: 'dark' }}
              >
                {SOIL_TYPES.map((soil) => (
                  <option
                    key={soil.value}
                    value={soil.value}
                    style={{ backgroundColor: '#111827', color: '#f3f4f6' }}
                  >
                    {soil.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Weather */}
            <div>
              <h3 className="text-sm font-semibold text-earth-400 uppercase tracking-wide mb-4">
                🌤️ {t('irrigation.section_weather')}
              </h3>
              <div className="space-y-4">
                <InputField
                  label={t('irrigation.temperature')}
                  name="temperature"
                  value={form.temperature}
                  onChange={handleChange}
                  min="0" max="50"
                  unit="°C"
                  hint="e.g. 30"
                />
                <InputField
                  label={t('irrigation.humidity')}
                  name="humidity"
                  value={form.humidity}
                  onChange={handleChange}
                  min="0" max="100"
                  unit="%"
                  hint="e.g. 60"
                />
                <InputField
                  label={t('irrigation.rainfall')}
                  name="rainfall"
                  value={form.rainfall}
                  onChange={handleChange}
                  min="0" max="500"
                  step="1"
                  unit="mm"
                  hint="e.g. 50 (recent or expected)"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {t('irrigation.analyzing')}
                  </>
                ) : (
                  `💧 ${t('irrigation.btn_recommend')}`
                )}
              </button>
              {result && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="btn-secondary px-5"
                >
                  ↺
                </button>
              )}
            </div>
          </form>

          {/* Result */}
          <div>
            {result ? (
              <ResultCard result={result} />
            ) : (
              <div className="glass-card p-10 text-center h-full flex flex-col items-center justify-center min-h-64">
                <div className="text-6xl mb-4">🌱</div>
                <p className="text-gray-400 text-sm max-w-xs leading-relaxed">
                  {t('irrigation.empty_state')}
                </p>
                <div className="mt-8 space-y-3 text-left w-full max-w-xs">
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('irrigation.tip_1')}</span>
                  </div>
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('irrigation.tip_2')}</span>
                  </div>
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('irrigation.tip_3')}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}