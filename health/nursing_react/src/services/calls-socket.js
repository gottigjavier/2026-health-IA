//----------- Calls Section websocket - channel through consumer.py ------------
import { createReconnectingSocket } from './websocket'

export const callsManager = ({handleCall}) =>
    createReconnectingSocket({
        path: '/ws/callData/',
        logLabel: 'Calls',
        onOpen: () => { console.debug('Calls connected'); },
        onMessage: e => {
            try {
                const msg = JSON.parse(e.data);
                console.debug('WS calls message received', { hasCall: !!msg.call, state: msg.state });
                handleCall(msg);
            } catch (err) {
                console.error('Failed parsing calls WS message', err, e.data);
            }
        },
        onClose: e => { console.debug('Calls closed:', e.code, e.reason); },
    });
//---------------- End Calls Section websocket ------------------------------
