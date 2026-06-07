// src/api.js

const API_BASE = (process.env.REACT_APP_API_BASE_URL || '').replace(/\/$/, '');

const URLS = {
  auth:      `${API_BASE}/api/module01`,
  session:   `${API_BASE}/api/module02`,
  device:    `${API_BASE}/api/module03`,
  activation:`${API_BASE}/api/module04`,
  rbac:      `${API_BASE}/api/module05`,
  questions: `${API_BASE}/api/module06`,
  random:    `${API_BASE}/api/module07`,
  timer:     `${API_BASE}/api/module08`,
  tabmon:    `${API_BASE}/api/module10`,
  clipboard: `${API_BASE}/api/module11`,
  activity:  `${API_BASE}/api/module12`,
  behavior:  `${API_BASE}/api/module15`,
  similarity:`${API_BASE}/api/module16`,
  risk:      `${API_BASE}/api/module17`,
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
    const data = await response.json();

    const authFailure = response.status === 401 && Boolean(token);
    if (authFailure) {
      localStorage.clear();
      window.location.href = '/';
      throw new Error('Session expired. Please login again.');
    }

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

// ================= SESSION (Modules 02 & 14) =================
export const invalidateSession = () =>
  fetchApi(`${URLS.session}/invalidate-session`, {
    method: 'POST',
    body: JSON.stringify({ reason: 'user_logout' })
  });

export const registerSession = () =>
  fetchApi(`${API_BASE}/api/module14/register-session`, {
    method: 'POST',
    body: JSON.stringify({})
  });

// ================= DEVICE (Module 03) =================
export const registerDevice = () => {
  const payload = {
    user_agent: navigator.userAgent,
    platform: navigator.platform,
    screen_resolution: `${window.screen.width}x${window.screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    color_depth: String(window.screen.colorDepth)
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
  fetchApi(`${URLS.timer}/create-exam`, { method: 'POST', body: JSON.stringify({ exam_id, exam_title, duration_minutes: parseInt(duration_minutes) }) });

export const startTimer = (exam_id) => 
  fetchApi(`${URLS.timer}/start-timer`, { method: 'POST', body: JSON.stringify({ exam_id }) });

export const getTimeRemaining = (exam_id) => 
  fetchApi(`${URLS.timer}/time-remaining/${exam_id}`);

export const submitExam = (exam_id, answers) => 
  fetchApi(`${URLS.timer}/submit-exam`, { method: 'POST', body: JSON.stringify({ exam_id, answers }) });

export const validateAnswer = (exam_id, answer) =>
  fetchApi(`${API_BASE}/api/module09/validate-input`, {
    method: 'POST',
    body: JSON.stringify({ exam_id, answer })
  });

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
  fetchApi(`${URLS.clipboard}/clipboard-event`, { method: 'POST', body: JSON.stringify({ exam_id, event_type }) });

export const logActivity = (exam_id, action) => 
  fetchApi(`${URLS.activity}/log-activity`, { method: 'POST', body: JSON.stringify({ exam_id, action }) });

// ================= RISK SCORE (Module 17) =================
export const getRiskDashboard = (exam_id) => 
  fetchApi(`${URLS.risk}/dashboard?exam_id=${exam_id}`);

export const runSimilarityAnalysis = (exam_id) =>
  fetchApi(`${URLS.similarity}/check-similarity`, {
    method: 'POST',
    body: JSON.stringify({ exam_id })
  });
