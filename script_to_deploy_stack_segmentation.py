from pipeline import stack

stack_key = [{'animal_id': 26897, 'stack_session': 2, 'stack_idx': 1},
            {'animal_id': 27393, 'stack_session': 2, 'stack_idx': 7},
            {'animal_id': 27393, 'stack_session': 1, 'stack_idx': 28},
            ]
stack.Segmentation.populate(stack_key, reserve_jobs=True)