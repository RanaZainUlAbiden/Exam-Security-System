import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateCode } from '../api';

export default function StudentDashboard() {
  const nav      = useNavigate();
  const username = localStorage.getItem('username');
  const [examId, setExamId]   = useState('');
  const [code, setCode]       = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg]         = useState({ type:'', text:'' });

  const logout = () => { localStorage.clear(); nav('/'); };

  const handleJoinExam = async () => {
    if (!examId || !code) return setMsg({ type:'error', text:'Enter Exam ID and activation code' });
    setLoading(true); setMsg({ type:'', text:'' });
    const res = await validateCode(code.toUpperCase(), examId);
    setLoading(false);
    if (res.status === 'success') {
      setMsg({ type:'success', text:'Code accepted! Redirecting to exam...' });
      setTimeout(() => nav(`/exam/${examId}`), 1200);
    } else {
      setMsg({ type:'error', text: res.message || 'Invalid code' });
    }
  };

  return (
    <div className="page">
      <nav className="navbar">
        <h2>🔐 SecureExam — Student Portal</h2>
        <div className="nav-right">
          <span>👋 {username}</span>
          <button className="btn-logout" onClick={logout}>Logout</button>
        </div>
      </nav>

      <div className="container">
        <div className="grid-3" style={{marginBottom:'24px'}}>
          <div className="stat-card">
            <div className="stat-number">🎓</div>
            <div className="stat-label">Student Account</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">🔒</div>
            <div className="stat-label">Device Bound</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">✅</div>
            <div className="stat-label">Session Active</div>
          </div>
        </div>

        <div className="card" style={{maxWidth:'500px', margin:'0 auto'}}>
          <p className="card-title">Join Exam</p>

          {msg.text && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

          <div className="form-group">
            <label>Exam ID</label>
            <input value={examId} onChange={e=>setExamId(e.target.value)}
              placeholder="e.g. exam001" />
          </div>

          <div className="form-group">
            <label>Activation Code (from teacher)</label>
            <input value={code} onChange={e=>setCode(e.target.value.toUpperCase())}
              placeholder="e.g. A3K9XZ2B" maxLength={8}
              style={{textTransform:'uppercase', letterSpacing:'4px', fontWeight:'700', fontSize:'1.1rem'}} />
          </div>

          <button className="btn btn-primary btn-full" onClick={handleJoinExam} disabled={loading}>
            {loading ? 'Verifying Code...' : '🚀 Start Exam'}
          </button>
        </div>

        <div className="card" style={{maxWidth:'500px', margin:'24px auto 0'}}>
          <p className="card-title">📋 Instructions</p>
          <ul style={{paddingLeft:'20px', lineHeight:'2', color:'#555', fontSize:'0.9rem'}}>
            <li>Get your activation code from teacher before exam</li>
            <li>Do not switch tabs during exam — monitored</li>
            <li>Do not copy/paste — monitored</li>
            <li>Timer runs on server — cannot be manipulated</li>
            <li>Submit before time runs out</li>
          </ul>
        </div>
      </div>
    </div>
  );
}