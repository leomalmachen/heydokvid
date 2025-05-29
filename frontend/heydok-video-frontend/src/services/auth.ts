import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api/v1';

export const authService = {
  async login(external_id: string, api_key: string) {
    const response = await axios.post(`${API_URL}/auth/token`, {
      external_id,
      api_key
    });
    return response.data;
  },

  async getCurrentUser(token: string) {
    const response = await axios.get(`${API_URL}/users/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  }
}; 