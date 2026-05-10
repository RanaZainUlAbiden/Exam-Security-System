import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { startTimer, getTimeRemaining, getRandomQuestions, submitExam, logTabSwitch, logClipboard, logActivity } from '../api';

export default function ExamPage() {
  const { examId } = useParams();
  const nav        = useNavigate();
  const [questions, setQuestions]   = useState([]);
  const [answers, setAnswers]       = useState({});
  const [remaining, setRemaining]   = useState(null);
  const [loading, setLoading]       = useState(true);
  const [submitted, setSubmitted]   = useState(false);
  const [msg, setMsg]               = useState({ type:'', text:'' });
  const timerRef = useRef(null);

  const fmt = (s) => `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;

  // Start timer + load questions
  useEffect(() => {
    const init = async () => {
      const [timerRes, qRes] = await Promise.all([
        startTimer(examId),
        getRandomQuestions(examId)
      ]);
      if (timerRes.status === 'success') setRemaining(timerRes.data.remaining_seconds);
      if (qRes.status === 'success') setQuestions(qRes.data.questions || []);
      setLoading(false);
      logActivity(examId, 'exam_started');
    };
    init();
  }, [examId]);

  // Countdown timer
  useEffect(() => {
    if (remaining === null || submitted) return;
    timerRef.current = setInterval(async () => {
      const res = await getTimeRemaining(examId);
      if (res.status === 'success') {
        const secs = res.data.remaining_seconds;
        setRemaining(secs);
        if (secs === 0) {
          clearInterval(timerRef.current);
          setMsg({ type:'warning', text:'⏰ Time expired! Auto-submitting...' });
          handleSubmit(true);
        }
      }
    }, 5000); // poll every 5 seconds
    return () => clearInterval(timerRef.current);
  }, [remaining, submitted]);

  // Tab switch monitoring
  useEffect(() => {
    const onHide = () => { logTabSwitch(examId, 'tab_hidden'); };
    const onShow = () => { logTabSwitch(examId, 'tab_visible'); };
    document.addEventListener('visibilitychange', () => {
      document.hidden ? onHide() : onShow();
    });
    return () => document.removeEventListener('visibilitychange', ()=>{});
  }, [examId]);

  // Clipboard monitoring
  useEffect(() => {
    const onCopy  = () => logClipboard(examId, 'copy');
    const onPaste = () => logClipboard(examId, 'paste');
    const onCut   = () => logClipboard(examId, 'cut');
    document.addEventListener('copy',  onCopy);
    document.addEventListener('paste', onPaste);
    document.addEventListener('cut',   onCut);
    return () => {
      document.removeEventListener('copy',  onCopy);
      document.removeEventListener('paste', onPaste);
      document.removeEventListener('cut',   onCut);
    };
  }, [examId]);

  // Right-click block
  useEffect(() => {
    const block = (e) => { e.preventDefault(); logActivity(examId, 'right_click_attempt'); };
    document.addEventListener('contextmenu', block);
    return () => document.removeEventListener('contextmenu', block);
  }, [examId]);

  const handleSubmit = async (auto = false) => {
    if (submitted) return;
    clearInterval(timerRef.current);
    setSubmitted(true);
    const answerList = Object.entries(answers).map(([question_id, answer_text]) => ({ question_id, answer_text }));
    const res = await submitExam(examId, answerList);
    if (res.status === 'success') {
      setMsg({ type:'success', text: auto ? '⏰ Time up — exam auto-submitted!' : '✅ Exam submitted successfully!' });
    } else {
      setMsg({ type:'error', text: res.message || 'Submission failed' });
    }
  };

  const timerClass = remaining !== null
    ? remaining < 60 ? 'timer-box danger' : remaining < 300 ? 'timer-box warning' : 'timer-box'
    : 'timer-box';

  if (loading) return (
    <div className="loading">
      <div className="spinner"></div>
      <p>Loading exam...</p>
    </div>
  );

  if (submitted) return (
    <div className="login-page">
      <div className="login-box" style={{textAlign:'center'}}>
        <div style={{fontSize:'4rem', marginBottom:'16px'}}>✅</div>
        <h2 style={{color:'#2e8b57', marginBottom:'8px'}}>Exam Submitted!</h2>
        <p style={{color:'#666', marginBottom:'24px'}}>Your answers have been saved securely.</p>
        {msg.text && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
        <button className="btn btn-primary" onClick={() => nav('/student')}>Back to Dashboard</button>
      </div>
    </div>
  );

  return (
    <div className="page">
      <nav className="navbar">
        <h2>🔐 Exam: {examId}</h2>
        <div className="nav-right">
          <span>{questions.length} Questions</span>
        </div>
      </nav>

      <div className="container">
        <div className="grid-2" style={{marginBottom:'24px', alignItems:'start'}}>
          <div className={timerClass}>
            <div className="timer-time">{remaining !== null ? fmt(remaining) : '--:--'}</div>
            <div className="timer-label">Time Remaining</div>
          </div>
          <div className="card">
            {msg.text && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
            <p style={{fontSize:'0.85rem', color:'#666', marginBottom:'12px'}}>
              ⚠️ This exam is monitored. Tab switches, copy/paste, and right-clicks are logged.
            </p>
            <p style={{fontSize:'0.85rem', color:'#666', marginBottom:'16px'}}>
              Answered: <b>{Object.keys(answers).length}</b> / {questions.length}
            </p>
            <button className="btn btn-primary btn-full" onClick={() => handleSubmit(false)}
              disabled={submitted}>
              📤 Submit Exam
            </button>
          </div>
        </div>

        {questions.map((q, i) => (
          <div key={q.question_id} className="question-card">
            <div className="question-num">Question {i+1} — {q.marks} mark{q.marks>1?'s':''}</div>
            <div className="question-text">{q.question_text}</div>
            <textarea className="answer-textarea"
              placeholder="Write your answer here..."
              value={answers[q.question_id] || ''}
              onChange={e => setAnswers(a => ({...a, [q.question_id]: e.target.value}))}
            />
          </div>
        ))}

        <div style={{textAlign:'center', marginTop:'20px'}}>
          <button className="btn btn-primary" style={{padding:'14px 40px', fontSize:'1rem'}}
            onClick={() => handleSubmit(false)} disabled={submitted}>
            📤 Submit All Answers
          </button>
        </div>
      </div>
    </div>
  );
}