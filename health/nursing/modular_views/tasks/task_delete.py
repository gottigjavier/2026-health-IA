import json
from ..data_analytics import save_event
from ...models import Task, Bed
from ...choices import BedState, TaskState


# -------------------------------------------------------------------------
def modular_delete_task(request):
    data = json.loads(request.body)
    task_pk = data["taskPk"]
    current_bed = data["currentBed"]
    task_is_repeat = data["repeatIsChecked"]
    task_repeat_id = data["reapeatTasksId"]
    if not task_is_repeat:
        delete_task_no_repeated(request, task_pk, current_bed)
    else:
        delete_task_repeated(request, task_repeat_id, current_bed)


def delete_task_no_repeated(request, task_pk, current_bed):
    task = Task.objects.get(pk=task_pk)
    bed_task_list = Task.objects.filter(
        bed__id_bed=current_bed, active=True, state=TaskState.PASSED
    )
    if not len(bed_task_list) > 1:
        bed = Bed.objects.get(id=task.bed.pk)
        if bed.bed_state == BedState.CALL_TASK or bed.bed_state == BedState.CALL:
            bed.bed_state = BedState.CALL
        else:
            bed.bed_state = BedState.OCCUPIED
        bed.save()
    task.delete()
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
        + "; task.active: True; task.state: "
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
        + "; task.active: False; task.state: "
        + str(task.state)
        + "; task.programed_by: "
        + task.programed_by
        + " ; task.task_done_by: "
        + task.task_done_by
        + "; task.action_done_by: "
        + task.action_done_by
    )
    save_event(request.user.username, "delete task", before, after)


# -------------------------------------------------------------------------


def delete_task_repeated(request, task_repeat_id, current_bed):
    tasks = Task.objects.filter(repeat_id=task_repeat_id, active=True)
    for task in tasks:
        bed_task_list = Task.objects.filter(
            bed__id_bed=current_bed, active=True, state=TaskState.PASSED
        )
        if len(bed_task_list) == 1:
            bed = Bed.objects.get(id=task.bed.pk)
            if task.pk == bed_task_list[0].id:
                if bed.bed_state == BedState.CALL_TASK or bed.bed_state == BedState.CALL:
                    bed.bed_state = BedState.CALL
                else:
                    bed.bed_state = BedState.OCCUPIED
                bed.save()
        task.delete()
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
            + "; task.active: True; task.state: "
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
            + "; task.active: False; task.state: "
            + str(task.state)
            + "; task.programed_by: "
            + task.programed_by
            + " ; task.task_done_by: "
            + task.task_done_by
            + "; task.action_done_by: "
            + task.action_done_by
        )
        save_event(request.user.username, "delete task", before, after)
        


# -------------------------------------------------------------------------------------
