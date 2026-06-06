import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Profile API
export const profileApi = {
  getProfile: (userId = 1) => apiClient.get(`/api/profile?user_id=${userId}`),
  updateProfile: (data: any) => apiClient.put('/api/profile', data),
  getSkills: (userId = 1) => apiClient.get(`/api/profile/skills?user_id=${userId}`),
  getResumes: (userId = 1) => apiClient.get(`/api/profile/resumes?user_id=${userId}`),
};

// Jobs API
export const jobsApi = {
  listJobs: (params?: { status?: string; platform?: string; limit?: number; offset?: number }) =>
    apiClient.get('/api/jobs', { params }),
  getJob: (jobId: number) => apiClient.get(`/api/jobs/${jobId}`),
  addToQueue: (jobId: number, priority = 5) =>
    apiClient.post('/api/jobs/queue/add', { job_id: jobId, priority }),
  listQueue: (status = 'queued', limit = 50) =>
    apiClient.get('/api/jobs/queue/list', { params: { status, limit } }),
  removeFromQueue: (queueId: number) => apiClient.delete(`/api/jobs/queue/${queueId}`),
};

// Applications API
export const applicationsApi = {
  listApplications: (params?: { status?: string; platform?: string; limit?: number; offset?: number }) =>
    apiClient.get('/api/applications', { params }),
  getApplication: (appId: number) => apiClient.get(`/api/applications/${appId}`),
  getStats: () => apiClient.get('/api/applications/stats/overview'),
  getDailyStats: (days = 30) => apiClient.get(`/api/applications/stats/daily?days=${days}`),
  getPlatformStats: () => apiClient.get('/api/applications/stats/by-platform'),
};

// Daemon API
export const daemonApi = {
  getStatus: () => apiClient.get('/api/daemon/status'),
  start: (config: any) => apiClient.post('/api/daemon/start', config),
  stop: () => apiClient.post('/api/daemon/stop'),
  getLogs: (limit = 100) => apiClient.get(`/api/daemon/logs?limit=${limit}`),
  listConfigs: () => apiClient.get('/api/daemon/configs'),
};

// Questions & AI API
export const questionsApi = {
  listPending: (status = 'pending', limit = 50) =>
    apiClient.get('/api/questions/pending', { params: { status, limit } }),
  answerQuestion: (data: { question_id: number; answer: string; save_to_kb?: boolean; reuse_policy?: string }) =>
    apiClient.post('/api/questions/answer', data),
  batchAnswer: (data: { answers: Record<number, string>; save_to_kb?: boolean; reuse_policy?: string }) =>
    apiClient.post('/api/questions/batch-answer', data),
  getSuggestion: (data: { question_text: string; job_id?: number; field_type?: string }) =>
    apiClient.post('/api/questions/suggest', data),
  getKnowledgeBase: (limit = 100) => apiClient.get(`/api/questions/knowledge-base?limit=${limit}`),
  getStats: () => apiClient.get('/api/questions/stats'),
  generateCoverLetter: (jobId: number, userId = 1) =>
    apiClient.post('/api/questions/ai/cover-letter', { job_id: jobId, user_id: userId }),
  calculateMatchScore: (jobId: number, userId = 1) =>
    apiClient.post('/api/questions/ai/match-score', null, { params: { job_id: jobId, user_id: userId } }),
  analyzeResume: (jobId: number, userId = 1) =>
    apiClient.post('/api/questions/ai/analyze-resume', null, { params: { job_id: jobId, user_id: userId } }),
};
