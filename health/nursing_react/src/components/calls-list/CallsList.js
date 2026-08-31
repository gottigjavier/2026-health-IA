import {useContext, useEffect, useState, useRef} from 'react';
import './calls-list.css';
import Call from './call/Call';
import {callsManager} from '../../services/calls-socket';
import AppContext from '../../context/appContext';




export default function CallsList(props){
    const [appState, setAppState] = useContext(AppContext);
    const appStateRef = useRef(appState);
    const [listCallsLen, setListCallsLen] = useState(appState.calls.length);
    const places = props.places;
    const recentlyProcessedRef = useRef({});

    useEffect(() => {
        appStateRef.current = appState;
    }, [appState]);


    useEffect(() => {
        const socket = callsManager({handleCall})
        return () => { if (socket) socket.close(); }
    }, [])

    useEffect(() => {
        setListCallsLen(appState.calls.length)
    }, [appState.calls.length])

    const handleCall = async msg => {
        if (!msg) return;
        
        if (msg.call === null || msg.call === undefined) {
            return;
        }

        const callsArr = (msg.call && msg.call.calls) ? msg.call.calls : (msg.calls || []);
        const incomingBed = msg.call?.bed || msg.bed;
        const isNewCall = msg.state === true || (msg.call && msg.call.state) === true;

        const currentCalls = appState.calls;
        
        if (isNewCall && incomingBed) {
            const existingCall = currentCalls.find(c => c.bed === incomingBed && c.state === 'active');
            if (existingCall || recentlyProcessedRef.current[incomingBed]) {
                return;
            }
            
            recentlyProcessedRef.current[incomingBed] = true;
            
            setTimeout(() => {
                delete recentlyProcessedRef.current[incomingBed];
            }, 500);
        }

        setAppState(prev => ({ ...prev, calls: callsArr }));
        setListCallsLen(callsArr.length);

        if (!isNewCall) {
            answeredCall(msg);
        }
    }

// ------------------- Answered Call ----------------------------------
    const answeredCall = call =>{
        call.bed = call.bed.split(",")[0];
        const callsList = call.call.calls
        const BEDS = places.numBeds;
        let saveCallsList = [];
        if (callsList.length > 0){
            for (let bed=1; bed<=BEDS; bed++){
                let answCall = `${call.bed},${bed}`
                callsList.map(elem => {
                    if(elem.bed === answCall && elem.state === 'active'){
                        elem.state = 'answered'
                        elem.response_time = new Date()
                        saveCallsList.push(elem)
                    }
                    return null
                })
            }
            saveAnsweredCall(saveCallsList)
            }
        else {
            // No calls to answered — expected state, no logging needed
        }
    }

    const saveAnsweredCall = async (saveCallsList) => {
        if (saveCallsList.length > 0) {
            import('../../services/api').then(({ authFetch, fetchLoad }) => {
                const promises = saveCallsList.map(elem => {
                    // Prefer explicit id if provided
                    const id = elem.id || elem.pk || elem.call_id;
                    if (id) return authFetch(`/calls/${id}/answer`, { method: 'POST' });
                    // fallback: find call by bed in current appState.calls
                    const match = (appState.calls || []).find(c => c.bed === elem.bed && c.state === 'active');
                    if (match) return authFetch(`/calls/${match.id}/answer`, { method: 'POST' });
                    return Promise.resolve();
                });
                Promise.all(promises)
                .then(() => fetchLoad())
                .then(data => setAppState(data))
                .catch(error => console.error(`An ERROR occurred while saving the Answered Calls: ${error}`));
            })
        }
    }
    // ---------------------- end answered call --------------------------

    return (
        <>
            <div className="call-title row justify-content-center clshdw rounded my-2">
                <p className="call-title-text">Llamadas</p>
            </div>
            <div className="calls-col">
            { 
            listCallsLen > 0 &&
                appState.calls.map( (call, index) =>  {
                    return (
                    <Call 
                        key = {`${call.bed},${index}`}
                        call = {call}
                        callBedAndIndex = {`${call.bed},${index}`} 
                    />
                    )
                })
            }
            </div>
        </>
    )
}
