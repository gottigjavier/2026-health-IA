export function formattingDateTime(format='d-m-y', propDateTime){
    if (!propDateTime) return '';
    const dateTimeData = propDateTime;
    let dateTime;
    if(typeof(dateTimeData) === 'object'){
        const year = dateTimeData.getFullYear();
        let mnth = dateTimeData.getMonth() +1;
        if (mnth > 12){ mnth = 1 }
        const month = addZero(mnth);
        const dte = dateTimeData.getDate();
        const date = addZero(dte);
        const hrs = dateTimeData.getHours();
        const hours = addZero(hrs);
        const mints = dateTimeData.getMinutes();
        const minutes = addZero(mints);
        const scnds = dateTimeData.getSeconds()
        const seconds = addZero(scnds);
        if(format === 'd-m-y'){
            dateTime = date + '-' + month + '-' + year + ' ' + hours + ':' + minutes + ':' + seconds;
        }
        else if(format === 'y-m-d'){
            dateTime = year + '-' + month + '-' + date + ' ' + hours + ':' + minutes + ':' + seconds;
        }
        else if(format === 'd/m/y'){
            dateTime = date + '/' + month + '/' + year + ' ' + hours + ':' + minutes + ':' + seconds;
        }
        else if(format === 'y/m/d'){
            dateTime = year + '/' + month + '/' + date + ' ' + hours + ':' + minutes + ':' + seconds;
        }
        else {
            dateTime = dateTimeData.toLocaleString('es-AR')
        }
    }
    else if (typeof(dateTimeData) === 'string'){
        if(format === 'y-m-d'){
            dateTime = dateTimeNoReverseHyphen(dateTimeData)
        } else if(format === 'd-m-y'){
            dateTime = dateTimeReverseHyphen(dateTimeData)
        }
        else {
            dateTime = dateTimeData
        }
    }
    return dateTime
}

export function formattingDate(format='d-m-y', propDate){
    if (!propDate) return '';
    const dateData = propDate;
    let exitDate;
    if(typeof(dateData) === 'object'){
        const year = dateData.getFullYear();
        let mnth = dateData.getMonth() + 1;
        if (mnth > 12){ mnth = 1 } 
        const month = addZero(mnth);
        const dte = dateData.getDate();
        const date = addZero(dte);
        if(format === 'd-m-y'){
            exitDate = date + '-' + month + '-' + year;
        }
        else if(format === 'y-m-d'){
            exitDate = year + '-' + month + '-' + date;
        }
        else if(format === 'd/m/y'){
            exitDate = date + '/' + month + '/' + year;
        }
        else if(format === 'y/m/d'){
            exitDate = year + '/' + month + '/' + date;
        }
        else if(format === 'd-m-y:short'){
            const shortYear = year.slice(2);
            exitDate = date + '-' + month + '-' + shortYear;
        }
        else if(format === 'y-m-d:short'){
            const shortYear = year.slice(2);
            exitDate = shortYear + '-' + month + '-' + date;
        }
        else if(format === 'd/m/y:short'){
            const shortYear = year.slice(2);
            exitDate = date + '/' + month + '/' + shortYear;
        }
        else if(format === 'y/m/d:short'){
            const shortYear = year.slice(2);
            exitDate = shortYear + '/' + month + '/' + date;
        }
        else {
            exitDate = dateData.toLocaleString('es-AR').split(' ')[0]
        }
    }
    if (typeof(dateData) === 'string'){
        if(format === 'y-m-d'){
            exitDate = dateTimeNoReverseHyphen(dateData).split(' ')[0]
        } else if(format === 'd-m-y'){
            exitDate = dateTimeReverseHyphen(dateData).split(' ')[0]
        }
        else if(format === 'y-m-d:short'){
            const fullDate = dateTimeNoReverseHyphen(dateData).split(' ')[0]
            exitDate = fullDate.slice(5)
        } else if(format === 'd-m-y:short'){
            const fullDate = dateTimeReverseHyphen(dateData).split(' ')[0]
            exitDate = fullDate.slice(0,5)
        }
        else {
            exitDate = dateData
        }
    }
    return exitDate
}

export function formattingTime(format='h:m:s', propTime){
    if (!propTime) return '';
    const timeData = propTime;
    let exitTime;
    if(typeof(timeData) === 'object'){
        const hrs = timeData.getHours();
        const hours = addZero(hrs);
        const mints = timeData.getMinutes();
        const minutes = addZero(mints);
        const scnds = timeData.getSeconds()
        const seconds = addZero(scnds);
        if(format === 'h:m:s'){
            exitTime = hours + ':' + minutes + ':' + seconds;
        }
        else if(format === 'h:m'){
            exitTime = hours + ':' + minutes;
        }
    }
    else if (typeof(timeData) === 'string'){
        if(format === 'h:m:s'){
            exitTime = dateTimeNoReverseHyphen(timeData).split(' ')[1]
        } else if(format === 'h:m'){
            const hMSStr = dateTimeNoReverseHyphen(timeData).split(' ')[1]
            const hoursStr = hMSStr.split(':')[0]
            const minutesStr = hMSStr.split(':')[1]
            exitTime = hoursStr + ':' + minutesStr;
        }
        else {
            exitTime = timeData
        }
    }
    return exitTime
}


function addZero(date){
    let strDate = date.toString()
    if(strDate.length < 2){
        strDate = '0' + strDate
    }
    return strDate
}

function dateTimeReverseHyphen(dateTimeData){
    // datetime.toLocaleString() format from new Date js: dd-mm-yyyy HH:MM:SS
    // datetime.toLocaleString() format from backend: yyyy-mm-ddTHH:MM:SS.fff
    // return dd-mm-yyyy HH:MM:SS 

    const localeDateTimeData = dateTimeData.toLocaleString('es-AR');
    const dateTimeFormat = () => {
        try {
            return {'date': localeDateTimeData.split('T')[0].split('-').reverse().join('-'), 'time': localeDateTimeData.split('T')[1].split('.')[0]};
        } 
        catch {
            return {'date': localeDateTimeData.split(' ')[0], 'time': localeDateTimeData.split(' ')[1]}
        }
    }
    const formatedDateTime = `${dateTimeFormat().date} ${dateTimeFormat().time}`
    return formatedDateTime
}

function dateTimeNoReverseHyphen(dateTimeData){
    // datetime.toLocaleString() format from new Date js: dd-mm-yyyy HH:MM:SS
    // datetime.toLocaleString() format from backend: yyyy-mm-ddTHH:MM:SS.fff
    // return dd-mm-yyyy HH:MM:SS 
    
    const localeDateTimeData = dateTimeData.toLocaleString('es-AR');
    const dateTimeFormat = () => {
        try {
            return {'date': localeDateTimeData.split('T')[0].split('-').join('-'), 'time': localeDateTimeData.split('T')[1].split('.')[0]};
        } 
        catch {
            return {'date': localeDateTimeData.split(' ')[0], 'time': localeDateTimeData.split(' ')[1]}
        }
    }
    const formatedDateTime = `${dateTimeFormat().date} ${dateTimeFormat().time}`
    return formatedDateTime
}