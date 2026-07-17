import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import api from '../api/axios';

export default function ScannerPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleImageSelect = useCallback((file) => {
    if (!file) return;

    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type)) {
      setError(t('scanner.error_file_type'));
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError(t('scanner.error_file_size'));
      return;
    }

    setError('');
    setImage(file);
    setImagePreview(URL.createObjectURL(file));
  }, [t]);

  const handleFileChange = (e) => handleImageSelect(e.target.files[0]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    handleImageSelect(e.dataTransfer.files[0]);
  }, [handleImageSelect]);

  const handleDragOver = (e) => e.preventDefault();

  const handleScan = async () => {
    if (!image) return;

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('image', image);

      const response = await api.post('/scan/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Navigate to results page with the scan data
      navigate('/results', { state: { result: response.data } });

    } catch (err) {
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError(t('common.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  const clearImage = () => {
    setImage(null);
    setImagePreview(null);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <main className="max-w-3xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="text-5xl mb-4">🔬</div>
          <h1 className="text-3xl font-bold mb-2">{t('scanner.title')}</h1>
          <p className="text-gray-400">{t('scanner.subtitle')}</p>
        </div>

        {/* Upload Area */}
        {!imagePreview ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="glass-card p-10 text-center border-2 border-dashed border-white/20 hover:border-primary-500/50 transition-all duration-300 cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="text-6xl mb-4">📷</div>
            <h3 className="text-lg font-semibold text-white mb-2">
              {t('scanner.drop_title')}
            </h3>
            <p className="text-gray-400 text-sm mb-6">
              {t('scanner.drop_subtitle')}
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {/* Upload from gallery */}
              <button
                onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                className="btn-primary text-sm py-2 px-6"
              >
                📁 {t('scanner.btn_upload')}
              </button>

              {/* Camera capture — works on mobile and desktop */}
              <button
                onClick={(e) => { e.stopPropagation(); cameraInputRef.current?.click(); }}
                className="btn-secondary text-sm py-2 px-6"
              >
                📸 {t('scanner.btn_camera')}
              </button>
            </div>

            <p className="text-gray-500 text-xs mt-4">
              {t('scanner.supported_formats')}
            </p>

            {/* Hidden inputs */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/webp"
              onChange={handleFileChange}
              className="hidden"
            />
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        ) : (
          /* Image Preview */
          <div className="glass-card p-6">
            <div className="relative">
              <img
                src={imagePreview}
                alt="Selected plant"
                className="w-full max-h-96 object-contain rounded-xl bg-black/20"
              />
              <button
                onClick={clearImage}
                className="absolute top-3 right-3 w-8 h-8 bg-red-600/80 hover:bg-red-600 rounded-full flex items-center justify-center text-white text-sm transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">{t('scanner.selected_file')}</p>
                <p className="text-white text-sm font-medium truncate max-w-xs">
                  {image?.name}
                </p>
                <p className="text-gray-500 text-xs">
                  {image ? `${(image.size / 1024).toFixed(0)} KB` : ''}
                </p>
              </div>
              <button onClick={clearImage} className="btn-secondary text-sm py-2 px-4">
                {t('scanner.btn_change')}
              </button>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mt-4 bg-red-600/20 border border-red-500/40 text-red-300 rounded-xl px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {/* Scan Button */}
        {imagePreview && (
          <button
            onClick={handleScan}
            disabled={loading}
            className="btn-primary w-full mt-6 flex items-center justify-center gap-3 text-base py-4"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {t('scanner.scanning')}
              </>
            ) : (
              <>
                🔬 {t('scanner.btn_scan')}
              </>
            )}
          </button>
        )}

        {/* Info note */}
        <div className="mt-8 glass-card p-4">
          <p className="text-gray-400 text-xs leading-relaxed text-center">
            🌐 {t('scanner.api_note')}
          </p>
        </div>

      </main>
    </div>
  );
}