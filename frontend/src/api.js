// src/api.js

const URLS = {
  auth:      'http://localhost:5001/api/module01',
  session:   'http://localhost:5002/api/module02',
  device:    'http://localhost:5003/api/module03',
  activation:'http://localhost:5004/api/module04',
  rbac:      'http://localhost:5005/api/module05',
  questions: 'http://localhost:5006/api/module06',
  random:    'http://localhost:5007/api/module07',
  timer:     'http://localhost:5008/api/module08',
  tabmon:    'http://localhost:5010/api/module10',
  clipboard: 'http://localhost:5011/api/module11',
  activity:  'http://localhost:5012/api/module12',
  risk:      'http://localhost:5017/api/module17',
};

// Helper to handle tokens and common fetch logic
async function fetchApi(url, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  };

  try {
    const response = await fetch(url, { ...options, headers });
    
    // Auto-logout on 401 Unauthorized
    if (response.status === 401) {
      localStorage.clear();
      window.location.href = '/';
      throw new Error('Session expired. Please login again.');
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.error || 'An API error occurred');
    }
    
    return data;
  } catch (error) {
    console.error('API Call Failed:', url, error.message);
    throw error;
  }
}

// ================= AUTH (Module 01) =================
export const login = (username, password) => 
  fetchApi(`${URLS.auth}/login`, { method: 'POST', body: JSON.stringify({ username, password }) });

export const verifyOtp = (user_id, otp) => 
  fetchApi(`${URLS.auth}/verify-otp`, { method: 'POST', body: JSON.stringify({ user_id, otp }) });

export const register = (username, password, role) => 
  fetchApi(`${URLS.auth}/register`, { method: 'POST', body: JSON.stringify({ username, password, role }) });

// ================= DEVICE (Module 03) =================
export const registerDevice = () => {
  const payload = {
    exam_id: "global", // Default for login phase
    device_fingerprint: {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      screenResolution: `${window.screen.width}x${window.screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      colorDepth: window.screen.colorDepth
    }
  };
  return fetchApi(`${URLS.device}/register-device`, { method: 'POST', body: JSON.stringify(payload) });
};

// ================= ACTIVATION (Module 04) =================
export const generateCode = (exam_id) => 
  fetchApi(`${URLS.activation}/generate-code`, { method: 'POST', body: JSON.stringify({ exam_id }) });

export const validateCode = (code, exam_id) => 
  fetchApi(`${URLS.activation}/validate-code`, { method: 'POST', body: JSON.stringify({ code, exam_id }) });

// ================= EXAM & TIMER (Module 08) =================
export const createExam = (exam_id, exam_title, duration_minutes) => 
  fetchApi(`${URLS.timer}/create-exam`, { method: 'POST', body: JSON.stringify({ exam_id, title: exam_title, duration_minutes: parseInt(duration_minutes) }) });

export const startTimer = (exam_id) => 
  fetchApi(`${URLS.timer}/start-timer`, { method: 'POST', body: JSON.stringify({ exam_id }) });

export const getTimeRemaining = (exam_id) => 
  fetchApi(`${URLS.timer}/time-remaining/${exam_id}`);

export const submitExam = (exam_id, answers) => 
  fetchApi(`${URLS.timer}/submit-exam`, { method: 'POST', body: JSON.stringify({ exam_id, answers }) });

export const getExamStatus = (exam_id) => 
  fetchApi(`${URLS.timer}/exam-status/${exam_id}`);

// ================= QUESTIONS (Module 06 & 07) =================
export const addQuestions = (exam_id, questions) => 
  fetchApi(`${URLS.questions}/add-questions`, { method: 'POST', body: JSON.stringify({ exam_id, questions }) });

export const releaseQuestions = (exam_id) => 
  fetchApi(`${URLS.questions}/release-questions`, { method: 'POST', body: JSON.stringify({ exam_id }) });

export const getRandomQuestions = (exam_id) => 
  fetchApi(`${URLS.random}/randomized-questions/${exam_id}`);

// ================= MONITORING (Modules 10, 11, 12) =================
export const logTabSwitch = (exam_id, event_type) => 
  fetchApi(`${URLS.tabmon}/tab-switch`, { method: 'POST', body: JSON.stringify({ exam_id, event_type }) });

export const logClipboard = (exam_id, event_type) => 
  fetchApi(`${URLS.clipboard}/clipboard-event`, { method: 'POST', body: JSON.stringify({ exam_id, action: event_type }) });

export const logActivity = (exam_id, action) => 
  fetchApi(`${URLS.activity}/log-activity`, { method: 'POST', body: JSON.stringify({ exam_id, action }) });

// ================= RISK SCORE (Module 17) =================
export const getRiskDashboard = (exam_id) => 
  fetchApi(`${URLS.risk}/dashboard?exam_id=${exam_id}`);