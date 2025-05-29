import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api/v1';

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const roomService = {
  async listRooms() {
    const response = await axios.get(`${API_URL}/rooms`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async createRoom(data: {
    name: string;
    max_participants?: number;
    enable_recording?: boolean;
    enable_chat?: boolean;
    enable_screen_share?: boolean;
    waiting_room_enabled?: boolean;
  }) {
    const response = await axios.post(`${API_URL}/rooms`, data, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async getRoom(roomId: string) {
    const response = await axios.get(`${API_URL}/rooms/${roomId}`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  async getRoomToken(roomId: string, userName?: string) {
    const response = await axios.post(
      `${API_URL}/rooms/${roomId}/token`,
      { room_id: roomId, user_name: userName },
      { headers: getAuthHeader() }
    );
    return response.data;
  }
}; 