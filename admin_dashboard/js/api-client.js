/**
 * API client for Turantalim Admin Dashboard
 * 
 * This file contains all API endpoints and authentication logic
 * required for the admin dashboard to communicate with the backend.
 */

class ApiClient {
    constructor() {
        this.baseUrl = '/multilevel/api/admin/submissions/';
        this.token = localStorage.getItem('authToken');
    }

    /**
     * Set the authentication token
     * @param {string} token - JWT or token string
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('authToken', token);
    }

    /**
     * Clear the authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('authToken');
    }

    /**
     * Check if user is authenticated
     * @returns {boolean} - True if authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Get common headers for API requests
     * @returns {Object} - Headers object
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Token ${this.token}`;
        }

        return headers;
    }

    /**
     * Make API request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise} - Response promise
     */
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('/') ? endpoint : `${this.baseUrl}${endpoint}`;
        
        const defaultOptions = {
            headers: this.getHeaders(),
        };
        
        const fetchOptions = {
            ...defaultOptions,
            ...options,
        };
        
        if (options.body && typeof options.body === 'object') {
            fetchOptions.body = JSON.stringify(options.body);
        }
        
        try {
            const response = await fetch(url, fetchOptions);
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Handle unauthorized - clear token and redirect to login
                    this.clearToken();
                    window.location.href = '/admin-dashboard/login.html';
                    return null;
                }
                
                const errorData = await response.json();
                throw new Error(errorData.detail || 'API request failed');
            }
            
            if (response.status === 204) {
                return { success: true };
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    /**
     * Login user
     * @param {string} username - Username
     * @param {string} password - Password
     * @returns {Promise} - Login response
     */
    async login(username, password) {
        try {
            const response = await this.request('/api/token/', {
                method: 'POST',
                body: { username, password },
            });
            
            if (response && response.token) {
                this.setToken(response.token);
                return { success: true };
            }
            
            return { success: false, message: 'Invalid credentials' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    /**
     * Logout user
     */
    logout() {
        this.clearToken();
        window.location.href = '/admin_dashboard/login.html';
    }

    /**
     * Get submissions list
     * @param {Object} filters - Filter parameters
     * @returns {Promise} - Submissions list
     */
    async getSubmissions(filters = {}) {
        const queryParams = new URLSearchParams();
        
        if (filters.status) queryParams.append('status', filters.status);
        if (filters.section) queryParams.append('section', filters.section);
        if (filters.exam_level) queryParams.append('exam_level', filters.exam_level);
        if (filters.search) queryParams.append('search', filters.search);
        
        const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
        
        return await this.request(`${queryString}`);
    }

    /**
     * Get submission details
     * @param {number} submissionId - Submission ID
     * @returns {Promise} - Submission details
     */
    async getSubmission(submissionId) {
        return await this.request(`${submissionId}/`);
    }

    /**
     * Get submission media
     * @param {number} submissionId - Submission ID
     * @returns {Promise} - Submission media
     */
    async getSubmissionMedia(submissionId) {
        return await this.request(`${submissionId}/media/`);
    }

    /**
     * Update writing scores
     * @param {number} submissionId - Submission ID
     * @param {Object} data - Score data
     * @returns {Promise} - Update response
     */
    async updateWritingScores(submissionId, data) {
        return await this.request(`${submissionId}/writing/`, {
            method: 'PATCH',
            body: data
        });
    }

    /**
     * Update speaking scores
     * @param {number} submissionId - Submission ID
     * @param {Object} data - Score data
     * @returns {Promise} - Update response
     */
    async updateSpeakingScores(submissionId, data) {
        return await this.request(`${submissionId}/speaking/`, {
            method: 'PATCH',
            body: data
        });
    }
}

// Create and export API client instance
const apiClient = new ApiClient();
