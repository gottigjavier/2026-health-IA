import {useContext, useEffect, useState} from 'react';
import AppContext from '../../../../../../context/appContext'
import {formattingDate, formattingTime} from '../../../../../../services/formattingDateTime'
import './bed-manager.css'
import AlertModal from '../../../../../tasks-list/task-modal/AlertModal'


export default function EditBed({currentBed, handleShowInfo}){
    const context = useContext(AppContext);
    const [appState, setAppState] = context;
    const bedState = currentBed.bed_state === 'free' ? 'Desocupada' : 'Ocupada';
    const [occupiedDate, setOccupiedDate] = useState()
    const [occupiedTime, setOccupiedTime] = useState()
    const [vacateDate, setVacateDate] = useState()
    const [vacateTime, setVacateTime] = useState()
    const [patientName, setPatientName] = useState(currentBed.patient)
    //const [patientCard, setPatientCard] = useState() (only in some countries)
    const [patientSocial, setPatientSocial] = useState(currentBed.patient_security_number)
    const [diagnosis, setDiagnosis] = useState(currentBed.diagnosis)
    const [doneBy, setDoneBy] = useState()
    const [alertShow, setAlertShow] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    
    useEffect(() => {
        setOccupiedDate(formattingDate('y-m-d', currentBed.bed_occupied_time))
        setOccupiedTime(formattingTime('h:m', currentBed.bed_occupied_time))
        setVacateDate(currentBed.bed_planed_vacate ? formattingDate('y-m-d', currentBed.bed_planed_vacate) : '0000-00-00')
        setVacateTime(currentBed.bed_planed_vacate ? formattingTime('h:m', currentBed.bed_planed_vacate) : '0000-00-00')
        setDoneBy(currentBed.action_done_by)
    }, [])

    const openAlertShow = () => {
        setAlertShow(true)
    }
    const hiddeAlertShow = () => {
        setAlertShow(false)
    }


    const saveEditBed = event => {
        const occupiedDateTime = occupiedDate + ' ' + occupiedTime; 
        const planedVacate = vacateDate + ' ' + vacateTime;
        const timeNow = new Date();
        
        if(Date.parse(occupiedDateTime) > Date.parse(timeNow)){
            setAlertMessage('Está intentando ocupar la cama en un tiempo futuro sin antes desocuparla')
            event.preventDefault()
            return openAlertShow()
        }
        if(Date.parse(planedVacate) < Date.parse(timeNow)){
            setAlertMessage('Para desocupar una cama en un momento pasado utilice la pestaña "Desocupar"')
            event.preventDefault()
            return openAlertShow()
        }
        
        const bedId = currentBed.id;
        import('../../../../../../services/api').then(({ authFetch, fetchLoad }) => {
            authFetch(`/beds/${bedId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patientName,
                    patientSocial,
                    diagnosis,
                    occupiedDateTime,
                    planedVacate,
                    doneBy
                })
            })
            .then(() => fetchLoad())
            .then(data => setAppState(data))
            .catch(error => console.error(`An ERROR occurred while saving the Edited Bed: ${error}`));
        });
        handleShowInfo()
        event.preventDefault()
    }


    return (
        <>
        <div className="container">
            <div className="row justify-content-center info-modal-title bmshdw">
                <h3 id="info-modal-title" className="text-center">
                    <b>Editar Cama</b>
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
        </div>
            <div className='container bmshdw'>
                <form id='edit-bed' onSubmit={saveEditBed}>
                <div className='container'>
                    <div className='row'>
                        <div className='col-2'></div>
                        <div className='col-8 modal-subtitle-center my-2'>Paciente</div>
                        <div className='col-2'></div>
                    </div>
                    <div className='row justify-content-center'>
                        <div className='col justify-content-center'>
                            <label className='text-box mb-0'>Nombre</label>
                            <input className='input-box-center text-center' type='text' id='patient-name' name='patient-name' 
                            placeholder={patientName} value={patientName} onChange={event => setPatientName(event.target.value)}/>
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
                            <label className='text-box mb-0'>Nº: OS, Hist. Clínica o DNI</label>
                            <input className='input-box-center text-center' type='text' id='patient-social' name='patient-social' title='Nº: OS, Hist. Clínica o DNI'
                            placeholder={patientSocial} value={patientSocial} onChange={event => setPatientSocial(event.target.value)}/>
                        </div>
                    </div>
                    <div className='row'>
                        <div className='col-2'></div>
                        <div className="col-8 modal-subtitle-center mb-2 mt-4">Diagnóstico</div>
                        <div className='col-2'></div>
                    </div>
                    <div className='row justify-content-center'>
                        <textarea id='diagnosis-info' name='diagnosis-info' className='text-box mb-3' 
                        placeholder={diagnosis} value={diagnosis} onChange={event => setDiagnosis(event.target.value)}/>
                    </div>
                    <div className="row">                            
                        <div id="occupied" className="col time-box bmshdw mx-1">
                            <p className="text-center modal-subtitle">Se ocupó</p>
                            <input type="date" id="occupied-date" name="occupied-date" className= 'd-box'
                                onChange={event => setOccupiedDate(event.target.value)} value={occupiedDate}
                            />
                            <input type="time" id="occupied-time" name="occupied-time" className= 'tm-box'
                                onChange={event => setOccupiedTime(event.target.value)} value={occupiedTime}
                            />
                        </div>
                        <div id="vacate" className="col time-box bmshdw mx-1">
                            <p className="text-center modal-subtitle">Previsto desocupar</p>
                            <input type="date" id="vacate-date" name="vacate-date" className= 'd-box'
                                onChange={event => setVacateDate(event.target.value)} value={vacateDate}
                            />
                            <input type="time" id="vacate-time" name="vacate-time" className= 'tm-box'
                                onChange={event => setVacateTime(event.target.value)} value={vacateTime}
                            />
                        </div>
                    </div>
                    <div className="row my-4 mx-0">
                        <div className='col-4'></div>
                        <div className='col-8 d-flex justify-content-end'>
                                    <label className='done-label'>Realizado por</label>
                                    <input type='text' id='done-by' name='done-by' className= 'done-box'
                                    onChange= {event => setDoneBy(event.target.value)} value={doneBy} placeholder={doneBy}/>
                        </div>
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
