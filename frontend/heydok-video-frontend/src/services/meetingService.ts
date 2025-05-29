import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

export interface SimpleMeetingResponse {
  meeting_id: string;
  meeting_url: string;
  created_at: string;
  expires_at: string;
  status: string;
}

export interface SimpleMeetingTokenResponse {
  token: string;
  meeting_id: string;
  livekit_url: string;
  participant_id: string;
}

export const createMeeting = async (name?: string): Promise<SimpleMeetingResponse> => {
  const response = await axios.post(`${API_BASE_URL}/meetings/create`, {
    name
  });
  return response.data;
};

export const joinMeeting = async (meetingId: string, displayName: string): Promise<SimpleMeetingTokenResponse> => {
  const response = await axios.post(`${API_BASE_URL}/meetings/${meetingId}/join`, {
    display_name: displayName
  });
  return response.data;
};

export const getMeetingInfo = async (meetingId: string): Promise<SimpleMeetingResponse> => {
  const response = await axios.get(`${API_BASE_URL}/meetings/${meetingId}/info`);
  return response.data;
}; 