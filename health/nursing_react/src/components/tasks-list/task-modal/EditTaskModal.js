
import { useEffect, useState, useContext } from 'react';
import './task-modal.css';
import {formattingDate, formattingTime} from '../../../services/formattingDateTime';
import AppContext from '../../../context/appContext'

function EditTaskModal({ hideTaskModal, show, task, taskBedAndIndex}) {
    const showHideClassName = show ? "modal display-block" : "display-none";
    const bedIdSplit = taskBedAndIndex.split(','); 
    const room = bedIdSplit[0];
    const bed = bedIdSplit[1];
    const taskIndex = bedIdSplit[2];
    const [textResponse, setTextResponse] = useState(task.task)
    const [programedDate, setProgramedDate] = useState()
    const [programedTime, setProgramedTime] = useState()
    const [doneDate, setDoneDate] = useState()
    const [doneTime, setDoneTime] = useState()
    const [programedBy, setProgramedBy] = useState(task.programed_by)
    const [taskEditor, setTaskEditor] = useState(task.action_done_by)
    const [doneBy, setDoneBy] = useState(task.task_done_by)
    const [taskState, setTaskState] = useState(task.active)
    const context = useContext(AppContext);
    const [appState, setAppState] = context;
    const [repeatIsChecked, setRepeatIsChecked] = useState(false)
    
    useEffect(() => {
        // fill input date and input time (firefox don't work with input datetime-local)
        
        setProgramedDate(formattingDate('y-m-d', task.programed_time))
        setProgramedTime(formattingTime('h:m', task.programed_time))
        setDoneDate(formattingDate('y-m-d', task.done_time))
        setDoneTime(formattingTime('h:m', task.done_time))
        setTextResponse(textResponse => textResponse = task.task)
    }, [])

    
    const saveTask = (event) => {
        const programedDT = `${programedDate} ${programedTime}`
        const doneDT = `${doneDate} ${doneTime}`
        const taskId = task.id;
        const programer = programedBy;
        const editor = taskEditor;
        const maker = doneBy;
        let textAction = textResponse;
        const timeNow = new Date();
        const currentBed = room + ',' + bed;
        let active = taskState;
        let state = 'soon';
        let doneTimeSent = null;
        
        // Check if done time is in the past - mark task as completed
        // Only mark as done if user explicitly set a done date/time
        if(doneDate && doneTime && Date.parse(doneDT) < Date.parse(timeNow)){
            textAction = `${textResponse}(Done)`
            active = false
            doneTimeSent = doneDT; // Send done_time to backend
        }
        if(Date.parse(programedDT) - Date.parse(timeNow) > 600000){
            state = 'later'
        } 
        else if(Date.parse(programedDT) - Date.parse(timeNow) > 0 && Date.parse(programedDT) - Date.parse(timeNow) < 1800000){
            state = 'soon'
        } else if (Date.parse(programedDT) - Date.parse(timeNow) < 0) {
            state = 'passed'
        }
        
        // Use authenticated API and reload full app state so UI stays consistent
        import('../../../services/api').then(({ updateTask, fetchLoad }) => {
            const updateData = { 
                task: textAction, 
                programed_time: programedDT,
                active: active
            };
            // Include done_time if task is being marked as completed
            if (doneTimeSent) {
                updateData.done_time = doneTimeSent;
            }
            
            updateTask(taskId, updateData)
            .then(() => fetchLoad())
            .then(data => setAppState(data))
            .catch(error => console.error(`An ERROR occurred while saving the Edited Task: ${error}`));
        });
        setTextResponse('')
        hideTaskModal()
        event.preventDefault()
    }

    const doneTask = () => {
        // Call the complete API to mark task as done and update bed_state
        import('../../../services/api').then(({ completeTask, fetchLoad }) => {
            completeTask(task.id)
            .then(() => fetchLoad())
            .then(data => setAppState(data))
            .catch(error => console.error(`Error completing task: ${error}`));
        });
        hideTaskModal();
    } 
    
    const deleteTask = event => {
        const taskPk = task.id;
        const currentBed = room + ',' + bed;
        const reapeatTasksId = task.repeat_id
        // Delete single task or, if user requested, delete all repeated occurrences.
        import('../../../services/api').then(({ authFetch, fetchLoad }) => {
            if (repeatIsChecked && reapeatTasksId) {
                // No bulk-delete API; delete by repeat_id by fetching tasks then deleting each
                // Fetch current tasks and remove those with matching repeat_id
                fetchLoad().then(data => {
                    const tasks = data.tasks || [];
                    const toDelete = tasks.filter(t => t.repeat_id === reapeatTasksId).map(t => t.id);
                    Promise.all(toDelete.map(id => authFetch(`/tasks/${id}`, { method: 'DELETE' })))
                    .then(() => fetchLoad())
                    .then(d => setAppState(d))
                    .catch(err => console.error('Error deleting repeated tasks', err));
                });
            } else {
                authFetch(`/tasks/${taskPk}`, { method: 'DELETE' })
                .then(() => fetchLoad())
                .then(d => setAppState(d))
                .catch(error => console.error(`An ERROR occurred while deleting Task: ${error}`));
            }
        });
        hideTaskModal()
        event.preventDefault()
    }

    const noSaveTask = event => {
        setTextResponse('')
        setProgramedBy('')
        setTaskEditor('')
        setDoneBy('')
        hideTaskModal()
        event.preventDefault()
    }


    return (
        <>
        <div className={showHideClassName}>
            <section className="modal-task">
                <div className="container">
                    <div className="row justify-content-center task-modal-title">
                        <h3 id="task-modal-title" className="text-center text-title">
                            <b>Editar Tarea</b>
                        </h3>
                    </div>   
                    <form onSubmit={saveTask} id="task-form" className="form-container">
                        <div id="task-place" className="row tmshdw">
                            <p className="modal-subtitle col text-center">Orden: <b>{parseInt(taskIndex) + 1}</b></p>
                            <p className="modal-subtitle col text-center">Habitación: <b>{room}</b></p>
                            <p className="modal-subtitle col text-center">Cama: <b>{bed}</b></p>
                        </div>
                        <div>
                            <p className="modal-subtitle col text-center">Paciente</p>
                            <p className='text-center'><b>{task.patient}</b></p>
                        </div>
                        <div className="row">                            
                            <div id="task-programed-time" className="col time-box tmshdw">
                                <p className="text-center modal-subtitle">Reprogramar</p>
                                <p className='task-label'>Programada por </p>
                                <input type='text' id='programed-by' name='programed-by' className= 'tx-box ml-3 mb-1'
                                onChange= {event => setProgramedBy(event.target.value)} value={programedBy} placeholder={task.programed_by}/>
                                <p className='task-label'>Editada por</p>
                                <input disabled={false} type='text' id='task-by' name='task-by' className= 'tx-box ml-3 mb-1'
                                onChange= {event => setTaskEditor(event.target.value)} value={taskEditor} placeholder={task.action_done_by}/>
                                <hr/>
                                <p className='task-label'>Programada para el </p>
                                <input type="date" id="programed-to" name="programed-to" className= 't-box mb-1'
                                    onChange={event => setProgramedDate(event.target.value)} value={programedDate}
                                />
                                <input type="time" id="programed" name="programed" className= 't-box mb-1'
                                    onChange={event => setProgramedTime(event.target.value)} value={programedTime}
                                />
                            </div>
                            <div id="task-done-time" className="col time-box tmshdw" title="Si el momento que figura en este sector ya pasó, la tarea se guardará como cumplida en ese momento">
                                <p className="text-center modal-subtitle">Efectivización de la Tarea</p>
                                <p className='task-label'>Cumplida por</p>
                                <input disabled={false} type='text' id='done-by' name='done-by' className= 'tx-box ml-3 mb-1'
                                onChange= {event => setDoneBy(event.target.value)} value={doneBy} placeholder={task.task_done_by}/>
                                <hr/>
                                <input disabled={false} type="date" id="done" name="done" className= 't-box mb-1'
                                    onChange={event => setDoneDate(event.target.value)} value={doneDate}
                                />
                                <input disabled={false} type="time" id="done" name="done" className= 't-box mb-1'
                                    onChange={event => setDoneTime(event.target.value)} value={doneTime}
                                />
                                <p>
                                <small className='small'>*Guardar tarea ya realizada: ingrese cuándo se realizó y presione "Guardar Edición", o presione "Recién Cumplida"</small>
                                </p>
                                <button type="button" onClick={doneTask} id="task-done" className="tmshdw done btn m-1" title="Recién Cumplida">Recién Cumplida</button>
                            </div>
                        </div>
                        <div className="justify-content-center row"> 
                            <label className="modal-subtitle col text-center"><b>Tarea</b>     
                                <textarea onChange={event => setTextResponse(event.target.value)} value={textResponse} id="action-text" className="text-box tmshdw" placeholder={task.task} name="answer-task" maxlength="1000" />
                            </label>
                        </div>
                        <div id="task-form-buttons" className="row">
                            <div id="new-edit-button" className="col ml-3">
                                <input type="submit" value="Guardar Edición" id="task-send" className="tmshdw save btn m-1" title="Guardar"/>
                            </div>
                            <div className='col border border-secondary mt-1 mb-4 mx-4'>
                                <button type="button" onClick={deleteTask} id="task-delete" className="tmshdw delete btn m-1 float-left" title="Eliminar Tarea">Eliminar Tarea</button>
                                    <label className='align-middle mycheck-box'>
                                    <input type='checkbox' id='check-repeat' name='check-repeat' className= ''
                                    onChange= {event => setRepeatIsChecked(event.target.checked)} checked={repeatIsChecked}/>
                                    <span className='task-label ml-1'> Todas las Ocurrencias</span>
                                </label>
                            </div>
                        </div>
                    </form>
                    <button type="button" id="task-close" className="tmshdw discard btn mx-3 mb-2 float-right" title="Descartar" onClick={noSaveTask}>
                        Descartar Cambios
                    </button>
                </div>
            </section>
        </div>
        </>
    )
}

export default EditTaskModal;
