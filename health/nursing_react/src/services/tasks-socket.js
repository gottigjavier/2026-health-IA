//----------- Tasks Section websocket - channel through consumer.py -----------
import { createReconnectingSocket } from './websocket'

export const tasksManager = ({handleTasks}) =>
    createReconnectingSocket({
        path: '/ws/taskData/',
        logLabel: 'Tasks',
        onOpen: () => { console.debug('Tasks connected'); },
        onMessage: e => {
            try {
                const msg = JSON.parse(e.data);
                console.debug('WS tasks message received', { tasks: msg.tasks ? msg.tasks.length : undefined });
                handleTasks(msg);
            } catch (err) {
                console.error('Failed parsing tasks WS message', err, e.data);
            }
        },
        onClose: e => { console.debug('Tasks closed:', e.code, e.reason); },
    });
// -------- End Tasks section websocket - channel -------------------
