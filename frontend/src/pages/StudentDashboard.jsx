import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateCode } from '../api';

export default function StudentDashboard() {
  const [examId, setExamId] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const username = localStorage.getItem('username') || 'Student';

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  const handleJoinExam = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await validateCode(code.toUpperCase(), examId);
      // On success, go to exam page
      navigate(`/exam/${examId}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <nav className="navbar">
        <h1>Student Portal</h1>
        <div className="nav-actions">
          <span>Welcome, {username}</span>
          <button className="btn btn-outline" style={{ color: 'white', borderColor: 'white' }} onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="container">
        <div className="grid-2">
          
          <div>
            <div className="card" style={{ marginBottom: '2rem' }}>
              <h2 className="card-title">👋 Welcome Back, {username}!</h2>
              <p style={{ color: 'var(--text-light)' }}>
                Your device has been securely registered with our monitoring system. You are ready to take your exams.
              </p>
            </div>

            <div className="card">
              <h2 className="card-title">📋 Exam Rules & Instructions</h2>
              <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-dark)' }}>
                <li style={{ marginBottom: '0.5rem' }}>Ensure you have a stable internet connection before starting.</li>
                <li style={{ marginBottom: '0.5rem' }}>Do <strong>NOT</strong> switch tabs or minimize the browser during the exam.</li>
                <li style={{ marginBottom: '0.5rem' }}>Copying, pasting, and cutting text is strictly prohibited.</li>
                <li style={{ marginBottom: '0.5rem' }}>Right-clicking is disabled.</li>
                <li style={{ marginBottom: '0.5rem' }}>Your session will automatically submit when the timer hits zero.</li>
                <li style={{ color: 'var(--danger)' }}>Violations of these rules will result in an immediate HIGH risk flag.</li>
              </ul>
            </div>
          </div>

          <div>
            <div className="card" style={{ borderTop: '4px solid var(--primary)' }}>
              <h2 className="card-title">🚀 Join Exam</h2>
              {error && (
                <div className="alert alert-error">
                  <span>⚠️</span> {error}
                </div>
              )}
              
              <form onSubmit={handleJoinExam}>
                <div className="form-group">
                  <label>Exam ID</label>
                  <input 
                    type="text" 
                    value={examId} 
                    onChange={e => setExamId(e.target.value)} 
                    placeholder="e.g., CS101_MID"
                    required 
                  />
                </div>
                
                <div className="form-group">
                  <label>Activation Code</label>
                  <input 
                    type="text" 
                    className="monospace-input"
                    value={code} 
                    onChange={e => setCode(e.target.value.toUpperCase())} 
                    placeholder="XXXX-XXXX"
                    maxLength={10}
                    required 
                  />
                  <small style={{ color: 'var(--text-light)', display: 'block', marginTop: '0.5rem' }}>
                    Ask your teacher for the one-time activation code.
                  </small>
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={isLoading}>
                  {isLoading ? <><span className="spinner"></span> Validating...</> : 'Start Exam'}
                </button>
              </form>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}