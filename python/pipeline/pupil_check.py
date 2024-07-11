import datajoint as dj
import streamlit as st
import cv2
from matplotlib import pyplot as plt
from matplotlib.patches import Circle
from stimulus import stimulus
from pipeline import meso, reso, experiment, pupil, treadmill, fuse
import numpy as np
from scipy import interpolate

subset = dj.create_virtual_module('pipeline_subset', 'pipeline_subset')
# dv_scan = dj.create_virtual_module('dv_datasets_v1_scan', 'dv_datasets_v1_scan')

# helper functions

@st.cache(allow_output_mutation=True)
def fetch_pupil(key):
    '''Return pupil center, pupil radius, pupil video and a function to interpolate from behavior times to pupil trace idx
    '''
    scan_filenames = (experiment.Scan & key).local_filenames_as_wildcard
    pupil_video_file = scan_filenames.split('*')[0] + "_beh.avi"
    pupil_video = cv2.VideoCapture(pupil_video_file)
    pupil_radii, pupil_centers = (pupil.FittedPupil.Circle & key & 'tracking_method=2').fetch('radius','center', 
                                                                            order_by='frame_id ASC')
    pupil_centers = np.array([p if p is not None else np.array([np.nan, np.nan]) for p in pupil_centers])
    pupil_center_x = pupil_centers[:, 0]
    pupil_center_y = pupil_centers[:, 1]

    # pupil centers stored in the FittedPupil table is the location of the pupil center in the cropped eye video, recover the original position
    crop_x0, crop_y0 = (pupil.Tracking.Deeplabcut & key).fetch1('cropped_x0', 'cropped_y0')
    pupil_center_x = pupil_center_x + crop_x0
    pupil_center_y = pupil_center_y + crop_y0

    eye_time = (pupil.Eye & key).fetch1('eye_time')
    beh_time2pupil_idx_float = interpolate.interp1d(eye_time, np.arange(len(pupil_radii)))
    # beh_time2pupil_idx = lambda x : int(np.round(beh_time2pupil_idx_float(x)))  # turn the interpolated value to an int
    beh_time2pupil_idx = lambda x : int(np.round(beh_time2pupil_idx_float(x)))  # turn the interpolated value to an int

    return pupil_center_x, pupil_center_y, pupil_radii, pupil_video, beh_time2pupil_idx

@st.cache(allow_output_mutation=True)
def fetch_intensity(key):
    # the following code is borrowed from pipeline/python/stimline/subset
    # Mean intensity per volume
    pipe = (fuse.ScanSet() & key).module
    mean_intensities_per_field = (pipe.Quality.MeanIntensity() & key).fetch('intensities')
    mean_intensities_per_volume = mean_intensities_per_field.mean(0)

    # get number of depths in each scan
    num_depths = len(np.unique((pipe.ScanInfo.Field & key).fetch('z')))

    # Getting depth times in behavior clock
    depth_times_in_beh = (stimulus.BehaviorSync() & key).fetch1('frame_times').squeeze()[::num_depths]
    residual_frames = len(depth_times_in_beh) % num_depths # remove the frames that are not completed for all depths
    if residual_frames != 0:
        depth_times_in_beh = depth_times_in_beh[:-residual_frames]
    depth_times_in_beh = depth_times_in_beh[:np.min((len(depth_times_in_beh), len(mean_intensities_per_volume)))]
    mean_intensities_per_volume = mean_intensities_per_volume[:np.min((len(depth_times_in_beh), len(mean_intensities_per_volume)))]

    beh_time2intensity_idx_float = interpolate.interp1d(depth_times_in_beh, np.arange(len(mean_intensities_per_volume)))
    beh_time2intensity_idx = lambda x : int(np.round(beh_time2intensity_idx_float(x)))
    return mean_intensities_per_volume, beh_time2intensity_idx

@st.cache(allow_output_mutation=True)
def fetch_treadmill(key):
    treadmill_time, treadmill_vel = (treadmill.Treadmill & key).fetch1('treadmill_time', 'treadmill_vel')
    beh_time2treadmill_idx_float = interpolate.interp1d(treadmill_time, np.arange(len(treadmill_vel)))
    beh_time2treadmill_idx = lambda x : int(np.round(beh_time2treadmill_idx_float(x)))
    return treadmill_vel, beh_time2treadmill_idx

@st.cache(allow_output_mutation=True)
def get_interpolators(key):
    num_depths = len(np.unique((meso.ScanInfo.Field & key).fetch('z')))
    depth_times_in_beh = (stimulus.BehaviorSync() & key).fetch1('frame_times').squeeze()
    residual_frames = len(depth_times_in_beh) % num_depths # remove the frames that are not completed for all depths
    if residual_frames != 0:
        depth_times_in_beh = depth_times_in_beh[:-residual_frames]
    depth_times_in_stim = (stimulus.Sync() & key).fetch1('frame_times').squeeze()
    residual_frames = len(depth_times_in_stim) % num_depths # remove the frames that are not completed for all depths
    if residual_frames != 0:
        depth_times_in_stim = depth_times_in_stim[:-residual_frames]
    stim2beh = interpolate.interp1d(depth_times_in_stim, depth_times_in_beh, kind='linear') # stimulus clock to behavior sync
    trial_times_stim = [i[0][0] for i in (stimulus.Trial & key).fetch('flip_times', order_by='trial_idx ASC')]  # trial times in stimuls clock
    trial_times_stim.append((stimulus.Trial & key).fetch('flip_times', limit=1, order_by='trial_idx DESC')[0][0,-1])
    trial_idx = list((stimulus.Trial & key).fetch('trial_idx', order_by='trial_idx ASC'))
    trial_idx.append(trial_idx[-1] + 1)  # add one hypothetical trial at the end to mark the end of the scan
    trial_times_beh = stim2beh(trial_times_stim)
    beh_time2trial_idx = interpolate.interp1d(trial_times_beh, np.array(trial_idx), kind='linear')
    beh_time2trial_idx_1 = lambda x : beh_time2trial_idx(np.array([x]))[0]
    trial_idx2beh_time = interpolate.interp1d(np.array(trial_idx), trial_times_beh, kind='linear')
    trial_idx2beh_time_1 = lambda x : trial_idx2beh_time(np.array([x]))[0]
    return stim2beh, beh_time2trial_idx_1, trial_idx2beh_time_1

def main():

    # layout
    plots_container = st.beta_container()

    # ask for scan key
    with st.sidebar:
        animal_id = int(st.number_input('animal_id', value=17797))
        session = int(st.number_input('session', value=4))
        scan_idx = int(st.number_input('scan_idx', value=7))
    single_scan_key = dict(animal_id=animal_id, session=session, scan_idx=scan_idx)
    pipe = (fuse.ScanSet & single_scan_key).module
    if len(pipe.ScanInfo & single_scan_key) != 1:
        raise Exception('WARNING: Key does not specify a single entry.')

    # fetch data
    pupil_center_x, pupil_center_y, pupil_radii, pupil_video, beh_time2pupil_idx = fetch_pupil(single_scan_key)
    mean_intensity, beh_time2intensity_idx = fetch_intensity(single_scan_key)
    treadmill_vel, beh_time2treadmill_idx = fetch_treadmill(single_scan_key)
    stim2beh, beh_time2trial_idx_1, trial_idx2beh_time_1 = get_interpolators(single_scan_key)
    n_trials = len(stimulus.Trial & single_scan_key)
    beh_time_0 = stim2beh((stimulus.Trial & single_scan_key & 'trial_idx=0').fetch1('flip_times')[0])[0]
    beh_time_finish = stim2beh((stimulus.Trial & single_scan_key).fetch('flip_times', order_by='trial_idx DESC')[0][0])[-1]

    # interactive part
    with st.sidebar:
        beh_time_window = float(st.number_input('Trace window (behavior sec):', min_value=1., max_value=1000., value=10.))

        # use time as input
        # beh_time_center = st.number_input(
        #     'Time (behavior sec):', 
        #     min_value=beh_time_window / 2, 
        #     max_value=beh_time_finish - beh_time_window / 2, 
        #     value=beh_time_window / 2, 
        #     step=1.
        # ) + beh_time_0

        # use trial_idx as input
        beh_time_center = trial_idx2beh_time_1(st.number_input(
            'Trial_idx: ',
            0.0,
            n_trials * 1.0,
            value=0.0,
            step=.1
        ))

        st_trial_num = st.markdown(f'Trial: {beh_time2trial_idx_1(beh_time_center):.2f}')
        trial_length = (stimulus.Trial & single_scan_key & {'trial_idx': int(beh_time2trial_idx_1(beh_time_center))}).fetch1('flip_times')[0]
        trial_length = trial_length[-1] - trial_length[0]
        st_trial_length = st.markdown(f'Trial length (sec): {trial_length:.1f}')


    beh_time_start = beh_time_center - beh_time_window / 2
    beh_time_end = beh_time_center + beh_time_window / 2

    # plot pupil frame
    pupil_frame_fig, pupil_frame_ax = plt.subplots()
    plt.axis('off')
    pupil_frame_idx = beh_time2pupil_idx(np.array([beh_time_center]))
    pupil_video.set(1, pupil_frame_idx)
    ret, pupil_frame = pupil_video.read()
    pupil_frame_ax.imshow(pupil_frame)

    if pupil_center_x[pupil_frame_idx] is not None:
        pupil_circ = Circle(
            [pupil_center_x[pupil_frame_idx], pupil_center_y[pupil_frame_idx]],
            pupil_radii[pupil_frame_idx],
            edgecolor='yellow', 
            facecolor=None, 
            fill=False
        )
        pupil_frame_ax.add_patch(pupil_circ)
        reference_zero = Circle(
            [0, 0],
            100,
            edgecolor='red', 
            facecolor=None, 
            fill=False
        )
        pupil_frame_ax.add_patch(reference_zero)
    plt.title(f'Eye video frame\npupil_x: {pupil_center_x[pupil_frame_idx]:.2f}\npupil_y: {pupil_center_y[pupil_frame_idx]:.2f}')
    with plots_container:
        st.pyplot(pupil_frame_fig)
    
    # plot pupil trace
    pupil_trace_fig, pupil_trace_ax = plt.subplots(figsize=[12,2])
    pupil_trace_start = beh_time2pupil_idx(np.array([beh_time_start]))
    pupil_trace_end = beh_time2pupil_idx(np.array([beh_time_end]))
    pupil_trace_ax.plot(
        np.linspace(beh_time_start - beh_time_0, beh_time_end - beh_time_0, pupil_trace_end - pupil_trace_start),
        pupil_radii[pupil_trace_start:pupil_trace_end]
    )
    pupil_trace_ax.axvline(x=beh_time_center - beh_time_0, color='black')
    plt.title('Pupil radius')
    with plots_container:
        st.pyplot(pupil_trace_fig)

    # plot intensity traces
    intensity_trace_fig, intensity_trace_ax = plt.subplots(figsize=[12,2])
    intensity_trace_center = beh_time2intensity_idx(np.array([beh_time_center]))
    intensity_trace_start = beh_time2intensity_idx(np.array([beh_time_start]))
    intensity_trace_end = beh_time2intensity_idx(np.array([beh_time_end]))
    intensity_trace_ax.plot(
        np.linspace(beh_time_start - beh_time_0, beh_time_end - beh_time_0, intensity_trace_end - intensity_trace_start),
        mean_intensity[intensity_trace_start:intensity_trace_end]
    )
    intensity_trace_ax.axvline(x=beh_time_center - beh_time_0, color='black')
    plt.title('Mean intensity')
    with plots_container:
        st.pyplot(intensity_trace_fig)

    # plot treadmill traces
    treadmill_trace_fig, treadmill_trace_ax = plt.subplots(figsize=[12,2])
    treadmill_trace_center = beh_time2treadmill_idx(np.array([beh_time_center]))
    treadmill_trace_start = beh_time2treadmill_idx(np.array([beh_time_start]))
    treadmill_trace_end = beh_time2treadmill_idx(np.array([beh_time_end]))
    treadmill_trace_ax.plot(
        np.linspace(beh_time_start - beh_time_0, beh_time_end - beh_time_0, treadmill_trace_end - treadmill_trace_start),
        treadmill_vel[treadmill_trace_start:treadmill_trace_end]
    )
    treadmill_trace_ax.axvline(x=beh_time_center - beh_time_0, color='black')
    plt.title('Treadmill velocity')
    plt.xlabel('Behavior sec')
    with plots_container:
        st.pyplot(treadmill_trace_fig)
    
    # plot pupil x,y
    pupil

if __name__ == "__main__":
    main()