import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, verifyOtp, register, registerDevice, registerSession } from '../api';

export default function Login() {
  const [activeTab, setActiveTab] = useState('login'); // 'login' or 'register'
  const [step, setStep] = useState(1); // 1 = Creds, 2 = OTP
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Form State
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [userId, setUserId] = useState(null);

  const navigate = useNavigate();

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const res = await login(username, password);
      setUserId(res.data.user_id);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const res = await verifyOtp(userId, otp);
      const { token, role: userRole, username: resUsername, user_id } = res.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('role', userRole);
      localStorage.setItem('username', resUsername);
      localStorage.setItem('user_id', user_id);

      // Register device automatically
      try {
        await registerSession();
        await registerDevice();
      } catch (err) {
        console.warn('Session or device registration failed:', err.message);
      }

      if (userRole === 'teacher') navigate('/teacher');
      else navigate('/student');
      
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);
    try {
      await register(username, password, 'student');
      setSuccess('Registration successful! You can now login.');
      setActiveTab('login');
      setStep(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="card login-card">
        <div className="login-header">
          <div className="login-icon">🔒</div>
          <h2>Secure Portal</h2>
        </div>

        {error && (
          <div className="alert alert-error">
            <span>⚠️</span> {error}
          </div>
        )}
        
        {success && (
          <div className="alert alert-success">
            <span>✅</span> {success}
          </div>
        )}

        {step === 1 ? (
          <>
            <div className="tabs">
              <div 
                className={`tab ${activeTab === 'login' ? 'active' : ''}`}
                onClick={() => { setActiveTab('login'); setError(''); setSuccess(''); }}
              >
                Login
              </div>
              <div 
                className={`tab ${activeTab === 'register' ? 'active' : ''}`}
                onClick={() => { setActiveTab('register'); setError(''); setSuccess(''); }}
              >
                Register
              </div>
            </div>

            {activeTab === 'login' ? (
              <form onSubmit={handleLoginSubmit}>
                <div className="form-group">
                  <label>Username</label>
                  <input 
                    type="text" 
                    value={username} 
                    onChange={e => setUsername(e.target.value)} 
                    required 
                    placeholder="Enter username"
                  />
                </div>
                <div className="form-group">
                  <label>Password</label>
                  <input 
                    type="password" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    required 
                    placeholder="Enter password"
                  />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={isLoading}>
                  {isLoading ? <><span className="spinner"></span> Authenticating...</> : 'Login'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegisterSubmit}>
                <div className="alert alert-warning">
                  Student self-registration only. Teacher accounts are created by an administrator.
                </div>
                <div className="form-group">
                  <label>Username</label>
                  <input 
                    type="text" 
                    value={username} 
                    onChange={e => setUsername(e.target.value)} 
                    required 
                    placeholder="Choose a username"
                  />
                </div>
                <div className="form-group">
                  <label>Password</label>
                  <input 
                    type="password" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    required 
                    placeholder="Choose a strong password"
                  />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={isLoading}>
                  {isLoading ? <><span className="spinner"></span> Registering...</> : 'Create Account'}
                </button>
              </form>
            )}
          </>
        ) : (
          <form onSubmit={handleOtpSubmit}>
            <div className="alert alert-warning">
              <span>💻</span> Check the server terminal for your OTP.
            </div>
            <div className="form-group">
              <label>One-Time Password (OTP)</label>
              <input 
                type="text" 
                className="monospace-input"
                value={otp} 
                onChange={e => setOtp(e.target.value)} 
                required 
                maxLength={6}
                placeholder="------"
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={isLoading}>
              {isLoading ? <><span className="spinner"></span> Verifying...</> : 'Verify & Proceed'}
            </button>
            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <button type="button" className="btn btn-outline" style={{ border: 'none' }} onClick={() => setStep(1)}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
