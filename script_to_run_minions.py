#!/usr/local/bin/python3
from pipeline import experiment, reso, meso, fuse, stack, pupil, treadmill, posture
from stimulus import stimulus
from stimline import tune

# Scans
for priority in range(120, -130, -10):  # highest to lowest priority
    next_scans = (experiment.AutoProcessing() & 'priority > {}'.format(priority) &
                  (experiment.Scan() & 'scan_ts > "2019-01-01 00:00:00"'))

# next_scans = (experiment.AutoProcessing  &
#               (experiment.Scan & 'scan_ts > "2019-01-01 00:00:00"'))

    # stimulus
    stimulus.Sync.populate(next_scans, reserve_jobs=True, suppress_errors=True)
    stimulus.BehaviorSync.populate(next_scans, reserve_jobs=True, suppress_errors=True)

    # treadmill, pupil, posture
    treadmill.Treadmill.populate(next_scans, reserve_jobs=True, suppress_errors=True)
    pupil.Eye.populate(next_scans, reserve_jobs=True, suppress_errors=True)
    pupil.FittedPupil.populate(next_scans, reserve_jobs=True, suppress_errors=True)
    posture.Posture.populate(next_scans, reserve_jobs=True, suppress_errors=True)

    # stack
    stack.StackInfo.populate(stack.CorrectionChannel, reserve_jobs=True, suppress_errors=True)
    stack.Quality.populate(reserve_jobs=True, suppress_errors=True)
    stack.RasterCorrection.populate(reserve_jobs=True, suppress_errors=True)
    stack.MotionCorrection.populate(reserve_jobs=True, suppress_errors=True)
    stack.Stitching.populate(reserve_jobs=True, suppress_errors=True)
    stack.CorrectedStack.populate(reserve_jobs=True, suppress_errors=True)

    # reso/meso
    for pipe in [reso, meso]:
        pipe.ScanInfo.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.Quality.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.RasterCorrection.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.MotionCorrection.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.SummaryImages.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.Segmentation.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.Fluorescence.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.MaskClassification.populate(next_scans, {'classification_method': 2},
                                        reserve_jobs=True, suppress_errors=True)
        pipe.ScanSet.populate(next_scans, reserve_jobs=True, suppress_errors=True)
        pipe.Activity.populate(next_scans, {'spike_method': 5}, reserve_jobs=True,
                            suppress_errors=True)
        full_scans = (pipe.ScanInfo.proj() & pipe.Activity) - (pipe.ScanInfo.Field -
                                                            pipe.Activity)
        pipe.ScanDone.populate(full_scans & next_scans, reserve_jobs=True,
                            suppress_errors=True)