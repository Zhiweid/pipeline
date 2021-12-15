from pipeline import pupil
key = dict(animal_id=26645, session=2, scan_idx=18)
pupil.Tracking.populate(key, 'tracking_method = 2', reserve_jobs=True)
pupil.FittedPupil.populate(key, reserve_jobs=True)