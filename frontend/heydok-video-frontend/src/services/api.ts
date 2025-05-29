import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://f5e6-169-150-197-59.ngrok-free.app';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface CreateMeetingResponse {
  meeting_id: string;
  meeting_url: string;
  created_at: string;
  expires_at: string;
}

export interface JoinMeetingResponse {
  token: string;
  meeting_id: string;
  livekit_url: string;
  participant_id: string;
}

export interface MeetingInfoResponse {
  meeting_id: string;
  meeting_url: string;
  created_at: string;
  expires_at: string;
  status: string;
  name?: string;
}

export const meetingApi = {
  // Neues Meeting erstellen
  createMeeting: async (name?: string): Promise<CreateMeetingResponse> => {
    const response = await api.post('/api/v1/meetings/create', { name });
    return response.data;
  },

  // Meeting beitreten
  joinMeeting: async (meetingId: string, displayName: string): Promise<JoinMeetingResponse> => {
    const response = await api.post(`/api/v1/meetings/${meetingId}/join`, {
      display_name: displayName,
    });
    return response.data;
  },

  // Meeting-Info abrufen
  getMeetingInfo: async (meetingId: string): Promise<MeetingInfoResponse> => {
    const response = await api.get(`/api/v1/meetings/${meetingId}/info`);
    return response.data;
  },

  // Meeting verlassen
  leaveMeeting: async (meetingId: string, participantId: string): Promise<void> => {
    await api.delete(`/api/v1/meetings/${meetingId}/leave/${participantId}`);
  },
};

export default api; 