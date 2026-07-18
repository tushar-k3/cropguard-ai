import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

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
    <div className="glass-card p-8 text-center">
      <div className="text-7xl mb-4">{result.icon}</div>
      <p className="text-gray-400 text-sm mb-2">{t('crop.recommended_crop')}</p>
      <h2 className="text-4xl font-bold text-white mb-2 capitalize">
        {result.crop}
      </h2>

      <div className="inline-flex items-center gap-2 bg-primary-600/20 border border-primary-500/40 text-primary-300 px-4 py-2 rounded-full text-sm font-medium mb-6">
        ✅ {result.confidence}% {t('crop.confidence')}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white/5 rounded-xl p-4">
          <p className="text-gray-500 text-xs mb-1">{t('crop.season')}</p>
          <p className="text-white font-semibold">{result.season}</p>
        </div>
        <div className="bg-white/5 rounded-xl p-4">
          <p className="text-gray-500 text-xs mb-1">{t('crop.duration')}</p>
          <p className="text-white font-semibold">{result.duration}</p>
        </div>
      </div>

      {result.top_3 && result.top_3.length > 1 && (
        <div className="text-left">
          <p className="text-gray-400 text-sm font-medium mb-3">
            {t('crop.alternatives')}
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
                  <span className="text-xl">{item.icon}</span>
                  <span
                    className={`font-medium capitalize ${
                      index === 0 ? 'text-primary-300' : 'text-gray-300'
                    }`}
                  >
                    {index === 0 && '⭐ '}
                    {item.crop}
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

export default function CropPage() {
  const { t } = useTranslation();

  const [form, setForm] = useState({
    N: '',
    P: '',
    K: '',
    temperature: '',
    humidity: '',
    ph: '',
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
        N: parseFloat(form.N),
        P: parseFloat(form.P),
        K: parseFloat(form.K),
        temperature: parseFloat(form.temperature),
        humidity: parseFloat(form.humidity),
        ph: parseFloat(form.ph),
        rainfall: parseFloat(form.rainfall),
      };

      const response = await api.post('/crop/recommend/', payload);
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
      N: '',
      P: '',
      K: '',
      temperature: '',
      humidity: '',
      ph: '',
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
          <div className="text-5xl mb-4">🌾</div>
          <h1 className="text-3xl font-bold mb-2">{t('crop.title')}</h1>
          <p className="text-gray-400">{t('crop.subtitle')}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="glass-card p-6 space-y-5">

            {/* Soil Nutrients */}
            <div>
              <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wide mb-4">
                🧪 {t('crop.section_soil')}
              </h3>
              <p className="text-gray-500 text-xs mb-4">
                {t('crop.soil_hint')}
              </p>
              <div className="grid grid-cols-3 gap-4">
                <InputField
                  label="Nitrogen (N)"
                  name="N"
                  value={form.N}
                  onChange={handleChange}
                  min="0"
                  max="300"
                  step="1"
                  unit="kg/ha"
                  hint="e.g. 80"
                />
                <InputField
                  label="Phosphorus (P)"
                  name="P"
                  value={form.P}
                  onChange={handleChange}
                  min="0"
                  max="300"
                  step="1"
                  unit="kg/ha"
                  hint="e.g. 60"
                />
                <InputField
                  label="Potassium (K)"
                  name="K"
                  value={form.K}
                  onChange={handleChange}
                  min="0"
                  max="300"
                  step="1"
                  unit="kg/ha"
                  hint="e.g. 40"
                />
              </div>
            </div>

            {/* Soil pH */}
            <InputField
              label="Soil pH"
              name="ph"
              value={form.ph}
              onChange={handleChange}
              min="0"
              max="14"
              step="0.1"
              hint="e.g. 6.5 (range: 0–14)"
            />

            {/* Climate */}
            <div>
              <h3 className="text-sm font-semibold text-earth-400 uppercase tracking-wide mb-4">
                🌤️ {t('crop.section_climate')}
              </h3>
              <div className="space-y-4">
                <InputField
                  label={t('crop.temperature')}
                  name="temperature"
                  value={form.temperature}
                  onChange={handleChange}
                  min="0"
                  max="50"
                  step="0.1"
                  unit="°C"
                  hint="e.g. 25"
                />
                <InputField
                  label={t('crop.humidity')}
                  name="humidity"
                  value={form.humidity}
                  onChange={handleChange}
                  min="0"
                  max="100"
                  step="0.1"
                  unit="%"
                  hint="e.g. 80"
                />
                <InputField
                  label={t('crop.rainfall')}
                  name="rainfall"
                  value={form.rainfall}
                  onChange={handleChange}
                  min="0"
                  max="500"
                  step="1"
                  unit="mm"
                  hint="e.g. 200 (annual)"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm">
                {error}
              </div>
            )}

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {t('crop.analyzing')}
                  </>
                ) : (
                  `🌾 ${t('crop.btn_recommend')}`
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

          {/* Result Panel */}
          <div>
            {result ? (
              <ResultCard result={result} />
            ) : (
              <div className="glass-card p-10 text-center h-full flex flex-col items-center justify-center min-h-64">
                <div className="text-6xl mb-4">🌱</div>
                <p className="text-gray-400 text-sm max-w-xs leading-relaxed">
                  {t('crop.empty_state')}
                </p>
                <div className="mt-8 space-y-3 text-left w-full max-w-xs">
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('crop.tip_1')}</span>
                  </div>
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('crop.tip_2')}</span>
                  </div>
                  <div className="flex gap-3 text-sm text-gray-500">
                    <span className="text-primary-500 flex-shrink-0">✓</span>
                    <span>{t('crop.tip_3')}</span>
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