const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const getToken = () => localStorage.getItem('access_token');
const getRefreshToken = () => localStorage.getItem('refresh_token');

const setTokens = (access, refresh) => {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};

const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const isAuthenticated = () => !!getToken();

export const getUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const login = async (username, password) => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data = await response.json();
  setTokens(data.access, data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data;
};

export const register = async (username, email, password, isLeader = false, role = "nurse", imageFile = null) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('email', email);
  formData.append('password', password);
  formData.append('is_leader', isLeader);
  formData.append('role', role);
  
  if (imageFile) {
    formData.append('image', imageFile);
  }

  const doRegister = async (token) => {
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers,
      body: formData,
    });
  };

  let token = getToken();
  let response = await doRegister(token);

  if (response.status === 401 && token) {
    try {
      const newToken = await refreshAccessToken();
      token = newToken;
      response = await doRegister(token);
    } catch (e) {
      clearTokens();
      window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!response.ok) {
    let errMsg = 'Registration failed';
    try {
      const error = await response.json();
      errMsg = error.detail || error[0] || error.error || JSON.stringify(error);
    } catch (e) {
      errMsg = `HTTP ${response.status}`;
    }
    throw new Error(errMsg);
  }

  return await response.json();
};

export const logout = () => {
  clearTokens();
};

export const refreshAccessToken = async () => {
  const refresh = getRefreshToken();
  if (!refresh) {
    throw new Error('No refresh token');
  }

  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) {
    clearTokens();
    throw new Error('Token refresh failed');
  }

  const data = await response.json();
  setTokens(data.access, data.refresh);
  return data.access;
};

export const authFetch = async (url, options = {}) => {
  const token = getToken();
  
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_URL}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    try {
      const newToken = await refreshAccessToken();
      headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(`${API_URL}${url}`, {
        ...options,
        headers,
      });
    } catch (error) {
      clearTokens();
      window.location.href = '/login';
      throw error;
    }
  }

  return response;
};

export const fetchApi = async (endpoint, method = 'GET', data = null) => {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  return authFetch(endpoint, options);
};

export const fetchLoad = async () => {
  const response = await authFetch('/app/load');
  if (!response.ok) {
    throw new Error('Failed to load app data');
  }
  return response.json();
};

export const getBeds = async () => {
  const response = await authFetch('/beds');
  if (!response.ok) throw new Error('Failed to fetch beds');
  return response.json();
};

export const getRooms = async () => {
  const response = await authFetch('/rooms');
  if (!response.ok) throw new Error('Failed to fetch rooms');
  return response.json();
};

export const getTasks = async () => {
  const response = await authFetch('/tasks');
  if (!response.ok) throw new Error('Failed to fetch tasks');
  return response.json();
};

export const getCalls = async () => {
  const response = await authFetch('/calls');
  if (!response.ok) throw new Error('Failed to fetch calls');
  return response.json();
};

export const createBed = async (bedData) => {
  const response = await authFetch('/beds', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bedData),
  });
  if (!response.ok) throw new Error('Failed to create bed');
  return response.json();
};

export const updateBed = async (bedId, bedData) => {
  const response = await authFetch(`/beds/${bedId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bedData),
  });
  if (!response.ok) throw new Error('Failed to update bed');
  return response.json();
};

export const vacateBed = async (bedData) => {
  const response = await authFetch('/beds/vacate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bedData),
  });
  if (!response.ok) throw new Error('Failed to vacate bed');
  return response.json();
};

export const createTask = async (taskData) => {
  const response = await authFetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(taskData),
  });
  if (!response.ok) throw new Error('Failed to create task');
  return response.json();
};

export const updateTask = async (taskId, taskData) => {
  const response = await authFetch(`/tasks/${taskId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(taskData),
  });
  if (!response.ok) throw new Error('Failed to update task');
  return response.json();
};

export const completeTask = async (taskId) => {
  const response = await authFetch(`/tasks/${taskId}/complete`, { method: 'POST' });
  if (!response.ok) throw new Error('Failed to complete task');
  return response.json();
};

export const deleteTask = async (taskId) => {
  const response = await authFetch(`/tasks/${taskId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete task');
  return response.json();
};

export const answerCall = async (callId) => {
  const response = await authFetch(`/calls/${callId}/answer`, { method: 'POST' });
  if (!response.ok) throw new Error('Failed to answer call');
  return response.json();
};

export const closeCall = async (callId, responseText) => {
  const response = await authFetch(`/calls/${callId}/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response: responseText }),
  });
  if (!response.ok) throw new Error('Failed to close call');
  return response.json();
};

export const getEvents = async () => {
  const response = await authFetch('/events');
  if (!response.ok) throw new Error('Failed to fetch events');
  return response.json();
};

export const getEvent = async (eventId) => {
  const response = await authFetch(`/events/${eventId}`);
  if (!response.ok) throw new Error('Failed to fetch event');
  return response.json();
};

export default {
  isAuthenticated,
  getUser,
  login,
  register,
  logout,
  authFetch,
  fetchApi,
  fetchLoad,
  getBeds,
  getRooms,
  getTasks,
  getCalls,
  createBed,
  updateBed,
  vacateBed,
  createTask,
  updateTask,
  completeTask,
  deleteTask,
  answerCall,
  closeCall,
  getEvents,
  getEvent,
};
