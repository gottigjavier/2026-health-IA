import Task from './task/Task'
import {useContext, useEffect, useState, useRef} from 'react';
import './tasks-list.css'
import {tasksManager} from '../../services/tasks-socket'
import AppContext from '../../context/appContext'
import sound from '../../media/call-bell.mp3'
import {Howl} from 'howler';


function TasksList({places}){
    const [appState, setAppState] = useContext(AppContext);
    const tasksList = appState.tasks || []
    const [tList, setTList] = useState(appState.tasks)
    const [bList, setBList] = useState(appState.beds)
    const [showButton, setShowButton] = useState(true);
    const prevPassedTasksRef = useRef(new Set());
    
    // Setup the new Howl.
    const sounder = new Howl({
        src: [sound]
    });
    
    useEffect(()=> {
        const socket = tasksManager({handleTasks}) // task websocked connect
        return () => { if (socket) socket.close(); }
    },[])
    
    useEffect(()=> {
        setAppState({
            ...appState,
            tasks :  tList,
            beds :  bList
        })          
    } ,[bList, tList])
        

    const handleTasks = msg => {
        const newTasks = msg.tasks_list || [];
        const newPassedIds = new Set(newTasks.filter(t => t.state === 'passed' && t.active).map(t => t.id));
        
        // Only play sound if there are NEW passed tasks that weren't passed before
        // This prevents sound when completing/deleting tasks
        const hasNewPassed = Array.from(newPassedIds).some(id => !prevPassedTasksRef.current.has(id));
        
        if (hasNewPassed && newPassedIds.size > 0) {
            sounder.play();
        }
        
        prevPassedTasksRef.current = newPassedIds;
        setTList(newTasks)
        setBList(msg.beds_list)
    }

    const alertTask = () => {
        setShowButton(false)
        let passed = false;
        tasksList.map(task => {
            if(task.state === 'passed') {
                passed = true
            }
            return passed
        })
        if(passed) {
            sounder.play();
        } 
    }

    return (
        <>
            <div id='tasks-head' className="row task-title justify-content-center tlshdw rounded my-2">
                <p id='tasks-title' className='task-title-text'>Tareas</p>
            </div>
            {showButton &&
                <button onClick={alertTask}>Activar Sonido</button>
            }
            <div className="tasks-col">
            { tasksList.length > 0 &&
                tasksList.map( (task, index) => {
                    const taskBedAndIndex = `${task.bed},${index}`;
                    return (
                        <Task 
                        task = {task}
                        key = {taskBedAndIndex}
                        taskBedAndIndex = {taskBedAndIndex}
                        places = {places}
                        />
                    )
                })
            }
            </div>
        </>
    )
}
export default TasksList;