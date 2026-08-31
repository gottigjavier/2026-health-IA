import { refreshAccessToken, logout } from './api';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

const getToken = () => localStorage.getItem('access_token');
const getRefreshToken = () => localStorage.getItem('refresh_token');

const REFRESHABLE_CLOSE_CODES = new Set([4401, 4402]);
const MAX_RETRIES = 5;
const BASE_DELAY = 1000;
const MAX_DELAY = 30000;

let inFlightRefresh = null;

// Returns a fresh access token. If `forceRefresh` is true (or there is no valid
// access token), it performs a refresh using the stored refresh token. Multiple
// callers (e.g. parallel WS reconnections) share the same in-flight refresh.
const ensureFreshToken = async ({ forceRefresh = false } = {}) => {
  const access = getToken();
  if (!forceRefresh && access) {
    return access;
  }

  if (!getRefreshToken()) {
    return access;
  }

  if (!inFlightRefresh) {
    inFlightRefresh = refreshAccessToken().finally(() => {
      inFlightRefresh = null;
    });
  }

  let newToken;
  try {
    newToken = await inFlightRefresh;
  } catch (e) {
    // refreshAccessToken already cleared tokens when it fails; mirror the
    // authFetch behavior and bounce the user to /login.
    logout();
    window.location.href = '/login';
    throw e;
  }
  return newToken;
};

export const getWsUrl = (path, token) => {
  if (token) {
    return `${WS_URL}${path}?token=${token}`;
  }
  return `${WS_URL}${path}`;
};

const getBackoffDelay = (attempt) => {
  const delay = BASE_DELAY * (2 ** attempt);
  return Math.min(delay, MAX_DELAY);
};

export const createReconnectingSocket = ({ path, onMessage, onOpen, onClose, logLabel }) => {
  let ws = null;
  let disposed = false;
  let retries = 0;
  let reconnectTimer = null;

  const open = async ({ forceRefresh = false } = {}) => {
    if (disposed) return;

    let token = null;
    try {
      token = await ensureFreshToken({ forceRefresh });
    } catch (e) {
      // Logout already handled inside ensureFreshToken.
      return;
    }

    if (disposed) return;

    ws = new WebSocket(getWsUrl(path, token));

    ws.onopen = () => {
      if (disposed) return;
      retries = 0;
      if (onOpen) onOpen();
    };

    ws.onmessage = (e) => {
      if (disposed) return;
      if (onMessage) onMessage(e);
    };

    ws.onerror = (e) => {
      console.debug(`${logLabel} WS error:`, e);
    };

    ws.onclose = (e) => {
      if (onClose) onClose(e);
      if (disposed) {
        ws = null;
        return;
      }

      const shouldRefresh = REFRESHABLE_CLOSE_CODES.has(e.code);

      if (retries >= MAX_RETRIES) {
        console.warn(`${logLabel} WS closed (${e.code}), max retries reached`, e.reason);
        ws = null;
        return;
      }

      const delay = getBackoffDelay(retries);
      retries += 1;

      console.debug(`${logLabel} WS closed (${e.code}), reconnecting in ${delay}ms`, e.reason);
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        open({ forceRefresh: shouldRefresh });
      }, delay);
    };
  };

  const close = () => {
    disposed = true;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close();
    }
    ws = null;
  };

  open();

  return {
    close,
    isConnected: () => !!(ws && ws.readyState === WebSocket.OPEN),
  };
};

export const getWsUrlWithCurrentToken = (path) => getWsUrl(path, getToken());

export const appManager = ({ handleApp }) =>
  createReconnectingSocket({
    path: '/ws/appData/',
    logLabel: 'App',
    onOpen: () => console.debug('App connected'),
    onMessage: (e) => {
      const msg = JSON.parse(e.data);
      console.debug('WS app message received', {
        beds: msg.beds ? msg.beds.length : undefined,
        calls: msg.calls ? msg.calls.length : undefined,
        tasks: msg.tasks ? msg.tasks.length : undefined,
      });
      handleApp(msg);
    },
    onClose: (e) => console.debug('App closed:', e.code, e.reason),
  });

export const callManager = ({ handleCall }) =>
  createReconnectingSocket({
    path: '/ws/callData/',
    logLabel: 'Calls',
    onOpen: () => console.debug('Calls connected'),
    onMessage: (e) => {
      const msg = JSON.parse(e.data);
      console.debug('WS call message received', {
        type: msg && msg.state !== undefined ? (msg.state ? 'new' : 'answered') : 'unknown',
        hasCall: !!msg.call,
      });
      handleCall(msg);
    },
    onClose: (e) => console.debug('Calls closed:', e.code, e.reason),
  });

export const taskManager = ({ handleTasks }) =>
  createReconnectingSocket({
    path: '/ws/taskData/',
    logLabel: 'Tasks',
    onOpen: () => console.debug('Tasks connected'),
    onMessage: (e) => {
      const msg = JSON.parse(e.data);
      console.debug('WS task message received', { tasks: msg.tasks ? msg.tasks.length : undefined });
      handleTasks(msg);
    },
    onClose: (e) => console.debug('Tasks closed:', e.code, e.reason),
  });
