from pipeline import pupil
key = dict(animal_id=29189, session=16, scan_idx=1)
pupil.Tracking.populate(key, 'tracking_method = 2', reserve_jobs=True)
pupil.FittedPupil.populate(key, reserve_jobs=True)