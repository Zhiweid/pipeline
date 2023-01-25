from pipeline import stack, meso

ls = [#dict(stack_keys = [{'animal_id': 27393, 'stack_session': 1, 'stack_idx': 28},
#                         {'animal_id': 27393, 'stack_session': 2, 'stack_idx': 7},],
#            scan_keys = [{'animal_id': 27393, 'session': 1, 'scan_idx': 25},
#                         {'animal_id': 27393, 'session': 1, 'scan_idx': 26}]),
#       dict(stack_keys = [{'animal_id': 27578, 'stack_session': 1, 'stack_idx': 8},
#                         {'animal_id': 27578, 'stack_session': 2, 'stack_idx': 2},],
#             scan_keys = [{'animal_id': 27578, 'session': 1, 'scan_idx': 5},
#                         {'animal_id': 27578, 'session': 1, 'scan_idx': 6},
#                         #{'animal_id': 27578, 'session': 1, 'scan_idx': 14},
#                         ]),
#     dict(stack_keys = [{'animal_id': 27816, 'stack_session': 1, 'stack_idx': 12},
#                         {'animal_id': 27816, 'stack_session': 2, 'stack_idx': 2},],
#             scan_keys = [{'animal_id': 27816, 'session': 1, 'scan_idx': 8},
#                         {'animal_id': 27816, 'session': 1, 'scan_idx': 10}]),
#     dict(stack_keys = [{'animal_id': 27679, 'stack_session': 1, 'stack_idx': 7},
#                         {'animal_id': 27679, 'stack_session': 2, 'stack_idx': 2},],
#             scan_keys = [{'animal_id': 27679, 'session': 1, 'scan_idx': 5},
#                         {'animal_id': 27679, 'session': 1, 'scan_idx': 10}]),
    dict(stack_keys = [{'animal_id': 28382, 'stack_session': 1, 'stack_idx': 13},
                        {'animal_id': 28382, 'stack_session': 2, 'stack_idx': 1},],
            scan_keys = [{'animal_id': 28382, 'session': 1, 'scan_idx': 11},
                        {'animal_id': 28382, 'session': 1, 'scan_idx': 12}]),
                        ]

for dic in ls:
    stack_keys = dic['stack_keys']
    scan_keys = dic['scan_keys']

    for stack_key in stack_keys:
        for scan_key in scan_keys:
            stack.RegistrationTask().fill(stack_key, scan_key)

    stack.PreprocessedStack().populate(stack.RegistrationTask().proj(
        session='stack_session', channel='stack_channel'), reserve_jobs=True,
        suppress_errors=True)
    stack.Registration().populate(stack_keys, scan_keys, reserve_jobs=True)        
    meso.StackCoordinates.populate(scan_keys, reserve_jobs=True)

    stack.SegmentationTask().fill(stack_keys)
    stack.Segmentation.populate(stack_keys, reserve_jobs=True)
    stack.FieldSegmentation.populate(stack_keys, reserve_jobs=True)
    stack.FieldSegmentation.populate(stack_keys, reserve_jobs=True)
    meso.Func2StructMatching.populate(stack_keys, scan_keys, reserve_jobs=True)