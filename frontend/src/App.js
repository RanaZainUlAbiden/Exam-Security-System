import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import ExamPage from './pages/ExamPage';

function PrivateRoute({ children, role }) {
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('role');
  if (!token) return <Navigate to="/" />;
  if (role && userRole !== role) return <Navigate to="/" />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/student" element={
          <PrivateRoute role="student"><StudentDashboard /></PrivateRoute>
        }/>
        <Route path="/teacher" element={
          <PrivateRoute role="teacher"><TeacherDashboard /></PrivateRoute>
        }/>
        <Route path="/exam/:examId" element={
          <PrivateRoute role="student"><ExamPage /></PrivateRoute>
        }/>
      </Routes>
    </BrowserRouter>
  );
}