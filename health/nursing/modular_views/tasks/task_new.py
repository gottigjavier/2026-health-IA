from ...models import Task, Bed
from ..data_analytics import save_event
from datetime import datetime
from dateutil import parser
import json
import random


def modular_new_task(request):
    data = json.loads(request.body)
    bed_id = data["bedId"]
    programed_time = data["programedDT"]
    done_time = data["doneDT"]
    programed_by = data["programer"]
    task_done_by = "Pendiente"
    task_text = data["textAction"]
    task_state = data["state"]
    task_repeat_checked = data["repeatIsChecked"]
    task_repeat_lapse = data["repeatLapse"]
    task_repeat_lapse_unit = data["repeatLapseUnit"]
    task_repeat_until = data["repeatUntil"]
    # Detecta automáticamente si trae segundos o no
    programed_date_time = parser.parse(programed_time)
    programed_time_float = programed_date_time.timestamp()
    task_repeat_id = str(programed_time_float * random.random())
    bed = Bed.objects.get(id=bed_id)
    if task_state == "passed":
        if bed.bed_state == "call" or bed.bed_state == "call-task":
            bed.bed_state = "call-task"
        else:
            bed.bed_state = "task"
    task = Task()
    task.bed = bed
    task.repeat = task_repeat_checked
    task.repeat_id = task_repeat_id
    task.task = task_text if task_text != "" else "Tarea de Rutina"
    task.programed_time = programed_time
    task.done_time = done_time
    task.programed_by = programed_by if programed_by != "" else "Anónimo"
    task.action_done_by = task.programed_by
    task.task_done_by = task_done_by
    task.state = task_state
    task.active = True
    bed.save()
    task.save()
    username = request.user.username
    before = (
        "task.pk: "
        + str(task.pk)
        + "; bed.pk: "
        + str(bed.pk)
        + "; bed_id: "
        + str(bed.id_bed)
        + "; task.repeat: "
        + str(task.repeat)
        + "; task.repeat_id: "
        + str(task.repeat_id)
        + "; task.task: "
        + task.task
        + "; task.programed_time: "
        + str(task.programed_time)
        + "; task.done_time: "
        + str(task.done_time)
        + "; task.active: False; task.state: No State; task.programed_by: "
        + task.programed_by
        + " ; task.task_done_by: "
        + task.task_done_by
        + " ; task.action_done_by: "
        + task.action_done_by
    )
    after = (
        "task.pk: "
        + str(task.pk)
        + "; bed.pk: "
        + str(bed.pk)
        + "; bed_id: "
        + str(bed.id_bed)
        + "; task.repeat: "
        + str(task.repeat)
        + "; task.repeat_id: "
        + str(task.repeat_id)
        + "; task.task: "
        + task.task
        + "; task.programed_time: "
        + str(task.programed_time)
        + "; task.done_time: "
        + str(task.done_time)
        + "; task.active: True; task.state: "
        + str(task.state)
        + "; task.programed_by: "
        + task.programed_by
        + " ; task.task_done_by: "
        + task.task_done_by
        + "; task.action_done_by: "
        + task.action_done_by
    )
    save_event(username, "new task", before, after)
    if task_repeat_checked:
        save_repeated_tasks(
            task_repeat_checked,
            task_repeat_lapse,
            task_repeat_lapse_unit,
            programed_time,
            task_repeat_until,
            bed_id,
            task_repeat_id,
            done_time,
            task.programed_by,
            task.action_done_by,
            task_done_by,
            task.task,
            task_state,
            username,
        )


def save_repeated_tasks(
    task_repeat_checked,
    task_repeat_lapse,
    task_repeat_lapse_unit,
    programed_time,
    task_repeat_until,
    bed_id,
    task_repeat_id,
    done_time,
    programed_by,
    action_done_by,
    task_done_by,
    task_text,
    task_state,
    username,
):
    time_now = datetime.now()
    time_now_float = time_now.timestamp()
    time_factor = int(task_repeat_lapse) * 60  # seconds
    if task_repeat_lapse_unit == "hours":
        time_factor = int(task_repeat_lapse) * 3600  # seconds
    if task_repeat_lapse_unit == "days":
        time_factor = int(task_repeat_lapse) * 86400  # seconds
    # Detecta automáticamente si trae segundos o no
    task_repeat_until_date_time = parser.parse(programed_time)
    task_repeat_until_float = task_repeat_until_date_time.timestamp()
    programed_date_time = parser.parse(programed_time)
    programed_time_float = programed_date_time.timestamp()
    done_date_time = parser.parse(programed_time)
    done_time_float = done_date_time.timestamp()
    task_count = int((task_repeat_until_float - programed_time_float) / time_factor)
    for i in range(1, task_count + 1):
        programed_time_float = programed_time_float + time_factor
        if programed_time_float - time_now_float < 600:
            task_state = "soon"
        else:
            task_state = "later"
        programed_time = datetime.fromtimestamp(programed_time_float)
        done_time_float = done_time_float + time_factor
        done_time = datetime.fromtimestamp(done_time_float)
        bed = Bed.objects.get(id=bed_id)
        task = Task()
        task.bed = bed
        task.repeat = task_repeat_checked
        task.repeat_id = task_repeat_id
        task.task = task_text if task_text != "" else "Tarea de Rutina"
        task.programed_time = programed_time
        task.done_time = done_time
        task.programed_by = programed_by if programed_by != "" else "Anónimo"
        task.action_done_by = task.programed_by
        task.task_done_by = task_done_by
        task.state = task_state
        task.active = True
        bed.save()
        task.save()
        before = (
            "task.pk: "
            + str(task.pk)
            + "; bed.pk: "
            + str(bed.pk)
            + "; bed_id: "
            + str(bed.id_bed)
            + "; task.repeat: "
            + str(task.repeat)
            + "; task.repeat_id: "
            + str(task.repeat_id)
            + "; task.task: "
            + task.task
            + "; task.programed_time: "
            + str(task.programed_time)
            + "; task.done_time: "
            + str(task.done_time)
            + "; task.active: False; task.state: "
            + str(task.state)
            + "; task.programed_by: "
            + task.programed_by
            + " ; task.task_done_by: "
            + task.task_done_by
            + "; task.action_done_by: "
            + task.action_done_by
        )
        after = (
            "task.pk: "
            + str(task.pk)
            + "; bed.pk: "
            + str(bed.pk)
            + "; bed_id: "
            + str(bed.id_bed)
            + "; task.repeat: "
            + str(task.repeat)
            + "; task.repeat_id: "
            + str(task.repeat_id)
            + "; task.task: "
            + task.task
            + "; task.programed_time: "
            + str(task.programed_time)
            + "; task.done_time: "
            + str(task.done_time)
            + "; task.active: True; task.state: "
            + str(task.state)
            + "; task.programed_by: "
            + task.programed_by
            + " ; task.task_done_by: "
            + task.task_done_by
            + "; task.action_done_by: "
            + task.action_done_by
        )
    save_event(username, "new task", before, after)
    return
