import axios from 'axios';

const BASE_URL = 'http://localhost:5000/api';

const apiService = {
  getDashboardData: async () => {
    try {
      const response = await axios.get(`${BASE_URL}/dashboard-data`);
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  },

  processTransaction: async (transactionData) => {
    try {
      const response = await axios.post(`${BASE_URL}/process-transaction`, transactionData);
      return response.data;
    } catch (error) {
      console.error('Error processing transaction:', error);
      throw error;
    }
  },

  getHeatMapData: async () => {
    try {
      const response = await axios.get(`${BASE_URL}/heat-map-data`);
      return response.data;
    } catch (error) {
      console.error('Error fetching heat map data:', error);
      throw error;
    }
  }
};

export default apiService;
