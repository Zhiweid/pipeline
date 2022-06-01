from pipeline import stack
import datajoint as dj
data_schemas = dj.create_virtual_module('neurodata_static', 'neurodata_static')
analyses = dj.create_virtual_module('neurostatic_pilot_analyses', 'neurostatic_pilot_analyses')

mei_keys = stack.Registration * analyses.DEIClosedLoopSummaryResults.proj(scan_session = 'session') & 'scan_session = stack_session'
imagenet_keys = stack.Registration * (data_schemas.StaticMultiDatasetGroupAssignment() & 'group_id in (233, 237, 239, 243, 271, 272)').proj(scan_session = 'session') & 'scan_session = stack_session'
stack.RegistrationOverTime.populate([mei_keys, imagenet_keys], reserve_jobs=True, order='random')