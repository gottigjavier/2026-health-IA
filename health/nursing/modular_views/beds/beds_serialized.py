from ...utils.dates import dt_serialize


def serial_beds(beds):
    beds_list = []
    if beds:
        for bed in beds:
            pk_id = bed.id
            bed_id = bed.id_bed
            bed_active = bed.active
            bed_occupied_time = dt_serialize(bed.occupied_time)
            bed_planed_vacate = dt_serialize(bed.planed_vacate)
            bed_state = bed.bed_state
            # patient can be None if bed has no patient assigned
            if bed.bed_patient:
                patient = bed.bed_patient.name
                patient_pk = bed.bed_patient.id
                patient_ssn = bed.bed_patient.social_security_number
                image = (
                    bed.bed_patient.image.name
                    if getattr(bed.bed_patient, "image", None)
                    else None
                )
                diagnosis = bed.bed_patient.short_diagnosis
            else:
                patient = None
                patient_pk = None
                patient_ssn = None
                image = None
                diagnosis = None
            done_by = bed.action_done_by
            bed_dict = {
                "id": pk_id,
                "bed_id": bed_id,
                "bed_active": bed_active,
                "bed_occupied_time": bed_occupied_time,
                "bed_planed_vacate": bed_planed_vacate,
                "bed_state": bed_state,
                "patient": patient,
                "patient_id": patient_pk,
                "patient_security_number": patient_ssn,
                "image": image,
                "diagnosis": diagnosis,
                "action_done_by": done_by,
            }
            beds_list.append(bed_dict)
    else:
        pass
    return beds_list
