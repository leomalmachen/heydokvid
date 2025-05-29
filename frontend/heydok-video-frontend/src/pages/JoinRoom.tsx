import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const JoinRoom: React.FC = () => {
  const navigate = useNavigate();
  const { roomId: urlRoomId } = useParams();
  const [roomId, setRoomId] = useState(urlRoomId || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (roomId.trim()) {
      navigate(`/room/${roomId.trim()}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-8"
        >
          <ArrowLeftIcon className="w-5 h-5 mr-2" />
          Zurück zum Dashboard
        </button>

        <div className="card">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Raum beitreten</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="roomId" className="block text-sm font-medium text-gray-700 mb-1">
                Raum-ID
              </label>
              <input
                id="roomId"
                type="text"
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
                className="input"
                placeholder="Raum-ID eingeben"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Geben Sie die Raum-ID ein, die Sie vom Organisator erhalten haben
              </p>
            </div>

            <button
              type="submit"
              className="btn-primary w-full"
            >
              Raum beitreten
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default JoinRoom; 