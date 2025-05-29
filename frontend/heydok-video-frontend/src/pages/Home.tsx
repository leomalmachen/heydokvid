import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, Users, Link2, ArrowRight } from 'lucide-react';
import { createMeeting } from '../services/meetingService';

export default function Home() {
  const navigate = useNavigate();
  const [isCreating, setIsCreating] = useState(false);
  const [meetingUrl, setMeetingUrl] = useState('');
  const [showCopySuccess, setShowCopySuccess] = useState(false);

  const handleCreateMeeting = async () => {
    setIsCreating(true);
    try {
      const response = await createMeeting();
      setMeetingUrl(response.meeting_url);
      
      // Auto-copy to clipboard
      await navigator.clipboard.writeText(response.meeting_url);
      setShowCopySuccess(true);
      setTimeout(() => setShowCopySuccess(false), 3000);
    } catch (error) {
      console.error('Failed to create meeting:', error);
      alert('Failed to create meeting. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinMeeting = () => {
    if (meetingUrl) {
      const meetingId = meetingUrl.split('/meeting/')[1];
      navigate(`/meeting/${meetingId}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Video Meetings Made Simple
            </h1>
            <p className="text-xl text-gray-600">
              Start a video call instantly. No sign-ups, no downloads.
            </p>
          </div>

          {/* Main Action Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            {!meetingUrl ? (
              <div className="text-center">
                <button
                  onClick={handleCreateMeeting}
                  disabled={isCreating}
                  className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  {isCreating ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                      Creating meeting...
                    </>
                  ) : (
                    <>
                      <Video className="w-6 h-6 mr-3" />
                      Start a new meeting
                    </>
                  )}
                </button>
                
                <div className="mt-8 pt-8 border-t border-gray-200">
                  <p className="text-gray-600 mb-4">Have a meeting link?</p>
                  <input
                    type="text"
                    placeholder="Enter meeting link or code"
                    className="w-full max-w-md px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value) {
                        const value = e.currentTarget.value;
                        if (value.includes('/meeting/')) {
                          window.location.href = value;
                        } else {
                          navigate(`/meeting/${value}`);
                        }
                      }
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className="text-center">
                <div className="mb-6">
                  <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-lg mb-4">
                    <Video className="w-5 h-5 mr-2" />
                    Meeting created successfully!
                  </div>
                  
                  {showCopySuccess && (
                    <div className="text-sm text-green-600 mb-2">
                      ✓ Link copied to clipboard
                    </div>
                  )}
                </div>

                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <p className="text-sm text-gray-600 mb-2">Share this link:</p>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={meetingUrl}
                      readOnly
                      className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-md text-sm"
                    />
                    <button
                      onClick={async () => {
                        await navigator.clipboard.writeText(meetingUrl);
                        setShowCopySuccess(true);
                        setTimeout(() => setShowCopySuccess(false), 3000);
                      }}
                      className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
                    >
                      <Link2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="flex gap-4 justify-center">
                  <button
                    onClick={handleJoinMeeting}
                    className="inline-flex items-center px-6 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Join meeting
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </button>
                  
                  <button
                    onClick={() => {
                      setMeetingUrl('');
                      setShowCopySuccess(false);
                    }}
                    className="px-6 py-3 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Create another
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg p-6 text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Video className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">No downloads</h3>
              <p className="text-gray-600 text-sm">
                Works directly in your browser. No apps or plugins needed.
              </p>
            </div>
            
            <div className="bg-white rounded-lg p-6 text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">No sign-ups</h3>
              <p className="text-gray-600 text-sm">
                Start or join meetings instantly. No account required.
              </p>
            </div>
            
            <div className="bg-white rounded-lg p-6 text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Link2 className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Share easily</h3>
              <p className="text-gray-600 text-sm">
                One link is all you need. Share it and start talking.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 