
import { useEffect, useState, useContext } from 'react';
import './task-modal.css';
import {addMinutes} from '../../../services/handlingDateTime'
import {formattingDate, formattingTime} from '../../../services/formattingDateTime'
import AppContext from '../../../context/appContext'
import AlertModal from './AlertModal'
import { authFetch, fetchLoad } from '../../../services/api'

export default function NewTaskModal({currentBed, handleShowNewTask, hideBedModal}) {
    const room = currentBed.bed_id.split(',')[0];
    const bed = currentBed.bed_id.split(',')[1];
    const defaultProgramedTime = addMinutes(new Date(), 30);
    const defaultDoneTime = addMinutes(new Date(), 150);
    const [programedDate, setProgramedDate] = useState()
    const [programedTime, setProgramedTime] = useState()
    const [doneDate, setDoneDate] = useState()
    const [doneTime, setDoneTime] = useState()
    const [textResponse, setTextResponse] = useState('')
    const [programedBy, setProgramedBy] = useState()
    const [doneBy, setDoneBy] = useState('Anónimo')
    const context = useContext(AppContext);
    const [appState, setAppState] = context;
    const [repeatIsChecked, setRepeatIsChecked] = useState(false)
    const [repeatUntilDate, setRepeatUntilDate] = useState()
    const [repeatUntilTime, setRepeatUntilTime] = useState()
    const [repeatLapse, setRepeatLapse] = useState(2)
    const [repeatLapseUnit, setRepeatLapseUnit] = useState('hours')
    const [alertShow, setAlertShow] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    
    useEffect(() => {
        // fill input date and input time (firefox don't work with input datetime-local)
        
        setProgramedDate(formattingDate('y-m-d', defaultProgramedTime))
        setProgramedTime(formattingTime('h:m', defaultProgramedTime))
        setDoneDate(formattingDate('y-m-d', defaultDoneTime))
        setDoneTime(formattingTime('h:m', defaultDoneTime))
        setRepeatUntilDate(formattingDate('y-m-d', currentBed.bed_planed_vacate))
        setRepeatUntilTime(formattingTime('h:m', currentBed.bed_planed_vacate))
    }, [])
    
    const openAlertShow = () => {
        setAlertShow(true)
    }
    const hiddeAlertShow = () => {
        setAlertShow(false)
    }

    const saveTask = (event) => {
        const bedId = currentBed.id;
        const programedDT = `${programedDate} ${programedTime}`;
        const doneDT = `${doneDate} ${doneTime}`;
        const repeatUntil = `${repeatUntilDate} ${repeatUntilTime}`
        const programer = programedBy || 'Anónimo';
        const textAction = textResponse || 'Tarea de Rutina';
        let state = 'soon';
        const timeNow = new Date();
        if(Date.parse(programedDT) < Date.parse(timeNow)){
            setAlertMessage('Está intentando programar una tarea para un momento que ya pasó')
            event.preventDefault()
            return openAlertShow()
        }
        else if(Date.parse(repeatUntil) < Date.parse(timeNow)){
            setAlertMessage('Está intentando repetir una tarea hasta un momento que ya pasó')
            event.preventDefault()
            return openAlertShow()
        }
        else {
            if(Date.parse(programedDT) - Date.parse(timeNow) > 600000){
                state = 'later'
            }
            const payload = {
                bed_id: bedId,
                task: textAction,
                programed_time: programedDT,
                repeat: repeatIsChecked,
                repeat_lapse: repeatLapse,
                repeat_lapse_unit: repeatLapseUnit,
                repeat_until: repeatUntil
            };

            authFetch('/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(response =>  response.json())  
            .then(() => fetchLoad())
            .then(data => {
                setAppState(data) //updates the context with fresh app state
            })
            .catch(error => {
                console.error(`An ERROR occurred while save New Task, ${error}`);        
            })
            setTextResponse('')
            hideBedModal()
            event.preventDefault()
        }
    }

    const noSaveTask = event => {
        setTextResponse('')
        setProgramedBy('')
        setDoneBy('')
        hideBedModal()
        event.preventDefault()
    }


    return (
        <>
        <div className="container">
            <div className="row justify-content-center task-modal-title tmshdw">
                <h3 id="task-modal-title" className="text-center text-title">
                    <b>Nueva Tarea</b>
                </h3>
            </div>   
            <div id="task-place" className="row tmshdw">
                <p className="modal-subtitle col text-center">Habitación: <b>{room}</b></p>
                <p className="modal-subtitle col text-center">Cama: <b>{bed}</b></p>
            </div>
            <div>
            <p className="modal-subtitle col text-center">Paciente</p>
            <p className='text-center'><b>{currentBed.patient}</b></p>
            </div>
        </div>
        <div className='container tmshdw'>
            <form onSubmit={saveTask} id="task-form">
                <div className="row">                            
                    <div id="task-programed-time" className="col time-box tmshdw">
                        <p className="text-center modal-subtitle">Programar</p>
                        <p className='task-label'>Programado por </p>
                        <input type='text' id='programed-by' name='programed-by' className= 'tx-box ml-3 mb-1'
                        onChange= {event => setProgramedBy(event.target.value)} value={programedBy} placeholder={'Anónimo'}/>
                        <hr/>
                        <p className='task-label'>A Cumplirse el </p>
                        <input type="date" id="programed-to" name="programed-to" className= 't-box mb-1'
                            onChange={event => setProgramedDate(event.target.value)} value={programedDate}
                        />
                        <input type="time" id="programed" name="programed" className= 't-box mb-1'
                            onChange={event => setProgramedTime(event.target.value)} value={programedTime}
                        />
                    </div>
                    <div id="repeat-task" className="col time-box tmshdw">
                        <div className="text-center modal-subtitle mb-2">
                        <span>Repetir</span>
                            <input type='checkbox' id='check-repeat' name='check-repeat' className= 'ml-3 mb-1'
                            onChange= {event => setRepeatIsChecked(event.target.checked)} checked={repeatIsChecked}/>
                        </div>
                        <p className='task-label'>Cada: </p>
                        <input type='number' id='repeat-count' name='repeat-count' className='number-box ml-3 mb-1'
                        onChange= {event => setRepeatLapse(event.target.value)} value={repeatLapse} placeholder={2}/>
                        <select onChange= {event => setRepeatLapseUnit(event.target.value)} value= {repeatLapseUnit} className='select-box ml-1 mb-1'>
                            <option value='minutes'>minutos</option>
                            <option value='hours'>horas</option>
                            <option value='days'>días</option>
                        </select>
                        <hr/>
                        <p className='task-label'>Hasta </p>
                        <input disabled={false} type="date" id="done" name="done" className='t-box'
                            onChange={event => setRepeatUntilDate(event.target.value)} value={repeatUntilDate}
                        />
                        <input disabled={false} type="time" id="done" name="done" className= 't-box '
                            onChange={event => setRepeatUntilTime(event.target.value)} value={repeatUntilTime}
                        />
                        <p>
                        <small className='small'>*Por defecto, momento previsto para desocupar la cama</small>
                        </p>
                    </div>
                </div>
                <div className="justify-content-center row"> 
                    <label className="modal-subtitle col text-center"><b>Tarea</b>     
                        <textarea onChange={event => setTextResponse(event.target.value)} value={textResponse} id="action-text" className="text-box tmshdw" placeholder={'Ingrese Nueva Tarea'} name="answer-task" maxlength="1000" />
                    </label>
                </div>
                <div id="task-form-buttons" className="row">
                    <div id="new-edit-buttons" className="col">
                        <input type="submit" value="Guardar" id="task-send" className="tmshdw save btn m-2 float-right" title="Guardar"/>
                    </div>
                </div>
            </form>
            <button type="button" id="task-close" className="tmshdw discard btn m-2 float-right" title="Descartar" onClick={noSaveTask}>
                Descartar Cambios
            </button>
        </div>
        { alertShow &&
            <AlertModal
                alertShow = {alertShow}
                hiddeAlertShow = {hiddeAlertShow}
                alertMessage = {alertMessage}
            />
        }
        </>
    )
}
