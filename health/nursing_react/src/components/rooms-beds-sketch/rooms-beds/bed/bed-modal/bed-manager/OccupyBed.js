import {useContext, useState} from 'react';
import AppContext from '../../../../../../context/appContext'
import './bed-manager.css'
import {formattingDate, formattingTime} from '../../../../../../services/formattingDateTime'
import {addDays} from '../../../../../../services/handlingDateTime'
import AlertModal from '../../../../../tasks-list/task-modal/AlertModal'
import { authFetch, fetchLoad } from '../../../../../../services/api'


export default function OccupyBed({currentBed, handleShowInfo}){
    const [appState, setAppState] = useContext(AppContext);
    const [patientName, setPatientName] = useState('')
    //const [patientCard, setPatientCard] = useState() (only in some countries)
    const [patientSocial, setPatientSocial] = useState('')
    const [occupiedDate, setOccupiedDate] = useState(formattingDate('y-m-d', new Date()))
    const [occupiedTime, setOccupiedTime] = useState(formattingTime('h:m', new Date()))
    const vacateDatePLus = addDays(new Date() , 7)
    const [vacateDate, setVacateDate] = useState(formattingDate('y-m-d', vacateDatePLus))
    const [vacateTime, setVacateTime] = useState(formattingTime('h:m', vacateDatePLus))
    const [diagnosis, setDiagnosis] = useState('')
    const [doneBy, setDoneBy] = useState('')
    const [alertShow, setAlertShow] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');

    const openAlertShow = () => {
        setAlertShow(true)
    }
    const hiddeAlertShow = () => {
        setAlertShow(false)
    }
    
    const saveOccupyBed = event => {
        const occupiedDateTime = occupiedDate + ' ' + occupiedTime; 
        const planedVacate = vacateDate + ' ' + vacateTime;
        const timeNow = new Date();
        
        if(Date.parse(planedVacate) < Date.parse(occupiedDateTime)){
            setAlertMessage('No puede planear desocupar la cama para un momento anterior a ocuparla')
            event.preventDefault()
            return openAlertShow()
        }
        if(Date.parse(planedVacate) < Date.parse(timeNow)){
            setAlertMessage('No puede planear desocupar la cama antes de ahora si todavía no la ocupó')
            event.preventDefault()
            return openAlertShow()
        }
        const roomBedId = currentBed.bed_id;
        
        const payload = {
            roomBedId: roomBedId,
            patientName: patientName,
            patientSocial: patientSocial,
            diagnosis: diagnosis,
            occupiedDateTime: occupiedDateTime,
            planedVacate: planedVacate,
            doneBy: doneBy || 'Anónimo'
        };

        authFetch('/beds', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())  
        .then(result => {
            // Reload app data after occupying bed
            return fetchLoad();
        })
        .then(data => {
            setAppState(data) //updates the context with fresh data
        })
        .catch(error => {
            console.error(`An ERROR occurred while save Occupy Bed, ${error}`);        
        })
        handleShowInfo()
    }

    return (
        <>
        <div className="container">
            <div className="row justify-content-center info-modal-title bmshdw">
                <h3 id="info-modal-title" className="text-center text-title">
                    <b>Ocupar Cama</b>
                </h3>
            </div>
            <div className='row bmshdw'>
                <div className='col'>
                <p className="col text-center mt-3">Habitación: <span className="modal-subtitle">{currentBed.bed_id.split(',')[0]}</span></p>
                    
                </div>
                <div className='col'>
                <p className="col text-center mt-3">Cama: <span className="modal-subtitle">{currentBed.bed_id.split(',')[1]}</span></p>
                </div>
            </div>
        </div>
        <div className='container bmshdw'>
        <form id='occupy-form' onSubmit={saveOccupyBed}>
        <div className='container'>
                <div className='row'>
                    <div className='col-2'></div>
                    <div className='col-8 modal-subtitle-center my-2'>Paciente</div>
                    <div className='col-2'></div>
                </div>
                <div className='row justify-content-center'>
                    <div className='col justify-content-center'>
                        <input className='input-box-center text-center' type='text' id='patient-name' name='patient-name' 
                        placeholder='Nombre del Paciente' value={patientName} onChange={event => setPatientName(event.target.value)}/>
                    </div>
                    {
                    /* (only in some countries) 
                <div className='row'>
                    <div className='col justify-content-center'>
                        <input className='input-box-center text-center' type='text' id='patient-card' name='patient-card' 
                        placeholder='Patient Card Number' value={patientCard} onChange={event => setPatientCard(event.target.value)}/>
                    </div>
                </div> */
                }
                    <div className='col justify-content-center'>
                        <input className='input-box-center text-center' type='text' id='patient-social' name='patient-social' 
                        placeholder='Nº: OS, Hist. Clínica o DNI' value={patientSocial} onChange={event => setPatientSocial(event.target.value)}/>
                    </div>
                </div>
            <div className='row'>
                <div className='col-2'></div>
                <div className="col-8 modal-subtitle-center mb-2 mt-4">Diagnóstico</div>
                <div className='col-2'></div>
            </div>
            <div className='row justify-content-center'>
                <textarea id='diagnosis-info' name='diagnosis-info' className='text-box mb-3' 
                placeholder='Resumen de Diagnóstico' value={diagnosis} onChange={event => setDiagnosis(event.target.value)}/>
            </div>
        </div>
        <div className='container'>
            <div className='row'>
                <div className='col-2'></div>
                <div className='col-8 modal-subtitle-center my-2'>Cama</div>
                <div className='col-2'></div>
            </div>
        <div className="row">                            
                <div id="occupied" className="col time-box bmshdw">
                    <p className="text-center modal-subtitle">Se ocupó</p>
                    <input type="date" id="occupied-date" name="occupied-date" className= 'mb-1'
                        onChange={event => setOccupiedDate(event.target.value)} value={occupiedDate}
                    />
                    <input type="time" id="occupied-time" name="occupied-time" className= 'mb-1'
                        onChange={event => setOccupiedTime(event.target.value)} value={occupiedTime}
                    />
                </div>
                <div id="vacate" className="col time-box bmshdw">
                    <p className="text-center modal-subtitle">Previsto desocupar</p>
                    <input type="date" id="vacate-date" name="vacate-date" className= 'mb-1'
                        onChange={event => setVacateDate(event.target.value)} value={vacateDate}
                    />
                    <input type="time" id="vacate-time" name="vacate-time" className= 'mb-1'
                        onChange={event => setVacateTime(event.target.value)} value={vacateTime}
                    />
                </div>
            </div>
            <div className="row justify-content-end">
                <p className='justify-content-end info-label mt-3'>Realizado por</p> <br/>
                <input type='text' id='done-by' name='done-by' className= 'justify-content-end my-3 mx-2'
                onChange= {event => setDoneBy(event.target.value)} value={doneBy} placeholder='Anónimo'/>
            </div>
        </div>
        <div className="justify-content-end">
            <input type='submit' value="Guardar" id="edit-bed-send" className="btn bmshdw m-2 px-2 py-1 float-right" title="Guardar"/>
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