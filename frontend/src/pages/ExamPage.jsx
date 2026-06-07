import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  startTimer, 
  getTimeRemaining, 
  getRandomQuestions, 
  submitExam,
  logTabSwitch,
  logClipboard,
  logActivity
} from '../api';

export default function ExamPage() {
  const { id: examId } = useParams();
  const navigate = useNavigate();
  
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [timeStr, setTimeStr] = useState('--:--');
  const [secondsLeft, setSecondsLeft] = useState(9999);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const timerInterval = useRef(null);
  const isFinished = useRef(false);
  const answersRef = useRef(answers);

  useEffect(() => {
    answersRef.current = answers;
  }, [answers]);

  // Handle Form state
  const handleAnswerChange = (qId, text) => {
    setAnswers(prev => ({ ...prev, [qId]: text }));
  };

  const executeSubmit = useCallback(async () => {
    isFinished.current = true; // Stop monitoring
    if (timerInterval.current) clearInterval(timerInterval.current);

    setIsSubmitting(true);
    try {
      const formattedAnswers = Object.entries(answersRef.current).map(([q_id, text]) => ({ question_id: q_id, answer_text: text }));
      await submitExam(examId, formattedAnswers);
      setIsSubmitted(true);
    } catch (err) {
      setError(err.message);
      isFinished.current = false; // Re-enable if failed
    } finally {
      setIsSubmitting(false);
    }
  }, [examId]);

  const handleAutoSubmit = useCallback(() => {
    if (!isFinished.current) {
      alert("Time is up! Your exam is being automatically submitted.");
      executeSubmit();
    }
  }, [executeSubmit]);

  const handleManualSubmit = () => {
    if (window.confirm("Are you sure you want to submit your exam? You cannot undo this action.")) {
      executeSubmit();
    }
  };

  // Initialize Exam & Setup Monitoring
  useEffect(() => {
    let mounted = true;

    const initExam = async () => {
      try {
        await startTimer(examId);
        const qRes = await getRandomQuestions(examId);
        if (mounted) setQuestions(qRes.data.questions || []);
      } catch (err) {
        if (mounted) setError(err.message);
      }
    };

    initExam();

    // Setup Monitoring
    const handleVisibility = () => {
      if (isFinished.current) return;
      const event = document.hidden ? 'tab_hidden' : 'tab_visible';
      logTabSwitch(examId, event).catch(console.error);
    };

    const handleCopy = () => !isFinished.current && logClipboard(examId, 'copy').catch(console.error);
    const handlePaste = () => !isFinished.current && logClipboard(examId, 'paste').catch(console.error);
    const handleCut = () => !isFinished.current && logClipboard(examId, 'cut').catch(console.error);

    const handleContext = (e) => {
      if (isFinished.current) return;
      e.preventDefault();
      logActivity(examId, 'right_click_attempt').catch(console.error);
    };

    const handleBeforeUnload = (e) => {
      if (!isFinished.current) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    document.addEventListener('visibilitychange', handleVisibility);
    document.addEventListener('copy', handleCopy);
    document.addEventListener('paste', handlePaste);
    document.addEventListener('cut', handleCut);
    document.addEventListener('contextmenu', handleContext);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      mounted = false;
      document.removeEventListener('visibilitychange', handleVisibility);
      document.removeEventListener('copy', handleCopy);
      document.removeEventListener('paste', handlePaste);
      document.removeEventListener('cut', handleCut);
      document.removeEventListener('contextmenu', handleContext);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [examId]);

  // Timer Polling
  useEffect(() => {
    const pollTime = async () => {
      if (isFinished.current) return;
      try {
        const res = await getTimeRemaining(examId);
        const { remaining_seconds, remaining_display } = res.data;
        setSecondsLeft(remaining_seconds);
        setTimeStr(remaining_display);

        if (remaining_seconds <= 0) {
          handleAutoSubmit();
        }
      } catch (err) {
        console.error('Timer sync error:', err.message);
      }
    };

    // Poll immediately, then every 5 seconds
    pollTime();
    timerInterval.current = setInterval(pollTime, 5000);

    return () => {
      if (timerInterval.current) clearInterval(timerInterval.current);
    };
  }, [examId, handleAutoSubmit]);

  // Timer Color Logic
  let timerClass = 'timer-green';
  if (secondsLeft <= 60) {
    timerClass = 'timer-red';
  } else if (secondsLeft <= 300) {
    timerClass = 'timer-orange';
  }

  if (isSubmitted) {
    return (
      <div className="login-wrapper">
        <div className="card" style={{ textAlign: 'center', maxWidth: '500px' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
          <h2 className="card-title">Exam Submitted Successfully</h2>
          <p style={{ color: 'var(--text-light)', marginBottom: '2rem' }}>
            Your answers have been recorded securely. You may now close this window or return to the dashboard.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/student')}>Return to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ paddingBottom: '100px' }}>
      {/* Warning Banner */}
      <div style={{ background: '#1f2937', color: '#fca5a5', padding: '0.75rem', textAlign: 'center', fontWeight: '500', fontSize: '0.875rem' }}>
        ⚠️ THIS EXAM IS MONITORED. Tab switches, copy/paste, and right-clicks are strictly logged and flagged.
      </div>

      <div className="container" style={{ maxWidth: '800px' }}>
        {error && <div className="alert alert-error">⚠️ {error}</div>}

        <div className={`timer-card ${timerClass}`}>
          ⏱️ {timeStr}
        </div>

        {questions.length === 0 && !error && (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <span className="spinner" style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent', width: '2rem', height: '2rem' }}></span>
            <p style={{ marginTop: '1rem', color: 'var(--text-light)' }}>Loading questions...</p>
          </div>
        )}

        {questions.map((q, idx) => (
          <div key={q.question_id} className="card question-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <strong style={{ fontSize: '1.125rem' }}>Question {idx + 1}</strong>
              <span className="badge badge-low">{q.marks} Marks</span>
            </div>
            <p style={{ fontSize: '1.125rem', marginBottom: '1.5rem', whiteSpace: 'pre-wrap' }}>
              {q.question_text}
            </p>
            
            <textarea 
              rows="6" 
              placeholder="Type your answer here..."
              value={answers[q.question_id] || ''}
              onChange={(e) => handleAnswerChange(q.question_id, e.target.value)}
              onPaste={(e) => { e.preventDefault(); alert("Pasting is disabled."); }}
              onCopy={(e) => { e.preventDefault(); alert("Copying is disabled."); }}
              onCut={(e) => { e.preventDefault(); alert("Cutting is disabled."); }}
            ></textarea>
            
            <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-light)', marginTop: '0.5rem' }}>
              {(answers[q.question_id] || '').length} characters
            </div>
          </div>
        ))}
      </div>

      {/* Sticky Bottom Bar */}
      <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: 'var(--white)', padding: '1rem', boxShadow: '0 -4px 6px -1px rgba(0, 0, 0, 0.1)', textAlign: 'center', zIndex: 50 }}>
        <button className="btn btn-primary" style={{ padding: '1rem 3rem', fontSize: '1.125rem' }} onClick={handleManualSubmit} disabled={isSubmitting || questions.length === 0}>
          {isSubmitting ? <><span className="spinner"></span> Submitting...</> : 'Submit Exam'}
        </button>
      </div>
    </div>
  );
}
