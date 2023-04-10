from pipeline import stack
import datajoint as dj
# data_schemas = dj.create_virtual_module('neurodata_static', 'neurodata_static')
# analyses = dj.create_virtual_module('neurostatic_pilot_analyses', 'neurostatic_pilot_analyses')

# groups = [233, 237, 239, 243, 271, 272, 273, 275, 279, 284, 285]
# mei_keys = stack.Registration * analyses.DEIClosedLoopSummaryResults.proj(scan_session = 'session') & 'scan_session = stack_session'
# imagenet_keys = stack.Registration * (data_schemas.StaticMultiDatasetGroupAssignment() & [{'group_id':g} for g in groups]).proj(scan_session = 'session') & 'scan_session = stack_session'
# stack.RegistrationOverTime.populate([mei_keys, imagenet_keys], reserve_jobs=True, order='random')

keys = (meso.ScanDone & (collection.CuratedScan & 'study_name LIKE "%%dei_v1%%" and animal_id = 29513 and scan_purpose in ("imagenet", "dei_texture_package")')).fetch(as_dict=True)
stack.RegistrationOverTime.populate(keys, reserve_jobs=True, order='random')

# stack_keys = [{'animal_id': 27468, 'stack_session': 13, 'stack_idx': 19},
#               {'animal_id': 27468, 'stack_session': 14, 'stack_idx': 11},
#               {'animal_id': 27802, 'stack_session': 3, 'stack_idx': 21},]
# stack.StackSet.populate(stack_keys, reserve_jobs=True)