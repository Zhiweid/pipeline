from pipeline import treadmill
keys = [{'animal_id': 29189, 'session': 16, 'scan_idx': 1},
        {'animal_id': 28489, 'session': 20, 'scan_idx': 1}]
treadmill.Treadmill.populate(keys, reserve_jobs=True)
