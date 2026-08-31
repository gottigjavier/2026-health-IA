import './call.css'
import CallModal from '../call-modal/CallModal'
import {useState, useContext, useEffect, useRef} from 'react'
import AppContext from '../../../context/appContext'
import bedAvatar from '../../../media/bed-solid-white.svg'
import sounds from '../../../media/call-tone.mp3';
import {Howl} from 'howler';


export default function Call({ call, callBedAndIndex}){
    const roomSplit = call.bed.split(',');
    const room = roomSplit[0];
    const bed = roomSplit[1];
    const [appState, setAppState] = useContext(AppContext); // looks like hook?
    const [show, setShow]= useState(false)
    const [callEventId, setCallEventId] = useState('');
    const audioCtxRef = useRef(null);

    // Setup the new Howl.
    const sounder = new Howl({
        src: [sounds],
        onloaderror: (id, err) => console.error('Sound load error:', err)
    });

    useEffect(() => {
        if (!audioCtxRef.current) {
            audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtxRef.current.state === 'suspended') {
            audioCtxRef.current.resume();
        }
    }, []);

    useEffect(() => {
        if (call.state !== 'active') return;
        
        const playSound = () => {
            sounder.play();
        };
        
        playSound();
        
        const intervalId = setInterval(playSound, 15000);
        
        return(() => {
            clearInterval(intervalId);
        })
    }, [call.state, call.bed])

    // To display in title
    const patient = () => {
        let callPatient = '';
        const roomBed = call.bed
        const bedsList = appState.beds
        bedsList.map(element => {
            if(element.bed_id === roomBed){
                callPatient =  element.patient
            }
            return callPatient
        })
        return callPatient
    }
    
    // Show Modal ---------------------------
    const showCallModal = (event) => {
        setCallEventId(callEventId => callEventId = event.target.id ? event.target.id : event.target.offsetParent.id);
        setShow(show => show = true );
    };
    
    const hideCallModal = () => {
        setShow(show => show = false );
    };
    
    // ---------------------- Closed call --------------------------------    
    const closeCall = (currentCallId, currentCallTime, textResponse, answeredBy) => {
        hideCallModal();
        saveCloseCall(currentCallId, currentCallTime, textResponse, answeredBy)
        }

    const saveCloseCall = async (currentCallId, currentCallTime, textResponse, answeredBy='Anonymous') => {
        const callId = currentCallId
        const callTime = currentCallTime;
        const text = textResponse === '' ? 'Respuesta Sin Novedad (por defecto)' : textResponse;
        import('../../../services/api').then(({ authFetch, fetchLoad }) => {
            const bed_id = call.bed_id || call.bedId || null;
            authFetch(`/calls/${callId}/close`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ response: text, bed_id })
            })
            .then(() => fetchLoad())
            .then(data => setAppState(data))
            .catch(error => console.error(`An ERROR occurred while saving the Closed Call: ${error}`));
        })
    }    
// ---------------------- End Closed call --------------------------------

    return (
        <>                        
            <div id={'c-' + callBedAndIndex} onClick={showCallModal} title={patient()}
            className= {`animate__animated animate__fadeInUp card text-center call cshdw rounded my-1 ${call.state}`}>
                <div className="card-hearder call-row py-1" onClick={showCallModal}>
                    <p className='call-bed'> HAB <b>{room}</b> </p>
                </div>
                <div className="card-title call-row py-1" onClick={showCallModal}>
                    
                    <p className='call-bed'> <b>{bed + ' '}</b>
                        <img id={`call-bed-avatar-${bed}`} src={bedAvatar} alt='Bed Avatar' className='call-bed-avatar' onClick={showCallModal}>
                        </img>
                    </p>
                </div>             
            </div>
            <div>
                { show &&
                    <CallModal 
                        key = {'CM-3'}
                        show={show} 
                        hideCallModal={hideCallModal}
                        callEventId={callEventId}
                        call= {call}
                        closeCall= {closeCall} 
                    />
                }
            </div>
        </>
    )    
}
