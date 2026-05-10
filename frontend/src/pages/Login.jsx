import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, verifyOtp, register, registerDevice } from '../api';

export default function Login() {
  const nav = useNavigate();
  const [tab, setTab]         = useState('login');   // login | register
  const [step, setStep]       = useState(1);          // 1=creds, 2=otp
  const [form, setForm]       = useState({ username:'', password:'', role:'student' });
  const [userId, setUserId]   = useState('');
  const [otpVal, setOtpVal]   = useState('');
  const [devOtp, setDevOtp]   = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg]         = useState({ type:'', text:'' });

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleLogin = async () => {
    if (!form.username || !form.password) return setMsg({ type:'error', text:'Fill all fields' });
    setLoading(true); setMsg({ type:'', text:'' });
    const res = await login(form.username, form.password);
    setLoading(false);
    if (res.status === 'success') {
      setUserId(res.data.user_id);
      setDevOtp(res.data.otp); // dev only
      setStep(2);
      setMsg({ type:'success', text:'OTP sent! (shown below for dev testing)' });
    } else {
      setMsg({ type:'error', text: res.message || 'Login failed' });
    }
  };

  const handleOtp = async () => {
    if (!otpVal) return setMsg({ type:'error', text:'Enter OTP' });
    setLoading(true);
    const res = await verifyOtp(userId, otpVal);
    setLoading(false);
    if (res.status === 'success') {
      const { token, role, username, user_id } = res.data;
      localStorage.setItem('token', token);
      localStorage.setItem('role', role);
      localStorage.setItem('username', username);
      localStorage.setItem('user_id', user_id);
      await registerDevice();
      nav(role === 'teacher' ? '/teacher' : '/student');
    } else {
      setMsg({ type:'error', text: res.message || 'Invalid OTP' });
    }
  };

  const handleRegister = async () => {
    if (!form.username || !form.password) return setMsg({ type:'error', text:'Fill all fields' });
    setLoading(true);
    const res = await register(form.username, form.password, form.role);
    setLoading(false);
    if (res.status === 'success') {
      setMsg({ type:'success', text:'Registered! Now login.' });
      setTab('login');
    } else {
      setMsg({ type:'error', text: res.message || 'Registration failed' });
    }
  };

  return (
    <div className="login-page">
      <div className="login-box">
        <div className="login-logo">
          <h1>🔐 SecureExam</h1>
          <p>Secure Online Examination System</p>
        </div>

        <div className="login-tabs">
          <button className={`tab-btn ${tab==='login'?'active':''}`} onClick={()=>{setTab('login');setStep(1);setMsg({type:'',text:''})}}>Login</button>
          <button className={`tab-btn ${tab==='register'?'active':''}`} onClick={()=>{setTab('register');setMsg({type:'',text:''})}}>Register</button>
        </div>

        {msg.text && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {tab === 'login' && step === 1 && (
          <>
            <div className="form-group">
              <label>Username</label>
              <input value={form.username} onChange={e=>set('username',e.target.value)} placeholder="Enter username" />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input type="password" value={form.password} onChange={e=>set('password',e.target.value)} placeholder="Enter password" />
            </div>
            <button className="btn btn-primary btn-full" onClick={handleLogin} disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </>
        )}

        {tab === 'login' && step === 2 && (
          <>
            {devOtp && (
              <div className="alert alert-warning">
                <b>Dev Mode OTP:</b> <span style={{letterSpacing:'4px',fontWeight:'700'}}>{devOtp}</span>
              </div>
            )}
            <div className="form-group">
              <label>Enter OTP</label>
              <input className="otp-input" maxLength={6} value={otpVal}
                onChange={e=>setOtpVal(e.target.value)} placeholder="------" />
            </div>
            <button className="btn btn-primary btn-full" onClick={handleOtp} disabled={loading}>
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>
            <button className="btn btn-outline btn-full" style={{marginTop:'10px'}} onClick={()=>setStep(1)}>Back</button>
          </>
        )}

        {tab === 'register' && (
          <>
            <div className="form-group">
              <label>Username</label>
              <input value={form.username} onChange={e=>set('username',e.target.value)} placeholder="Choose username" />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input type="password" value={form.password} onChange={e=>set('password',e.target.value)} placeholder="Choose password" />
            </div>
            <div className="form-group">
              <label>Role</label>
              <select value={form.role} onChange={e=>set('role',e.target.value)}>
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>
            </div>
            <button className="btn btn-primary btn-full" onClick={handleRegister} disabled={loading}>
              {loading ? 'Registering...' : 'Create Account'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}