const BASE = {
  auth:       'http://localhost:5001/api/module01',
  session:    'http://localhost:5002/api/module02',
  device:     'http://localhost:5003/api/module03',
  activation: 'http://localhost:5004/api/module04',
  rbac:       'http://localhost:5005/api/module05',
  questions:  'http://localhost:5006/api/module06',
  random:     'http://localhost:5007/api/module07',
  timer:      'http://localhost:5008/api/module08',
  tabmon:     'http://localhost:5010/api/module10',
  clipboard:  'http://localhost:5011/api/module11',
  activity:   'http://localhost:5012/api/module12',
  risk:       'http://localhost:5017/api/module17',
};

const token = () => localStorage.getItem('token');

const headers = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token()}`
});

const post = async (url, body) => {
  const r = await fetch(url, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  return r.json();
};

const get = async (url) => {
  const r = await fetch(url, { headers: headers() });
  return r.json();
};

// AUTH
export const login = (username, password) =>
  post(`${BASE.auth}/login`, { username, password });

export const register = (username, password, role) =>
  post(`${BASE.auth}/register`, { username, password, role });

export const verifyOtp = (user_id, otp) =>
  post(`${BASE.auth}/verify-otp`, { user_id, otp });

export const getExamState = (exam_id) =>
  get(`http://localhost:5001/api/exam/state/${exam_id}`);

// DEVICE
export const registerDevice = () => {
  const components = {
    user_agent: navigator.userAgent,
    platform: navigator.platform,
    screen_resolution: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    color_depth: String(screen.colorDepth)
  };
  return post(`${BASE.device}/register-device`, components);
};

export const verifyDevice = () => {
  const components = {
    user_agent: navigator.userAgent,
    platform: navigator.platform,
    screen_resolution: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    color_depth: String(screen.colorDepth)
  };
  return post(`${BASE.device}/verify-device`, components);
};

// ACTIVATION
export const generateCode = (exam_id) =>
  post(`${BASE.activation}/generate-code`, { exam_id, student_id: 'any' });

export const validateCode = (code, exam_id) =>
  post(`${BASE.activation}/validate-code`, { code, exam_id });

// EXAM / TIMER
export const createExam = (exam_id, exam_title, duration_minutes) =>
  post(`${BASE.timer}/create-exam`, { exam_id, exam_title, duration_minutes });

export const startTimer = (exam_id) =>
  post(`${BASE.timer}/start-timer`, { exam_id });

export const getTimeRemaining = (exam_id) =>
  get(`${BASE.timer}/time-remaining/${exam_id}`);

export const submitExam = (exam_id, answers) =>
  post(`${BASE.timer}/submit-exam`, { exam_id, answers });

// QUESTIONS
export const addQuestions = (exam_id, questions) =>
  post(`${BASE.questions}/add-questions`, { exam_id, questions });

export const releaseQuestions = (exam_id) =>
  post(`${BASE.questions}/release-questions`, { exam_id });

export const getRandomQuestions = (exam_id) =>
  get(`${BASE.random}/randomized-questions/${exam_id}`);

// MONITORING
export const logTabSwitch = (exam_id, event_type) =>
  post(`${BASE.tabmon}/tab-switch`, { exam_id, event_type });

export const logClipboard = (exam_id, event_type) =>
  post(`${BASE.clipboard}/clipboard-event`, { exam_id, event_type });

export const logActivity = (exam_id, action, details = {}) =>
  post(`${BASE.activity}/log-activity`, { exam_id, action, details });

// ACTIVATION CODE (Teacher)
export const getExamCodes = (exam_id) =>
  get(`${BASE.activation}/exam-codes/${exam_id}`);

// RISK DASHBOARD
export const getRiskDashboard = (exam_id) =>
  get(`${BASE.risk}/dashboard?exam_id=${exam_id}`);

export const getExamStatus = (exam_id) =>
  get(`${BASE.timer}/exam-status/${exam_id}`);