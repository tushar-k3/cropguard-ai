import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

function ScanReportCard({ scan, onDownload, downloading }) {
  const { t } = useTranslation();
  return (
    <div className="glass-card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-white font-semibold">
            {scan.plant_name || t('results.unknown_plant')}
          </h3>
          <p className="text-gray-500 text-xs mt-1">
            Scan #{scan.id} · {new Date(scan.created_at).toLocaleDateString('en-IN')}
          </p>
        </div>
        <div className={`px-2 py-1 rounded-lg text-xs font-medium ${
          scan.is_healthy
            ? 'bg-primary-600/20 text-primary-300'
            : 'bg-red-600/20 text-red-300'
        }`}>
          {scan.is_healthy ? '✅ Healthy' : '⚠️ Diseased'}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>
            {scan.source === 'kindwise' ? '🌐 Kindwise AI' : '💻 Offline Model'}
          </span>
          <span>·</span>
          <span>{scan.confidence?.toFixed(1)}% confidence</span>
        </div>
        <button
          onClick={() => onDownload(scan.id)}
          disabled={downloading === scan.id}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600/20 hover:bg-primary-600/40 border border-primary-500/40 text-primary-300 rounded-xl text-xs font-medium transition-all duration-200 disabled:opacity-50"
        >
          {downloading === scan.id ? (
            <div className="w-3 h-3 border-2 border-primary-300/30 border-t-primary-300 rounded-full animate-spin" />
          ) : '📄'}
          {t('reports.download_pdf')}
        </button>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const { t } = useTranslation();

  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);
  const [summaryDownloading, setSummaryDownloading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    const fetchScans = async () => {
      try {
        const response = await api.get('/scan/history/');
        setScans(response.data.results || []);
      } catch {
        setError(t('common.error'));
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
  }, []);

  const downloadScanReport = async (scanId) => {
    setDownloading(scanId);
    setError('');
    try {
      const response = await api.get(`/reports/scan/${scanId}/`, {
        responseType: 'blob',
      });
      const url  = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href  = url;
      link.setAttribute('download', `cropguard_scan_${scanId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccessMsg(t('reports.download_success'));
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch {
      setError(t('reports.download_error'));
    } finally {
      setDownloading(null);
    }
  };

  const downloadSummaryReport = async () => {
    setSummaryDownloading(true);
    setError('');
    try {
      const response = await api.get('/reports/summary/', {
        responseType: 'blob',
      });
      const url  = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href  = url;
      link.setAttribute('download', 'cropguard_summary_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccessMsg(t('reports.download_success'));
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch {
      setError(t('reports.download_error'));
    } finally {
      setSummaryDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-4xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">📄</div>
          <h1 className="text-3xl font-bold mb-2">{t('reports.title')}</h1>
          <p className="text-gray-400">{t('reports.subtitle')}</p>
        </div>

        {/* Success message */}
        {successMsg && (
          <div className="bg-primary-600/20 border border-primary-500/40 text-primary-300 rounded-xl px-4 py-3 text-sm mb-6 text-center">
            ✅ {successMsg}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {/* Summary report card */}
        <div className="glass-card p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white mb-1">
                📊 {t('reports.summary_title')}
              </h2>
              <p className="text-gray-400 text-sm">
                {t('reports.summary_desc')}
              </p>
            </div>
            <button
              onClick={downloadSummaryReport}
              disabled={summaryDownloading}
              className="btn-primary flex items-center gap-2 text-sm py-2 px-5 flex-shrink-0 ml-4"
            >
              {summaryDownloading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : '⬇️'}
              {t('reports.download_summary')}
            </button>
          </div>
        </div>

        {/* Individual scan reports */}
        <h2 className="text-lg font-bold text-white mb-4">
          🔬 {t('reports.scan_reports')}
        </h2>

        {loading && (
          <div className="glass-card p-12 text-center">
            <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-gray-400 text-sm">{t('common.loading')}</p>
          </div>
        )}

        {!loading && scans.length === 0 && (
          <div className="glass-card p-12 text-center">
            <div className="text-5xl mb-4">🌱</div>
            <p className="text-gray-400 text-sm">{t('reports.no_scans')}</p>
            <a href="/scanner" className="btn-primary inline-block mt-4 text-sm py-2 px-5">
              {t('dashboard.start_scanning')}
            </a>
          </div>
        )}

        {!loading && scans.length > 0 && (
          <div className="space-y-4">
            {scans.map((scan) => (
              <ScanReportCard
                key={scan.id}
                scan={scan}
                onDownload={downloadScanReport}
                downloading={downloading}
              />
            ))}
          </div>
        )}

      </main>
    </div>
  );
}