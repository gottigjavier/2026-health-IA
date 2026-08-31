from ...models import Bed, Task
from ...choices import BedState, TaskState
from ..data_analytics import save_event
import json


def modular_edit_task(request):
    data = json.loads(request.body)
    task_id = data["taskId"]
    task = Task.objects.get(id=task_id)
    before = (
        "task.pk: "
        + str(task.pk)
        + "; bed.pk: "
        + str(task.bed.pk)
        + "; bed_id: "
        + str(task.bed.id_bed)
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
        + "; task.active: "
        + str(task.active)
        + "; task.state: "
        + str(task.state)
        + "; task.programed_by: "
        + task.programed_by
        + " ; task.task_done_by: "
        + task.task_done_by
        + "; task.action_done_by: "
        + task.action_done_by
    )
    current_bed = data["currentBed"]
    task_state = data["state"]
    if task_state not in TaskState.values:
        raise ValueError(f"Invalid task state: {task_state!r}")
    task_active = data["active"]
    task.programed_time = data["programedDT"]
    task.done_time = data["doneDT"]
    task.programed_by = data["programer"]
    task.task_done_by = data["maker"]
    task.action_done_by = data["editor"]
    task.task = data["textAction"]
    task.state = task_state
    task.active = task_active
    bed_task_list = Task.objects.filter(
        bed__id_bed=current_bed, active=True, state=TaskState.PASSED
    )
    edit_task_bed_color(task, bed_task_list, task_state, task_active)
    task.save()
    after = (
        "task.pk: "
        + str(task.pk)
        + "; bed.pk: "
        + str(task.bed.pk)
        + "; bed_id: "
        + str(task.bed.id_bed)
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
        + "; task.active: "
        + str(task.active)
        + "; task.state: "
        + str(task.state)
        + "; task.programed_by: "
        + task.programed_by
        + " ; task.task_done_by: "
        + task.task_done_by
        + "; task.action_done_by: "
        + task.action_done_by
    )
    save_event(request.user.username, "edit task", before, after)


# ----------------------------------------------------------------------------
def edit_task_bed_color(task, bed_task_list, task_state, task_active):
    if len(bed_task_list) == 1:
        bed = Bed.objects.get(id=task.bed.pk)
        if bed_task_list[0].id == task.pk:
            if not task_active:
                if bed.bed_state == BedState.CALL_TASK:
                    bed.bed_state = BedState.CALL
                else:
                    bed.bed_state = BedState.OCCUPIED
            else:
                if task_state != TaskState.PASSED:
                    if bed.bed_state == BedState.CALL_TASK or bed.bed_state == BedState.CALL:
                        bed.bed_state = BedState.CALL
                    else:
                        bed.bed_state = BedState.OCCUPIED
        bed.save()
    if len(bed_task_list) == 0:
        bed = Bed.objects.get(id=task.bed.pk)
        if task_active and task_state == TaskState.PASSED:
            if bed.bed_state == BedState.CALL:
                bed.bed_state = BedState.CALL_TASK
            else:
                bed.bed_state = BedState.TASK
        bed.save()


# ----------------------------------------------------------------------------
