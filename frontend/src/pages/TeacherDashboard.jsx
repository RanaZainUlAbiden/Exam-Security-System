import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createExam, addQuestions, releaseQuestions, generateCode, getExamStatus, getRiskDashboard } from '../api';

export default function TeacherDashboard() {
  const nav      = useNavigate();
  const username = localStorage.getItem('username');
  const [activeTab, setActiveTab] = useState('create');
  const [loading, setLoading]     = useState(false);
  const [msg, setMsg]             = useState({ type:'', text:'' });

  // Create Exam State
  const [examForm, setExamForm] = useState({ exam_id:'', title:'', duration:60 });
  const [examCreated, setExamCreated] = useState(false);

  // Add Questions State
  const [qExamId, setQExamId]   = useState('');
  const [questions, setQuestions] = useState([{ question_text:'', marks:1 }]);

  // Activation Code State
  const [codeExamId, setCodeExamId] = useState('');
  const [generatedCode, setGeneratedCode] = useState(null);

  // Monitor State
  const [monExamId, setMonExamId]   = useState('');
  const [monitorData, setMonitorData] = useState(null);
  const [riskData, setRiskData]     = useState(null);

  const logout = () => { localStorage.clear(); nav('/'); };
  const setE = (k,v) => setExamForm(f=>({...f,[k]:v}));

  const handleCreateExam = async () => {
    if (!examForm.exam_id || !examForm.title) return setMsg({type:'error',text:'Fill all fields'});
    setLoading(true); setMsg({type:'',text:''});
    const res = await createExam(examForm.exam_id, examForm.title, parseInt(examForm.duration));
    setLoading(false);
    if (res.status === 'success') {
      setExamCreated(true);
      setMsg({type:'success', text:`Exam "${examForm.title}" created!`});
    } else {
      setMsg({type:'error', text: res.message});
    }
  };

  const addQRow = () => setQuestions(q => [...q, {question_text:'', marks:1}]);
  const setQ = (i,k,v) => setQuestions(q => q.map((item,idx) => idx===i ? {...item,[k]:v} : item));

  const handleAddQuestions = async () => {
    if (!qExamId) return setMsg({type:'error',text:'Enter Exam ID'});
    const valid = questions.filter(q => q.question_text.trim());
    if (!valid.length) return setMsg({type:'error',text:'Add at least 1 question'});
    setLoading(true); setMsg({type:'',text:''});
    const r1 = await addQuestions(qExamId, valid);
    if (r1.status === 'success') {
      const r2 = await releaseQuestions(qExamId);
      setMsg({type:'success', text:`${valid.length} questions added & released!`});
    } else {
      setMsg({type:'error', text: r1.message});
    }
    setLoading(false);
  };

  const handleGenCode = async () => {
    if (!codeExamId) return setMsg({type:'error',text:'Enter Exam ID'});
    setLoading(true); setMsg({type:'',text:''});
    const res = await generateCode(codeExamId);
    setLoading(false);
    if (res.status === 'success') {
      setGeneratedCode(res.data);
      setMsg({type:'success', text:'Activation code generated!'});
    } else {
      setMsg({type:'error', text: res.message});
    }
  };

  const handleMonitor = async () => {
    if (!monExamId) return setMsg({type:'error',text:'Enter Exam ID'});
    setLoading(true); setMsg({type:'',text:''});
    const [status, risk] = await Promise.all([
      getExamStatus(monExamId),
      getRiskDashboard(monExamId)
    ]);
    setLoading(false);
    if (status.status === 'success') setMonitorData(status.data);
    if (risk.status === 'success') setRiskData(risk.data);
  };

  const tabs = [
    { id:'create',   label:'📝 Create Exam' },
    { id:'questions',label:'❓ Add Questions' },
    { id:'codes',    label:'🔑 Activation Codes' },
    { id:'monitor',  label:'📊 Monitor' },
  ];

  return (
    <div className="page">
      <nav className="navbar">
        <h2>🔐 SecureExam — Teacher Portal</h2>
        <div className="nav-right">
          <span>👨‍🏫 {username}</span>
          <button className="btn-logout" onClick={logout}>Logout</button>
        </div>
      </nav>

      <div className="container">
        {/* Tab Nav */}
        <div style={{display:'flex', gap:'10px', marginBottom:'24px', flexWrap:'wrap'}}>
          {tabs.map(t => (
            <button key={t.id} className={`btn ${activeTab===t.id?'btn-primary':'btn-outline'}`}
              onClick={()=>{setActiveTab(t.id); setMsg({type:'',text:''});}}>
              {t.label}
            </button>
          ))}
        </div>

        {msg.text && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {/* CREATE EXAM */}
        {activeTab === 'create' && (
          <div className="card" style={{maxWidth:'550px'}}>
            <p className="section-title">Create New Exam</p>
            <div className="form-group"><label>Exam ID</label>
              <input value={examForm.exam_id} onChange={e=>setE('exam_id',e.target.value)} placeholder="e.g. exam001" />
            </div>
            <div className="form-group"><label>Exam Title</label>
              <input value={examForm.title} onChange={e=>setE('title',e.target.value)} placeholder="e.g. Mid Term CS101" />
            </div>
            <div className="form-group"><label>Duration (minutes)</label>
              <input type="number" value={examForm.duration} onChange={e=>setE('duration',e.target.value)} min={5} max={300} />
            </div>
            <button className="btn btn-primary" onClick={handleCreateExam} disabled={loading}>
              {loading ? 'Creating...' : 'Create Exam'}
            </button>
          </div>
        )}

        {/* ADD QUESTIONS */}
        {activeTab === 'questions' && (
          <div className="card">
            <p className="section-title">Add Questions</p>
            <div className="form-group" style={{maxWidth:'300px'}}>
              <label>Exam ID</label>
              <input value={qExamId} onChange={e=>setQExamId(e.target.value)} placeholder="e.g. exam001" />
            </div>
            {questions.map((q, i) => (
              <div key={i} className="question-card">
                <div className="question-num">Question {i+1}</div>
                <div className="form-group">
                  <label>Question Text</label>
                  <textarea className="answer-textarea" value={q.question_text}
                    onChange={e=>setQ(i,'question_text',e.target.value)}
                    placeholder="Enter question..." />
                </div>
                <div className="form-group" style={{width:'100px'}}>
                  <label>Marks</label>
                  <input type="number" value={q.marks} onChange={e=>setQ(i,'marks',parseInt(e.target.value))} min={1} />
                </div>
              </div>
            ))}
            <div style={{display:'flex', gap:'10px'}}>
              <button className="btn btn-outline" onClick={addQRow}>+ Add Question</button>
              <button className="btn btn-primary" onClick={handleAddQuestions} disabled={loading}>
                {loading ? 'Saving...' : '💾 Save & Release'}
              </button>
            </div>
          </div>
        )}

        {/* ACTIVATION CODES */}
        {activeTab === 'codes' && (
          <div className="card" style={{maxWidth:'500px'}}>
            <p className="section-title">Generate Activation Code</p>
            <div className="form-group">
              <label>Exam ID</label>
              <input value={codeExamId} onChange={e=>setCodeExamId(e.target.value)} placeholder="e.g. exam001" />
            </div>
            <button className="btn btn-primary" onClick={handleGenCode} disabled={loading}>
              {loading ? 'Generating...' : '🔑 Generate Code'}
            </button>

            {generatedCode && (
              <div className="code-display" style={{marginTop:'20px'}}>
                <div style={{fontSize:'0.85rem', color:'#555', marginBottom:'8px'}}>Share this code with student:</div>
                <div className="code-text">{generatedCode.code}</div>
                <div className="code-expiry">⏱ Expires in {generatedCode.expires_in_minutes} minutes</div>
                <div className="code-expiry">Exam: {generatedCode.exam_id}</div>
              </div>
            )}
          </div>
        )}

        {/* MONITOR */}
        {activeTab === 'monitor' && (
          <div>
            <div style={{display:'flex', gap:'10px', marginBottom:'20px', alignItems:'flex-end'}}>
              <div className="form-group" style={{marginBottom:0, width:'220px'}}>
                <label>Exam ID</label>
                <input value={monExamId} onChange={e=>setMonExamId(e.target.value)} placeholder="e.g. exam001" />
              </div>
              <button className="btn btn-primary" onClick={handleMonitor} disabled={loading}>
                {loading ? 'Loading...' : '🔍 Load Data'}
              </button>
            </div>

            {monitorData && (
              <div className="grid-2" style={{marginBottom:'20px'}}>
                <div className="card">
                  <p className="section-title">📊 Exam Status</p>
                  <div className="grid-3">
                    <div className="stat-card"><div className="stat-number">{monitorData.summary?.total_students||0}</div><div className="stat-label">Total</div></div>
                    <div className="stat-card"><div className="stat-number">{monitorData.summary?.submitted||0}</div><div className="stat-label">Submitted</div></div>
                    <div className="stat-card"><div className="stat-number">{monitorData.summary?.active||0}</div><div className="stat-label">Active</div></div>
                  </div>
                </div>
                {riskData && (
                  <div className="card">
                    <p className="section-title">⚠️ Risk Summary</p>
                    <div className="grid-3">
                      <div className="stat-card"><div className="stat-number" style={{color:'#e74c3c'}}>{riskData.summary?.high||0}</div><div className="stat-label">High Risk</div></div>
                      <div className="stat-card"><div className="stat-number" style={{color:'#f39c12'}}>{riskData.summary?.medium||0}</div><div className="stat-label">Medium</div></div>
                      <div className="stat-card"><div className="stat-number" style={{color:'#2e8b57'}}>{riskData.summary?.low||0}</div><div className="stat-label">Low</div></div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {riskData?.students?.length > 0 && (
              <div className="card">
                <p className="section-title">🏆 Risk Scores — All Students</p>
                <table className="table">
                  <thead><tr>
                    <th>Student ID</th><th>Risk Score</th><th>Level</th>
                    <th>Tab Switches</th><th>Similarity</th><th>Idle (s)</th>
                  </tr></thead>
                  <tbody>
                    {riskData.students.map((s,i) => (
                      <tr key={i}>
                        <td>{s.user_id}</td>
                        <td><b>{s.score}%</b></td>
                        <td><span className={`badge badge-${s.level?.toLowerCase()}`}>{s.level}</span></td>
                        <td>{s.breakdown?.tab_switches||0}</td>
                        <td>{s.breakdown?.similarity_score||0}</td>
                        <td>{s.breakdown?.idle_time_sec||0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}