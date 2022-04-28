# from pipeline import stack

# stack_key = [{'animal_id': 26897, 'stack_session': 2, 'stack_idx': 1},
#             {'animal_id': 27393, 'stack_session': 2, 'stack_idx': 7},
#             {'animal_id': 27393, 'stack_session': 1, 'stack_idx': 28},
#             ]
# stack.Segmentation.populate(stack_key, reserve_jobs=True)

from pipeline import stack
import datajoint as dj
data_schemas = dj.create_virtual_module('neurodata_static', 'neurodata_static')
analyses = dj.create_virtual_module('neurostatic_pilot_analyses', 'neurostatic_pilot_analyses')

mei_keys = stack.Registration * analyses.DEIClosedLoopSummaryResults.proj(scan_session = 'session') & 'scan_session = stack_session'
imagenet_keys = stack.Registration * (data_schemas.StaticMultiDatasetGroupAssignment() & 'group_id in (233, 237, 239, 241, 243)').proj(scan_session = 'session') & 'scan_session = stack_session'
stack.RegistrationOverTime.populate([mei_keys, imagenet_keys], reserve_jobs=True, order='random')