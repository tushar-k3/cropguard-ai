import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

const COMMON_CROPS = [
  'rice', 'wheat', 'maize', 'cotton', 'sugarcane', 'potato',
  'tomato', 'onion', 'banana', 'soybean', 'groundnut', 'mustard',
  'chilli', 'cabbage', 'cauliflower', 'grapes', 'mango', 'tea', 'coffee',
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
        step={step || '1'}
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

      {/* Unknown crop warning */}
      {result.unknown_crop && (
        <div className="warning-banner flex gap-3">
          <span className="flex-shrink-0">⚠️</span>
          <span>{t('fertilizer.unknown_crop_warning')}</span>
        </div>
      )}

      {/* Main result */}
      <div className="glass-card p-8 text-center">
        <div className="text-6xl mb-4">{result.icon}</div>
        <p className="text-gray-400 text-sm mb-2">
          {t('fertilizer.recommended_fertilizer')}
        </p>
        <h2 className="text-3xl font-bold text-white mb-2">
          {result.fertilizer}
        </h2>
        <div className="inline-flex items-center gap-2 bg-primary-600/20 border border-primary-500/40 text-primary-300 px-4 py-2 rounded-full text-sm font-medium mb-4">
          ✅ {result.confidence}% {t('fertilizer.confidence')}
        </div>
        <p className="text-earth-400 text-sm font-medium">
          {result.nutrient}
        </p>
      </div>

      {/* Details */}
      <div className="glass-card p-6 space-y-4">
        <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wide">
          📋 {t('fertilizer.application_guide')}
        </h3>

        <div className="grid grid-cols-1 gap-4">
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-1">
              {t('fertilizer.best_for')}
            </p>
            <p className="text-white text-sm">{result.best_for}</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-1">
              {t('fertilizer.how_to_apply')}
            </p>
            <p className="text-white text-sm">{result.application}</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-1">
              {t('fertilizer.dosage')}
            </p>
            <p className="text-white text-sm">{result.dosage}</p>
          </div>
          <div className="bg-amber-600/10 border border-amber-500/30 rounded-xl p-4">
            <p className="text-amber-400 text-xs mb-1 font-medium">
              ⚠️ {t('fertilizer.caution')}
            </p>
            <p className="text-amber-300/80 text-sm">{result.caution}</p>
          </div>
        </div>
      </div>

      {/* Top 3 alternatives */}
      {result.top_3 && result.top_3.length > 1 && (
        <div className="glass-card p-6">
          <p className="text-gray-400 text-sm font-medium mb-3">
            {t('fertilizer.alternatives')}
          </p>
          <div className="space-y-2">
            {result.top_3.map((item, index) => (
              <div
                key={index}
                className={`flex items-center justify-between px-4 py-3 rounded-xl ${
                  index === 0
                    ? 'bg-primary-600/20 border border-primary-500/30'
                    : 'bg-white/5'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{item.icon}</span>
                  <span
                    className={`text-sm font-medium ${
                      index === 0 ? 'text-primary-300' : 'text-gray-300'
                    }`}
                  >
                    {index === 0 && '⭐ '}
                    {item.fertilizer}
                  </span>
                </div>
                <span
                  className={`text-sm font-semibold ${
                    index === 0 ? 'text-primary-400' : 'text-gray-400'
                  }`}
                >
                  {item.confidence}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function FertilizerPage() {
  const { t } = useTranslation();

  const [form, setForm] = useState({ crop: '', N: '', P: '', K: '' });
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
        N: parseFloat(form.N),
        P: parseFloat(form.P),
        K: parseFloat(form.K),
      };
      const response = await api.post('/fertilizer/recommend/', payload);
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
    setForm({ crop: '', N: '', P: '', K: '' });
    setResult(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-5xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="text-5xl mb-4">🧪</div>
          <h1 className="text-3xl font-bold mb-2">{t('fertilizer.title')}</h1>
          <p className="text-gray-400">{t('fertilizer.subtitle')}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Form */}
          <form onSubmit={handleSubmit} className="glass-card p-6 space-y-5">

            {/* Crop name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('fertilizer.crop_name')}
              </label>
              <input
                type="text"
                name="crop"
                value={form.crop}
                onChange={handleChange}
                className="input-field"
                placeholder={t('fertilizer.crop_placeholder')}
                required
                list="crop-suggestions"
              />
              <datalist id="crop-suggestions">
                {COMMON_CROPS.map((crop) => (
                  <option key={crop} value={crop} />
                ))}
              </datalist>
              <p className="text-gray-500 text-xs mt-1">
                {t('fertilizer.crop_hint')}
              </p>
            </div>

            {/* NPK */}
            <div>
              <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wide mb-4">
                🧪 {t('fertilizer.section_soil')}
              </h3>
              <p className="text-gray-500 text-xs mb-4">
                {t('fertilizer.soil_hint')}
              </p>
              <div className="grid grid-cols-3 gap-4">
                <InputField
                  label="Nitrogen (N)"
                  name="N"
                  value={form.N}
                  onChange={handleChange}
                  min="0" max="300"
                  unit="kg/ha"
                  hint="e.g. 80"
                />
                <InputField
                  label="Phosphorus (P)"
                  name="P"
                  value={form.P}
                  onChange={handleChange}
                  min="0" max="300"
                  unit="kg/ha"
                  hint="e.g. 40"
                />
                <InputField
                  label="Potassium (K)"
                  name="K"
                  value={form.K}
                  onChange={handleChange}
                  min="0" max="300"
                  unit="kg/ha"
                  hint="e.g. 40"
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
                    {t('fertilizer.analyzing')}
                  </>
                ) : (
                  `🧪 ${t('fertilizer.btn_recommend')}`
                )}
              </button>
              {result && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="btn-secondary px-5"
                  title="Reset"
                >
                  ↺
                </button>
              )}
            </div>
          </form>

          {/* Result or empty state */}
          <div>
            {result ? (
              <ResultCard result={result} />
            ) : (
              <div className="glass-card p-10 text-center h-full flex flex-col items-center justify-center min-h-64">
                <div className="text-6xl mb-4">🌿</div>
                <p className="text-gray-400 text-sm max-w-xs leading-relaxed">
                  {t('fertilizer.empty_state')}
                </p>
                <div className="mt-8 space-y-3 text-left w-full max-w-xs">
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('fertilizer.tip_1')}</span>
                  </div>
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('fertilizer.tip_2')}</span>
                  </div>
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('fertilizer.tip_3')}</span>
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