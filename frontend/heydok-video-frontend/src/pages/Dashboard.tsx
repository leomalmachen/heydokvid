import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { roomService } from '../services/rooms';
import { 
  VideoCameraIcon, 
  CalendarIcon, 
  UserGroupIcon,
  PlusIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

interface Room {
  id: string;
  name: string;
  room_id: string;
  status: string;
  scheduled_start?: string;
  participant_count: number;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      const data = await roomService.listRooms();
      setRooms(data.rooms);
    } catch (error) {
      console.error('Failed to load rooms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickStart = async () => {
    try {
      const room = await roomService.createRoom({
        name: `Schnellbesprechung - ${new Date().toLocaleString('de-DE')}`,
        max_participants: 10,
        enable_recording: false,
        enable_chat: true,
        enable_screen_share: true,
        waiting_room_enabled: false
      });
      window.location.href = `/room/${room.room_id}`;
    } catch (error) {
      console.error('Failed to create room:', error);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Willkommen zurück, {user?.email}</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <button
          onClick={handleQuickStart}
          className="card hover:shadow-heydok-lg transition-shadow cursor-pointer group"
        >
          <div className="flex items-center">
            <div className="p-3 bg-heydok-light rounded-lg group-hover:bg-heydok-primary transition-colors">
              <VideoCameraIcon className="w-6 h-6 text-heydok-primary group-hover:text-white" />
            </div>
            <div className="ml-4">
              <h3 className="font-semibold text-gray-900">Sofort starten</h3>
              <p className="text-sm text-gray-500">Neue Videokonferenz beginnen</p>
            </div>
          </div>
        </button>

        <Link
          to="/schedule"
          className="card hover:shadow-heydok-lg transition-shadow cursor-pointer group"
        >
          <div className="flex items-center">
            <div className="p-3 bg-heydok-light rounded-lg group-hover:bg-heydok-primary transition-colors">
              <CalendarIcon className="w-6 h-6 text-heydok-primary group-hover:text-white" />
            </div>
            <div className="ml-4">
              <h3 className="font-semibold text-gray-900">Termin planen</h3>
              <p className="text-sm text-gray-500">Konferenz für später planen</p>
            </div>
          </div>
        </Link>

        <Link
          to="/join"
          className="card hover:shadow-heydok-lg transition-shadow cursor-pointer group"
        >
          <div className="flex items-center">
            <div className="p-3 bg-heydok-light rounded-lg group-hover:bg-heydok-primary transition-colors">
              <UserGroupIcon className="w-6 h-6 text-heydok-primary group-hover:text-white" />
            </div>
            <div className="ml-4">
              <h3 className="font-semibold text-gray-900">Raum beitreten</h3>
              <p className="text-sm text-gray-500">Mit Raum-ID beitreten</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Active Rooms */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Aktive Räume</h2>
          {user?.can_create_rooms && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary flex items-center"
            >
              <PlusIcon className="w-5 h-5 mr-2" />
              Neuer Raum
            </button>
          )}
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-heydok-primary mx-auto"></div>
          </div>
        ) : rooms.length === 0 ? (
          <div className="text-center py-8">
            <VideoCameraIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500">Keine aktiven Räume</p>
          </div>
        ) : (
          <div className="space-y-4">
            {rooms.map((room) => (
              <div
                key={room.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-heydok-primary transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{room.name}</h3>
                    <div className="flex items-center mt-1 text-sm text-gray-500">
                      <UserGroupIcon className="w-4 h-4 mr-1" />
                      {room.participant_count} Teilnehmer
                      {room.scheduled_start && (
                        <>
                          <ClockIcon className="w-4 h-4 ml-3 mr-1" />
                          {new Date(room.scheduled_start).toLocaleString('de-DE')}
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      room.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {room.status === 'active' ? 'Aktiv' : 'Geplant'}
                    </span>
                    <Link
                      to={`/room/${room.room_id}`}
                      className="btn-primary text-sm"
                    >
                      Beitreten
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 