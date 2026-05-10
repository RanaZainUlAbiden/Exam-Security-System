import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  createExam, 
  addQuestions, 
  releaseQuestions, 
  generateCode, 
  getExamStatus, 
  getRiskDashboard 
} from '../api';

export default function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState(1);
  const username = localStorage.getItem('username') || 'Teacher';
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <div>
      <nav className="navbar">
        <h1>Teacher Portal</h1>
        <div className="nav-actions">
          <span>Instructor: {username}</span>
          <button className="btn btn-outline" style={{ color: 'white', borderColor: 'white' }} onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="container">
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="tabs" style={{ marginBottom: 0, background: '#f9fafb', padding: '0 1rem' }}>
            {['Create Exam', 'Manage Questions', 'Activation Codes', 'Monitor & Risk'].map((tab, idx) => (
              <div 
                key={idx}
                className={`tab ${activeTab === idx + 1 ? 'active' : ''}`}
                onClick={() => setActiveTab(idx + 1)}
              >
                {tab}
              </div>
            ))}
          </div>
          <div style={{ padding: '2rem' }}>
            {activeTab === 1 && <TabCreateExam />}
            {activeTab === 2 && <TabAddQuestions />}
            {activeTab === 3 && <TabActivationCodes />}
            {activeTab === 4 && <TabMonitorRisk />}
          </div>
        </div>
      </div>
    </div>
  );
}

// ================= TAB 1: CREATE EXAM =================
function TabCreateExam() {
  const [examId, setExamId] = useState('');
  const [title, setTitle] = useState('');
  const [duration, setDuration] = useState('');
  const [status, setStatus] = useState({ type: '', msg: '' });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setStatus({ type: '', msg: '' });
    try {
      await createExam(examId, title, duration);
      setStatus({ type: 'success', msg: `Exam ${examId} created successfully!` });
      setExamId(''); setTitle(''); setDuration('');
    } catch (err) {
      setStatus({ type: 'error', msg: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 className="card-title">Create New Exam</h2>
      {status.msg && (
        <div className={`alert alert-${status.type}`}>
          {status.type === 'success' ? '✅' : '⚠️'} {status.msg}
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Exam ID (Unique)</label>
          <input type="text" value={examId} onChange={e => setExamId(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Exam Title</label>
          <input type="text" value={title} onChange={e => setTitle(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Duration (Minutes)</label>
          <input type="number" min="1" value={duration} onChange={e => setDuration(e.target.value)} required />
        </div>
        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? <><span className="spinner"></span> Creating...</> : 'Create Exam'}
        </button>
      </form>
    </div>
  );
}

// ================= TAB 2: ADD QUESTIONS =================
function TabAddQuestions() {
  const [examId, setExamId] = useState('');
  const [questions, setQuestions] = useState([{ question_text: '', marks: 1 }]);
  const [status, setStatus] = useState({ type: '', msg: '' });
  const [isLoading, setIsLoading] = useState(false);

  const addQ = () => setQuestions([...questions, { question_text: '', marks: 1 }]);
  const removeQ = (idx) => setQuestions(questions.filter((_, i) => i !== idx));
  const updateQ = (idx, field, val) => {
    const newQ = [...questions];
    newQ[idx][field] = val;
    setQuestions(newQ);
  };

  const handleSaveAndRelease = async () => {
    if (!examId) return setStatus({ type: 'error', msg: 'Exam ID is required' });
    if (questions.some(q => !q.question_text)) return setStatus({ type: 'error', msg: 'All questions must have text' });
    
    setIsLoading(true);
    setStatus({ type: '', msg: '' });
    try {
      await addQuestions(examId, questions);
      await releaseQuestions(examId);
      setStatus({ type: 'success', msg: `${questions.length} questions added and released!` });
      setQuestions([{ question_text: '', marks: 1 }]);
    } catch (err) {
      setStatus({ type: 'error', msg: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 className="card-title">Add & Release Questions</h2>
      {status.msg && (
        <div className={`alert alert-${status.type}`}>
          {status.type === 'success' ? '✅' : '⚠️'} {status.msg}
        </div>
      )}
      
      <div className="form-group" style={{ maxWidth: '400px' }}>
        <label>Target Exam ID</label>
        <input type="text" value={examId} onChange={e => setExamId(e.target.value)} />
      </div>

      {questions.map((q, idx) => (
        <div key={idx} style={{ background: '#f9fafb', padding: '1.5rem', borderRadius: '8px', marginBottom: '1rem', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <strong>Question {idx + 1}</strong>
            {questions.length > 1 && (
              <button className="btn btn-outline" style={{ padding: '0.25rem 0.75rem', borderColor: 'var(--danger)', color: 'var(--danger)' }} onClick={() => removeQ(idx)}>Remove</button>
            )}
          </div>
          <div className="form-group">
            <textarea rows="3" placeholder="Enter question text..." value={q.question_text} onChange={e => updateQ(idx, 'question_text', e.target.value)}></textarea>
          </div>
          <div className="form-group" style={{ maxWidth: '150px' }}>
            <label>Marks</label>
            <input type="number" min="1" value={q.marks} onChange={e => updateQ(idx, 'marks', parseInt(e.target.value) || 1)} />
          </div>
        </div>
      ))}

      <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        <button className="btn btn-outline" onClick={addQ}>+ Add Another Question</button>
        <button className="btn btn-primary" onClick={handleSaveAndRelease} disabled={isLoading}>
          {isLoading ? <><span className="spinner"></span> Saving...</> : 'Save & Release All'}
        </button>
      </div>
    </div>
  );
}

// ================= TAB 3: ACTIVATION CODES =================
function TabActivationCodes() {
  const [examId, setExamId] = useState('');
  const [codes, setCodes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!examId) return setError('Exam ID is required');
    setError('');
    setIsLoading(true);
    try {
      const res = await generateCode(examId);
      setCodes([res.data, ...codes]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Code copied to clipboard!');
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 className="card-title">Generate Activation Codes</h2>
      <p style={{ color: 'var(--text-light)', marginBottom: '1.5rem' }}>
        Generate secure, one-time use codes for students to enter the exam. Codes expire in 10 minutes.
      </p>

      {error && <div className="alert alert-error">⚠️ {error}</div>}

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <input style={{ flex: 1 }} type="text" placeholder="Exam ID" value={examId} onChange={e => setExamId(e.target.value)} />
        <button className="btn btn-primary" onClick={handleGenerate} disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Generate Code'}
        </button>
      </div>

      {codes.map((c, i) => (
        <div key={i} className="card" style={{ marginBottom: '1rem', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-light)', fontSize: '0.875rem' }}>Valid for {c.exam_id}</p>
          <div className="code-display">
            {c.code}
          </div>
          <button className="btn btn-outline" onClick={() => copyToClipboard(c.code)}>Copy to Clipboard</button>
          <p style={{ color: 'var(--danger)', fontSize: '0.875rem', marginTop: '1rem' }}>
            Expires at: {new Date(c.expires_at).toLocaleTimeString()}
          </p>
        </div>
      ))}
    </div>
  );
}

// ================= TAB 4: MONITOR & RISK =================
function TabMonitorRisk() {
  const [examId, setExamId] = useState('');
  const [statusData, setStatusData] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    if (!examId) return setError('Exam ID required');
    setError('');
    setIsLoading(true);
    try {
      const [sRes, rRes] = await Promise.all([
        getExamStatus(examId).catch(() => ({ data: {} })), // Ignore if doesn't exist
        getRiskDashboard(examId)
      ]);
      setStatusData(sRes.data);
      setRiskData(rRes.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getBadgeClass = (level) => {
    if (level === 'HIGH') return 'badge-high';
    if (level === 'MEDIUM') return 'badge-medium';
    return 'badge-low';
  };

  // Sort risk data by score descending
  const sortedStudents = riskData?.students ? [...riskData.students].sort((a, b) => b.risk_score - a.risk_score) : [];

  return (
    <div>
      <h2 className="card-title">Live Monitoring & Risk Dashboard</h2>
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', maxWidth: '500px' }}>
        <input style={{ flex: 1 }} type="text" placeholder="Exam ID" value={examId} onChange={e => setExamId(e.target.value)} />
        <button className="btn btn-primary" onClick={loadData} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Load Dashboard'}
        </button>
      </div>

      {error && <div className="alert alert-error">⚠️ {error}</div>}

      {statusData && riskData && (
        <>
          <div className="grid-2" style={{ marginBottom: '2rem' }}>
            <div className="card" style={{ background: 'linear-gradient(135deg, #f8fafc, #f1f5f9)' }}>
              <h3 style={{ marginBottom: '1rem' }}>Exam Status</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Total Candidates:</span> <strong>{statusData.total_candidates || 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Active Now:</span> <strong style={{ color: 'var(--success)' }}>{statusData.active || 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Submitted:</span> <strong>{statusData.submitted || 0}</strong>
              </div>
            </div>

            <div className="card" style={{ background: 'linear-gradient(135deg, #f8fafc, #f1f5f9)' }}>
              <h3 style={{ marginBottom: '1rem' }}>Risk Summary</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>High Risk:</span> <span className="badge badge-high">{riskData.summary?.high || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span>Medium Risk:</span> <span className="badge badge-medium">{riskData.summary?.medium || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Low Risk:</span> <span className="badge badge-low">{riskData.summary?.low || 0}</span>
              </div>
            </div>
          </div>

          <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Risk Level</th>
                  <th>Score %</th>
                  <th>Tab Switches</th>
                  <th>Sim. Score</th>
                  <th>Idle Time</th>
                </tr>
              </thead>
              <tbody>
                {sortedStudents.map((s, i) => (
                  <tr key={i} className={s.risk_level === 'HIGH' ? 'highlight' : ''}>
                    <td><strong>{s.user_id}</strong></td>
                    <td><span className={`badge ${getBadgeClass(s.risk_level)}`}>{s.risk_level}</span></td>
                    <td><strong style={{ color: s.risk_score > 70 ? 'var(--danger)' : 'inherit' }}>{s.risk_score.toFixed(1)}%</strong></td>
                    <td>{s.factors?.tab_switches || 0}</td>
                    <td>{s.factors?.similarity_score ? (s.factors.similarity_score * 100).toFixed(1) + '%' : 'N/A'}</td>
                    <td>{s.factors?.idle_time_seconds || 0}s</td>
                  </tr>
                ))}
                {sortedStudents.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-light)' }}>No student risk data available yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}