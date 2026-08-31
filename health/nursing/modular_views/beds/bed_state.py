from ...models import Call, Task
from ...choices import BedState, CallState, TaskState


def compute_bed_state(*, has_active_call, has_passed, has_soon, has_later) -> str:
    """Deduce the bed_state from the bed's task/call flags.

    Pure function (no DB access) so it can be tested in isolation.

    Business semantics:
      - active call + passed task      -> "call-task"
      - active call, otherwise          -> "call"
      - no call + passed task           -> "task"
      - no call + soon task             -> "soon"
      - no call + later task            -> "later"
      - no call, no relevant task       -> "occupied"

    Callers that should NOT consider "later" (e.g. after deleting/answering
    a task/call) simply pass ``has_later=False``.
    """
    if has_active_call:
        return BedState.CALL_TASK if has_passed else BedState.CALL
    if has_passed:
        return BedState.TASK
    if has_soon:
        return BedState.SOON
    if has_later:
        return BedState.LATER
    return BedState.OCCUPIED


def refresh_bed_state(
    bed, *, consider_later=True, has_active_call=None
) -> str | None:
    """Recompute a bed's state from its active tasks/calls and persist it.

    Returns the new bed_state, or None when ``bed`` is falsy/inactive (in
    which case nothing is changed).

    - ``consider_later``: when False a "later" task is not enough to mark the
      bed as "later" (used after deleting/answering, mirroring the original
      per-context behaviour).
    - ``has_active_call``: explicit value (e.g. False right after answering a
      call) or None to query for an active call.
    """
    if not bed or not bed.active:
        return None

    tasks = Task.objects.filter(bed=bed, active=True)
    flags = {
        "has_passed": tasks.filter(state=TaskState.PASSED).exists(),
        "has_soon": tasks.filter(state=TaskState.SOON).exists(),
        "has_later": bool(consider_later) and tasks.filter(state=TaskState.LATER).exists(),
        "has_active_call": (
            Call.objects.filter(bed=bed, state=CallState.ACTIVE).exists()
            if has_active_call is None
            else bool(has_active_call)
        ),
    }
    bed.bed_state = compute_bed_state(**flags)
    bed.save()
    return bed.bed_state
