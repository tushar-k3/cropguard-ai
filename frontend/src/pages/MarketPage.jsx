import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

const INDIAN_STATES = [
  'Maharashtra', 'Punjab', 'Haryana', 'Uttar Pradesh', 'Madhya Pradesh',
  'Gujarat', 'Rajasthan', 'Karnataka', 'Andhra Pradesh', 'Telangana',
  'Tamil Nadu', 'West Bengal', 'Bihar', 'Odisha', 'Assam',
];

function PriceCard({ record }) {
  const date = record.arrival_date || record.price_date || '';
  return (
    <div className="glass-card p-5 hover:bg-white/15 transition-all duration-200">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-white font-semibold text-base">{record.commodity}</h3>
          {record.variety && (
            <p className="text-gray-500 text-xs mt-0.5">{record.variety}</p>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-primary-400">
            ₹{record.modal_price}
          </div>
          <div className="text-gray-500 text-xs">per quintal</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="bg-white/5 rounded-lg p-2 text-center">
          <p className="text-gray-500 text-xs">Min</p>
          <p className="text-green-400 text-sm font-semibold">₹{record.min_price}</p>
        </div>
        <div className="bg-primary-600/10 rounded-lg p-2 text-center border border-primary-500/20">
          <p className="text-gray-400 text-xs">Modal</p>
          <p className="text-primary-300 text-sm font-semibold">₹{record.modal_price}</p>
        </div>
        <div className="bg-white/5 rounded-lg p-2 text-center">
          <p className="text-gray-500 text-xs">Max</p>
          <p className="text-red-400 text-sm font-semibold">₹{record.max_price}</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>📍 {record.market}{record.district ? `, ${record.district}` : ''}</span>
        <span>📅 {date}</span>
      </div>
    </div>
  );
}

export default function MarketPage() {
  const { t } = useTranslation();

  const [records, setRecords] = useState([]);
  const [commodities, setCommodities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [source, setSource] = useState('');
  const [fetchedAt, setFetchedAt] = useState(null);
  const [apiUnavailable, setApiUnavailable] = useState(false);

  const [filters, setFilters] = useState({
    commodity: '',
    state: 'Maharashtra',
  });

  // Load commodities for dropdown
  useEffect(() => {
    const loadCommodities = async () => {
      try {
        const response = await api.get('/market/commodities/');
        setCommodities(response.data.commodities || []);
      } catch {
        // Non-critical
      }
    };
    loadCommodities();
  }, []);

  // Load prices on mount and filter change
  useEffect(() => {
    fetchPrices();
  }, []);

  const fetchPrices = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ limit: 60 });
      if (filters.commodity) params.append('commodity', filters.commodity);
      if (filters.state) params.append('state', filters.state);

      const response = await api.get(`/market/?${params}`);
      const data = response.data;

      setRecords(data.records || []);
      setSource(data.source_label || '');
      setFetchedAt(data.fetched_at);
      setApiUnavailable(data.api_unavailable || false);

      if (data.records?.length === 0) {
        setError(t('market.no_results'));
      }
    } catch (err) {
      setError(err.response?.data?.error || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchPrices();
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-6xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">📈</div>
          <h1 className="text-3xl font-bold mb-2">{t('market.title')}</h1>
          <p className="text-gray-400">{t('market.subtitle')}</p>
        </div>

        {/* Data source badge */}
        {source && (
          <div className={`flex items-center justify-between px-4 py-3 rounded-xl border text-sm mb-6 ${
            apiUnavailable
              ? 'bg-amber-600/20 border-amber-500/40 text-amber-300'
              : 'bg-primary-600/20 border-primary-500/40 text-primary-300'
          }`}>
            <span>
              {apiUnavailable ? '⚠️' : '✅'} {source}
            </span>
            {fetchedAt && (
              <span className="text-gray-400 text-xs">
                {t('common.last_updated')}: {new Date(fetchedAt).toLocaleString('en-IN')}
              </span>
            )}
          </div>
        )}

        {/* Filters */}
        <form onSubmit={handleSearch} className="glass-card p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('market.commodity_label')}
              </label>
              <input
                type="text"
                name="commodity"
                value={filters.commodity}
                onChange={handleFilterChange}
                className="input-field"
                placeholder={t('market.commodity_placeholder')}
                list="commodity-list"
              />
              <datalist id="commodity-list">
                {commodities.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {t('market.state_label')}
              </label>
              <select
                name="state"
                value={filters.state}
                onChange={handleFilterChange}
                className="input-field"
                style={{ colorScheme: 'dark' }}
              >
                <option value="" style={{ backgroundColor: '#111827', color: '#f3f4f6' }}>
                  All States
                </option>
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s} style={{ backgroundColor: '#111827', color: '#f3f4f6' }}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : '🔍'}
                {t('market.search_btn')}
              </button>
            </div>
          </div>
        </form>

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
            <p className="text-gray-400">{t('market.loading')}</p>
          </div>
        )}

        {/* Results */}
        {!loading && records.length > 0 && (
          <>
            <p className="text-gray-400 text-sm mb-4">
              {t('market.showing')} {records.length} {t('market.results')}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {records.map((record, i) => (
                <PriceCard key={i} record={record} />
              ))}
            </div>
          </>
        )}

        {/* Empty state */}
        {!loading && records.length === 0 && !error && (
          <div className="glass-card p-12 text-center">
            <div className="text-5xl mb-4">📊</div>
            <p className="text-gray-400 text-sm">{t('market.empty_state')}</p>
          </div>
        )}

      </main>
    </div>
  );
}