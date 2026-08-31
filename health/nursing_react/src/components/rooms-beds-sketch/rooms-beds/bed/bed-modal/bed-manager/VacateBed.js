import './bed-manager.css'
import {formattingDateTime, formattingDate, formattingTime} from '../../../../../../services/formattingDateTime'
import { useState, useContext } from 'react';
import AppContext from '../../../../../../context/appContext';
import AlertModal from '../../../../../tasks-list/task-modal/AlertModal'
import { authFetch, fetchLoad } from '../../../../../../services/api'

export default function VacateBed({currentBed, hideBedModal}){
    const [appState, setAppState] = useContext(AppContext)
    const [bedState, setBedState] = useState(currentBed.bed_state === 'free' ? 'Desocupada' : 'Ocupada');
    const occupiedTime = formattingDateTime('d-m-y', currentBed.bed_occupied_time)
    const planedVacate = currentBed.bed_planed_vacate ? formattingDateTime('d-m-y', currentBed.bed_planed_vacate) : 'Undetermined'
    const [vacateDate, setVacateDate] = useState(formattingDate('y-m-d', new Date()))
    const [vacateTime, setVacateTime] = useState(formattingTime('h:m', new Date()))
    const [doneBy, setDoneBy] = useState('Anónimo')
    const [alertShow, setAlertShow] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');

    const openAlertShow = () => {
        setAlertShow(true)
    }
    const hiddeAlertShow = () => {
        setAlertShow(false)
    }
    
    
    const saveVacateBed = event => {
        const vacateDT = vacateDate + ' ' + vacateTime;
        const timeNow = new Date();
        if(Date.parse(vacateDT) > Date.parse(timeNow)){
            setAlertMessage('Para desocupar la cama no puede utilizar un momento futuro')
            event.preventDefault()
            return openAlertShow()
        }
        
        const bedId = currentBed.id;
        const patientId = currentBed.patient_id;
        currentBed.bed_active = false;
        currentBed.bed_state = 'free';
        currentBed.patient = 'No Name';
        currentBed.diagnosis = 'No Diagnosis';
        setBedState('Desocupada');
        
        event.preventDefault()
        
        const payload = {
            bedId: bedId,
            patientId: patientId,
            vacateDT: vacateDT,
            doneBy: doneBy
        };

        authFetch('/beds/vacate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response =>  response.json())  
        .then(result => {
            // Reload app data after vacating bed
            return fetchLoad();
        })
        .then(data => {
            setAppState(data) //updates the context with fresh data
        })
        .catch(error => {
            console.error(`An ERROR occurred while vacate Bed, ${error}`);        
        })
        hideBedModal()
    }

    return (
        <>
            <div className="container">
                    <div className="row justify-content-center info-modal-title bmshdw">
                        <h3 id="info-modal-title" className="text-center text-title">
                            <b>Desocupar Cama</b>
                        </h3>
                    </div>
                    <div className='row bmshdw'>
                        <div className='col'>
                        <p className="col text-center mt-3 modal-subtitle">Habitación: <span className="p-styled1">{currentBed.bed_id.split(',')[0]}</span></p>
                            
                        </div>
                        <div className='col'>
                        <p className="col text-center mt-3 modal-subtitle">Cama: <span className="p-styled1">{currentBed.bed_id.split(',')[1]}</span></p>
                        </div>
                    </div>
                    <div className='row bmshdw'>
                        <div className='col-md-8 col-sm-8'>
                            <p className="modal-subtitle">Paciente</p>
                            <p className='p-styled1'>
                                {currentBed.patient}
                            </p>
                        </div>
                        <div className='col-md-2 col-sm-4'>
                            <p className="modal-subtitle">Estado</p>
                            <p className='p-styled1'>
                                {bedState}
                            </p>
                        </div>
                    </div>
                    <div className='row justify-content-center bmshdw pb-3'>
                        <p className="modal-subtitle">Diagnóstico</p>
                        <p className='border border-info text-box'>
                            {currentBed.diagnosis}
                        </p>
                    </div>
                    <div className='row bmshdw pb-3'>
                    { currentBed.bed_active &&
                        <div className='col justify-content-center'>
                            <p className="modal-subtitle">Se ocupó</p>
                            <p className='p-styled1 text-center'>
                                {occupiedTime}
                            </p>
                        </div>
                    }
                    { currentBed.bed_active &&
                        <div className='col justify-content-center'>
                            <p className="modal-subtitle">Previsto desocupar</p>
                            <p className='p-styled1 text-center'>
                                {planedVacate}
                            </p>
                        </div>
                    }
                    </div>
                    <form id='edit-bed' onSubmit={saveVacateBed}>
                    <div className='container bmshdw'>
                        <div id="vacate" className="time-box">
                            <p className="text-center modal-subtitle">Se desocupó</p>
                            <div className='row'>
                                <div className='col-2'></div>
                                <div className='col-8 b-center'>
                                    <input type="date" id="vacate-date" name="vacate-date" className= 'mb-1'
                                        onChange={event => setVacateDate(event.target.value)} value={vacateDate}
                                    />
                                    <input type="time" id="vacate-time" name="vacate-time" className= 'mb-1'
                                        onChange={event => setVacateTime(event.target.value)} value={vacateTime}
                                        />
                                </div>
                                <div className='col-2'></div>
                            </div>
                        </div>
                        <div className="row justify-content-end">
                            <p className='justify-content-end info-label mt-3'>Realizado por</p> <br/>
                            <input type='text' id='done-by' name='done-by' className= 'justify-content-end my-3 mx-3'
                            onChange= {event => setDoneBy(event.target.value)} value={doneBy} placeholder={doneBy}/>
                        </div>
                        <div className='row justify-content-center vacate-warning bmshdw'>
                            <i className='vacate-text-warning text-center'>Desocupar la cama borrará de las listas todas sus llamadas y tareas</i>
                        </div>
                        <div className="row justify-content-end">
                            <input type='submit' value="Guardar" id="edit-bed-send" className="btn save bmshdw m-2 px-2 py-1 float-right" title="Guardar"/>
                        </div>
                    </div>
                </form>
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