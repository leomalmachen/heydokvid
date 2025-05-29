import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, Users, Calendar, ArrowRight } from 'lucide-react';
import { meetingApi } from '../services/api';
import toast from 'react-hot-toast';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [meetingLink, setMeetingLink] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateMeeting = async () => {
    try {
      setIsCreating(true);
      const response = await meetingApi.createMeeting();
      navigate(`/meeting/${response.meeting_id}`);
    } catch (error) {
      toast.error('Fehler beim Erstellen des Meetings');
      console.error('Error creating meeting:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinMeeting = () => {
    if (!meetingLink.trim()) {
      toast.error('Bitte geben Sie einen Meeting-Link ein');
      return;
    }

    // Extrahiere Meeting-ID aus dem Link
    const meetingIdMatch = meetingLink.match(/meeting\/([a-z]{3}-[a-z]{4}-[a-z]{3})/);
    if (meetingIdMatch) {
      navigate(`/meeting/${meetingIdMatch[1]}`);
    } else {
      // Versuche es als direkte Meeting-ID
      const directIdMatch = meetingLink.match(/^([a-z]{3}-[a-z]{4}-[a-z]{3})$/);
      if (directIdMatch) {
        navigate(`/meeting/${directIdMatch[1]}`);
      } else {
        toast.error('Ungültiger Meeting-Link oder Code');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Video className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Video Meeting</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-2 gap-8 items-center">
          {/* Left Column - Hero Content */}
          <div>
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Premium-Videokonferenzen. Jetzt für alle kostenlos.
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Wir haben unseren sicheren Videokonferenzdienst für alle Nutzer kostenlos verfügbar gemacht.
            </p>

            {/* Action Buttons */}
            <div className="space-y-4">
              <button
                onClick={handleCreateMeeting}
                disabled={isCreating}
                className="w-full sm:w-auto bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Video className="h-5 w-5" />
                <span>{isCreating ? 'Meeting wird erstellt...' : 'Neues Meeting'}</span>
              </button>

              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  placeholder="Meeting-Code oder Link eingeben"
                  value={meetingLink}
                  onChange={(e) => setMeetingLink(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleJoinMeeting()}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleJoinMeeting}
                  className="px-6 py-3 text-blue-600 font-medium hover:bg-blue-50 rounded-lg transition-colors flex items-center space-x-2"
                >
                  <span>Teilnehmen</span>
                  <ArrowRight className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Features */}
            <div className="mt-12 grid grid-cols-3 gap-6">
              <div className="text-center">
                <Users className="h-8 w-8 text-gray-600 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Bis zu 100 Teilnehmer</p>
              </div>
              <div className="text-center">
                <Calendar className="h-8 w-8 text-gray-600 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Keine Zeitbegrenzung</p>
              </div>
              <div className="text-center">
                <Video className="h-8 w-8 text-gray-600 mx-auto mb-2" />
                <p className="text-sm text-gray-600">HD-Videoqualität</p>
              </div>
            </div>
          </div>

          {/* Right Column - Image */}
          <div className="hidden md:block">
            <div className="bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl p-8 h-96 flex items-center justify-center">
              <div className="text-center">
                <Video className="h-24 w-24 text-blue-600 mx-auto mb-4" />
                <p className="text-xl font-medium text-gray-800">
                  Starten Sie jetzt Ihr Meeting
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default HomePage; 