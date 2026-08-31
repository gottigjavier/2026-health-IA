function getAccessToken() {
    const meta = document.querySelector('meta[name="access-token"]');
    if (meta && meta.content) {
        return meta.content;
    }
    // Fallback: SPA stores the JWT here after /api/auth/login (same origin).
    return localStorage.getItem('access_token') || '';
}

document.addEventListener('DOMContentLoaded', function() {
    room_calls();
    document.addEventListener('click', event => {
        const elem = event.target;
        //console.log(elem.id);
        call(elem.id);
    });
});

function connectSocket() {
    const token = getAccessToken();
    const url = token
        ? 'ws://' + window.location.host + '/ws/callData/?token=' + encodeURIComponent(token)
        : 'ws://' + window.location.host + '/ws/callData/';
    return new WebSocket(url);
}

let callSocket = connectSocket();

// Reconnect the call socket if it is not open yet (the JWT-based consumer
// rejects connections without a token, and sockets may close/retry).
function ensureSocket() {
    if (!callSocket || callSocket.readyState !== WebSocket.OPEN) {
        callSocket = connectSocket();
    }
    return callSocket;
}

function call(call_id){
    ensureSocket();
    let state;
    if(!call_id.includes(',0')){
        state = true;
    }
    else{
        state = false;
    }
    const key = document.querySelector('meta[name="call-secret"]')
        ? document.querySelector('meta[name="call-secret"]').content
        : '';
    callSocket.send(JSON.stringify({
        'key': key,
        'state': state,
        'bed': call_id
    }))
}

function room_calls(){
    const TOTAL_ROOMS = 30,
        TOTAL_BEDS = 4;
        const $containerRooms = document.createElement('div');
        $containerRooms.setAttribute('class', 'row justify-content-center');
        const $fragmentRooms = document.createDocumentFragment();
    
    for (roomsCounter=1; roomsCounter<=TOTAL_ROOMS; roomsCounter++){
        const $room = document.createElement('div');
        $room.setAttribute('class', 'col-2 shadow-lg bg-light rounded m-1 justify-content-center');
        const $room_head = document.createElement('button');
        $room_head.setAttribute('class', 'btn btn-danger m-2');
        $room_head.setAttribute('id', `${roomsCounter},0`);
        $room_head.innerHTML = `Room ${roomsCounter}`;
        const $room_beds = document.createElement('div');
        $room_beds.setAttribute('class', 'row text-center shadow-lg bg-light rounded justify-content-center');
        for (bedsCounter=1; bedsCounter<=TOTAL_BEDS; bedsCounter++){
            const $bed = document.createElement('button');
            $bed.setAttribute('class', 'btn btn-success m-2');
            $bed.setAttribute('id', `${roomsCounter},${bedsCounter}`);
            $bed.innerHTML = `Bed: ${bedsCounter}`;
            $room_beds.appendChild($bed);
            }
        $room.appendChild($room_head);
        $room.appendChild($room_beds);
        $containerRooms.appendChild($room);
    }
    $fragmentRooms.appendChild($containerRooms);
    document.getElementById('rooms').appendChild($fragmentRooms);
}