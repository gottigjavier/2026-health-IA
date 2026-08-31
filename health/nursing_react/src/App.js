import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import AppContext from './context/appContext';
import HealthApp from './HealthApp';
import Login from './components/Login';
import Register from './components/Register';
import { isAuthenticated, logout, getUser } from './services/api';

function App() {
  const [appState, setAppState] = useState();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      logout();
    }
    setLoading(false);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AppContext.Provider value={[appState, setAppState]}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={!isAuthenticated() ? <Login /> : <Navigate to="/" />} />
          <Route 
            path="/register" 
            element={
              isAuthenticated() && (getUser()?.is_superuser === true || (getUser()?.is_leader === true && getUser()?.role === 'doctor'))
                ? <Register /> 
                : <Navigate to="/" />
            } 
          />
          <Route path="/*" element={isAuthenticated() ? <HealthApp /> : <Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AppContext.Provider>
  );
}

export default App;
