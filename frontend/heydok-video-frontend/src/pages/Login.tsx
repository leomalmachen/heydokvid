import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const [externalId, setExternalId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(externalId, apiKey);
      navigate('/dashboard');
    } catch (err) {
      setError('Ungültige Anmeldedaten');
    } finally {
      setLoading(false);
    }
  };

  // Demo-Login für Tests
  const handleDemoLogin = () => {
    setExternalId('demo-physician');
    setApiKey('your_secret_key_here_change_me_32_chars_min'.substring(0, 32));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-heydok-primary mb-2">heydok</h1>
          <p className="text-gray-600">Video Conferencing System</p>
        </div>

        <div className="card">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Anmelden</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="externalId" className="block text-sm font-medium text-gray-700 mb-1">
                External ID
              </label>
              <input
                id="externalId"
                type="text"
                value={externalId}
                onChange={(e) => setExternalId(e.target.value)}
                className="input"
                placeholder="Ihre External ID"
                required
              />
            </div>

            <div>
              <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-1">
                API Key
              </label>
              <input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="input"
                placeholder="Ihr API Key"
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Anmelden...' : 'Anmelden'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={handleDemoLogin}
              className="btn-secondary w-full"
            >
              Demo-Zugang verwenden
            </button>
            <p className="text-xs text-gray-500 text-center mt-2">
              Für Testzwecke
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login; 