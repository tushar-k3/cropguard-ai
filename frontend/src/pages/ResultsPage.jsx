import React from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';

function SourceBadge({ source }) {
  const { t } = useTranslation();
  if (source === 'kindwise') {
    return (
      <span className="badge-kindwise">
        🌐 {t('source_badge.kindwise')}
      </span>
    );
  }
  return (
    <span className="badge-local-model">
      💻 {t('source_badge.local_model')}
    </span>
  );
}

function ConfidenceBar({ value }) {
  const color = value >= 70 ? 'bg-primary-500' : value >= 40 ? 'bg-earth-500' : 'bg-red-500';
  return (
    <div className="w-full bg-white/10 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all duration-700 ${color}`}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

function DiseaseCard({ disease }) {
  const { t } = useTranslation();

  const hasBiological = disease.treatment?.biological?.length > 0;
  const hasChemical = disease.treatment?.chemical?.length > 0;
  const hasPrevention = disease.treatment?.prevention?.length > 0;

  return (
    <div className="glass-card p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{disease.name}</h3>
          {disease.common_names?.length > 0 && (
            <p className="text-gray-400 text-sm mt-1">
              {t('results.also_known_as')}: {disease.common_names.join(', ')}
            </p>
          )}
        </div>
        <div className="text-right ml-4 flex-shrink-0">
          <div className="text-2xl font-bold text-earth-400">
            {disease.probability}%
          </div>
          <div className="text-gray-500 text-xs">{t('results.confidence')}</div>
        </div>
      </div>

      <ConfidenceBar value={disease.probability} />

      {disease.description && (
        <p className="text-gray-400 text-sm mt-4 leading-relaxed">
          {disease.description}
        </p>
      )}

      {/* Treatment sections */}
      {hasBiological && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-primary-400 mb-2">
            🌿 {t('results.biological_treatment')}
          </h4>
          <ul className="space-y-1">
            {disease.treatment.biological.map((item, i) => (
              <li key={i} className="text-gray-400 text-sm flex gap-2">
                <span className="text-primary-500 flex-shrink-0">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasChemical && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-earth-400 mb-2">
            🧪 {t('results.chemical_treatment')}
          </h4>
          <ul className="space-y-1">
            {disease.treatment.chemical.map((item, i) => (
              <li key={i} className="text-gray-400 text-sm flex gap-2">
                <span className="text-earth-500 flex-shrink-0">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasPrevention && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-blue-400 mb-2">
            🛡️ {t('results.prevention')}
          </h4>
          <ul className="space-y-1">
            {disease.treatment.prevention.map((item, i) => (
              <li key={i} className="text-gray-400 text-sm flex gap-2">
                <span className="text-blue-500 flex-shrink-0">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function ResultsPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const result = location.state?.result;

  // If user lands here directly without scan data, redirect to scanner
  if (!result) {
    return (
      <div className="min-h-screen bg-gray-950 text-white">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-screen gap-4">
          <div className="text-5xl">🔬</div>
          <p className="text-gray-400">{t('results.no_result')}</p>
          <Link to="/scanner" className="btn-primary">
            {t('results.go_to_scanner')}
          </Link>
        </div>
      </div>
    );
  }

  const isHealthy = result.is_healthy;
  const diseases = result.diseases || [];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-3xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate('/scanner')}
            className="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2"
          >
            ← {t('results.back')}
          </button>
        </div>

        {/* Plant Identity Card */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-gray-400 text-sm mb-1">{t('results.identified_plant')}</p>
              <h1 className="text-2xl font-bold text-white">
                {result.plant_name || t('results.unknown_plant')}
              </h1>
            </div>
            <SourceBadge source={result.source} />
          </div>

          {/* Confidence */}
          {result.plant_probability > 0 && (
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">{t('results.identification_confidence')}</span>
                <span className="text-white font-medium">{result.plant_probability}%</span>
              </div>
              <ConfidenceBar value={result.plant_probability} />
            </div>
          )}

          {/* Health Status */}
          <div className={`mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium ${
            isHealthy
              ? 'bg-primary-600/20 border border-primary-500/40 text-primary-300'
              : 'bg-red-600/20 border border-red-500/40 text-red-300'
          }`}>
            <span>{isHealthy ? '✅' : '⚠️'}</span>
            <span>{isHealthy ? t('results.healthy') : t('results.disease_detected')}</span>
          </div>
        </div>

        {/* Local model warning */}
        {result.source === 'local_model' && (
          <div className="warning-banner mb-6 flex gap-3">
            <span className="flex-shrink-0">⚠️</span>
            <span>{t('source_badge.local_model_warning')}</span>
          </div>
        )}

        {/* Unsupported crop warning */}
        {result.unsupported_crop && (
          <div className="warning-banner mb-6 flex gap-3">
            <span className="flex-shrink-0">🚫</span>
            <span>{t('results.unsupported_crop_warning')}</span>
          </div>
        )}

        {/* Disease Results */}
        {!isHealthy && diseases.length > 0 && (
          <div className="space-y-4 mb-6">
            <h2 className="text-xl font-bold text-white">
              {t('results.diseases_found')} ({diseases.length})
            </h2>
            {diseases.map((disease, index) => (
              <DiseaseCard key={index} disease={disease} />
            ))}
          </div>
        )}

        {/* Healthy result */}
        {isHealthy && (
          <div className="glass-card p-8 text-center mb-6">
            <div className="text-5xl mb-4">🌿</div>
            <h2 className="text-xl font-bold text-primary-400 mb-2">
              {t('results.plant_healthy')}
            </h2>
            <p className="text-gray-400 text-sm">
              {t('results.plant_healthy_desc')}
            </p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Link to="/scanner" className="btn-primary flex-1 text-center text-sm py-3">
            🔬 {t('results.scan_another')}
          </Link>
          <Link to="/dashboard" className="btn-secondary flex-1 text-center text-sm py-3">
            🏠 {t('nav.dashboard')}
          </Link>
        </div>

      </main>
    </div>
  );
}