import React, { useState, useCallback } from 'react';
import {
  useTracks,
  useLocalParticipant,
  useRoomContext,
  useParticipants,
  TrackToggle,
  DisconnectButton,
  StartMediaButton,
  useTrackToggle
} from '@livekit/components-react';
import { Track, Room } from 'livekit-client';
import {
  MicrophoneIcon,
  VideoCameraIcon,
  ComputerDesktopIcon,
  PhoneXMarkIcon,
  ChatBubbleLeftRightIcon,
  EllipsisHorizontalIcon,
  UserGroupIcon,
  Cog6ToothIcon,
  XMarkIcon,
  PlayCircleIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import './MeetingControls.css';

interface MeetingControlsProps {
  onLeave?: () => void;
  onToggleChat?: () => void;
  onToggleParticipants?: () => void;
  onToggleSettings?: () => void;
  showRecording?: boolean;
  isRecording?: boolean;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  className?: string;
}

export const MeetingControls: React.FC<MeetingControlsProps> = ({
  onLeave,
  onToggleChat,
  onToggleParticipants,
  onToggleSettings,
  showRecording = false,
  isRecording = false,
  onStartRecording,
  onStopRecording,
  className = ''
}) => {
  const room = useRoomContext();
  const { localParticipant } = useLocalParticipant();
  const participants = useParticipants();
  
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [showMoreOptions, setShowMoreOptions] = useState(false);
  
  // Track toggles
  const {
    buttonProps: micButtonProps,
    enabled: micEnabled
  } = useTrackToggle({ source: Track.Source.Microphone });
  
  const {
    buttonProps: cameraButtonProps,
    enabled: cameraEnabled
  } = useTrackToggle({ source: Track.Source.Camera });

  const handleScreenShare = useCallback(async () => {
    if (!localParticipant) return;

    try {
      if (isScreenSharing) {
        // Stop screen sharing
        await localParticipant.setScreenShareEnabled(false);
        setIsScreenSharing(false);
        toast.success('Screen sharing stopped');
      } else {
        // Start screen sharing
        await localParticipant.setScreenShareEnabled(true);
        setIsScreenSharing(true);
        toast.success('Screen sharing started');
      }
    } catch (error) {
      console.error('Screen share error:', error);
      toast.error('Failed to toggle screen sharing');
    }
  }, [localParticipant, isScreenSharing]);

  const handleRecording = useCallback(async () => {
    try {
      if (isRecording) {
        if (onStopRecording) {
          await onStopRecording();
          toast.success('Recording stopped');
        }
      } else {
        if (onStartRecording) {
          await onStartRecording();
          toast.success('Recording started');
        }
      }
    } catch (error) {
      console.error('Recording error:', error);
      toast.error('Failed to toggle recording');
    }
  }, [isRecording, onStartRecording, onStopRecording]);

  const handleLeave = useCallback(() => {
    if (onLeave) {
      onLeave();
    } else {
      room?.disconnect();
    }
  }, [room, onLeave]);

  const participantCount = participants.length;

  return (
    <div className={`meeting-controls ${className}`}>
      <div className="controls-container">
        {/* Left side - Meeting info */}
        <div className="controls-left">
          <div className="meeting-info">
            <span className="participant-count">
              <UserGroupIcon className="w-4 h-4" />
              {participantCount}
            </span>
            {isRecording && (
              <div className="recording-indicator">
                <PlayCircleIcon className="w-4 h-4 text-red-500 animate-pulse" />
                <span className="text-red-500 text-sm font-medium">REC</span>
              </div>
            )}
          </div>
        </div>

        {/* Center - Main controls */}
        <div className="controls-center">
          {/* Microphone */}
          <button
            {...micButtonProps}
            className={`control-btn ${micEnabled ? 'enabled' : 'disabled'}`}
            title={micEnabled ? 'Mute microphone' : 'Unmute microphone'}
          >
            {micEnabled ? (
              <MicrophoneIcon className="w-5 h-5" />
            ) : (
              <XMarkIcon className="w-5 h-5" />
            )}
          </button>

          {/* Camera */}
          <button
            {...cameraButtonProps}
            className={`control-btn ${cameraEnabled ? 'enabled' : 'disabled'}`}
            title={cameraEnabled ? 'Turn off camera' : 'Turn on camera'}
          >
            {cameraEnabled ? (
              <VideoCameraIcon className="w-5 h-5" />
            ) : (
              <XMarkIcon className="w-5 h-5" />
            )}
          </button>

          {/* Screen Share */}
          <button
            onClick={handleScreenShare}
            className={`control-btn ${isScreenSharing ? 'active' : ''}`}
            title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
          >
            <ComputerDesktopIcon className="w-5 h-5" />
          </button>

          {/* Recording (if enabled) */}
          {showRecording && (
            <button
              onClick={handleRecording}
              className={`control-btn ${isRecording ? 'recording' : ''}`}
              title={isRecording ? 'Stop recording' : 'Start recording'}
            >
              {isRecording ? (
                <StopIcon className="w-5 h-5" />
              ) : (
                <PlayCircleIcon className="w-5 h-5" />
              )}
            </button>
          )}

          {/* Leave */}
          <button
            onClick={handleLeave}
            className="control-btn leave-btn"
            title="Leave meeting"
          >
            <PhoneXMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Right side - Additional controls */}
        <div className="controls-right">
          {/* Chat */}
          {onToggleChat && (
            <button
              onClick={onToggleChat}
              className="control-btn secondary"
              title="Toggle chat"
            >
              <ChatBubbleLeftRightIcon className="w-5 h-5" />
            </button>
          )}

          {/* Participants */}
          {onToggleParticipants && (
            <button
              onClick={onToggleParticipants}
              className="control-btn secondary"
              title="Show participants"
            >
              <UserGroupIcon className="w-5 h-5" />
            </button>
          )}

          {/* More options */}
          <div className="relative">
            <button
              onClick={() => setShowMoreOptions(!showMoreOptions)}
              className="control-btn secondary"
              title="More options"
            >
              <EllipsisHorizontalIcon className="w-5 h-5" />
            </button>

            {showMoreOptions && (
              <div className="more-options-menu">
                {onToggleSettings && (
                  <button
                    onClick={() => {
                      onToggleSettings();
                      setShowMoreOptions(false);
                    }}
                    className="menu-item"
                  >
                    <Cog6ToothIcon className="w-4 h-4" />
                    Settings
                  </button>
                )}
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href);
                    toast.success('Meeting link copied to clipboard');
                    setShowMoreOptions(false);
                  }}
                  className="menu-item"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy meeting link
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}; 