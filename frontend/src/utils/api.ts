import axios, { AxiosResponse } from 'axios';

const API_BASE_URL = '/api';  // Proxy to backend (live calls)

interface TimeSeriesData {
    timestamp: string;
    value: number;
}

interface User {
    id: string;
    username: string;
    fullname: string;
    email?: string;
}

interface AuthResponse {
    token: string;
    user: User;
}

interface ApiResponse<T> {
    success: boolean;
    data: T;
    message?: string;
}

class ApiClient {
    private api = axios.create({
        baseURL: API_BASE_URL,
        timeout: 10000,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    constructor() {
        this.api.interceptors.request.use(
            (config) => {
                const token = localStorage.getItem('token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );
    }

    // Generic post method for OTP endpoints
    async post(endpoint: string, data: any): Promise<any> {
        try {
            const response = await this.api.post(endpoint, data);
            return response.data;  // Extract data
        } catch (error: any) {
            console.error(`POST ${endpoint} failed:`, error.message, error.response?.data || error);
            throw error;
        }
    }

    // Generic get method for other endpoints
    async get(endpoint: string): Promise<any> {
        try {
            const response = await this.api.get(endpoint);
            return response.data;  // Extract data
        } catch (error: any) {
            console.error(`GET ${endpoint} failed:`, error.message, error.response?.data || error);
            throw error;
        }
    }

    async register(userData: { username: string; fullname: string; password: string; confirmPassword: string; isInstaller: boolean }): Promise<AuthResponse> {
        console.log('Register payload:', userData);
        try {
            const response = await this.api.post('/auth/register', userData);  // Use generic post
            return response.data;  // Extract data as AuthResponse
        } catch (error: any) {
            console.error('Registration failed:', error.message, error.response?.data || error);
            throw error;
        }
    }

    async login(credentials: { username: string; password: string; isInstaller: boolean }): Promise<AuthResponse> {
        console.log('Login payload:', credentials);
        try {
            const response = await this.api.post('/auth/login', credentials);  // Use generic post
            return response.data;  // Extract data as AuthResponse
        } catch (error: any) {
            console.error('Login failed:', error.message, error.response?.data || error);
            throw error;
        }
    }

    async logout(): Promise<void> {
        try {
            await this.api.post('/auth/logout');
        } catch (error: any) {
            console.error('Logout failed:', error.message, error.response?.data || error);
            throw error;
        }
    }

    async getPlants(userType = 'demo') {
        try {
            const response = await this.api.get('/dashboard/plants');  // Use generic get
            return response.data;
        } catch (error: any) {
            console.error('Error fetching plants:', error.message, error.response?.data || error);
            return [];  // Empty fallback
        }
    }

    async getDevices(userType = 'demo') {
        try {
            const response = await this.api.get('/dashboard/devices');  // Use generic get
            return response.data;
        } catch (error: any) {
            console.error('Error fetching devices:', error.message, error.response?.data || error);
            return [];  // Empty fallback
        }
    }

    async getMultipleTimeSeriesData(deviceId: string, metrics: string[], timeRange: string): Promise<TimeSeriesData[]> {
        try {
            const response = await this.api.get(`/dashboard/timeseries/${deviceId}`, {
                params: { metrics: metrics.join(','), timeRange }
            });
            return response.data;
        } catch (error: any) {
            console.error('Error fetching time series data:', error.message, error.response?.data || error);
            return [];  // Empty fallback
        }
    }
}

export const apiClient = new ApiClient();