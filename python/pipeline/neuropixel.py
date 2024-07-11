""" Schemas for neuropixel recordings."""
import datajoint as dj
from . import experiment, shared

import logging

logger = logging.getLogger(__name__)


schema = dj.schema("pipeline_neuropixel", locals(), create_tables=True)
npx = dj.create_virtual_module('npx', 'neuropixel_ephys')
CURRENT_VERSION = -1


@schema
class Version(dj.Manual):
    definition = """ # versions for the neuropixel pipeline
    -> shared.PipelineVersion
    ---
    description = ''                : varchar(256)      # any notes on this version
    date = CURRENT_TIMESTAMP        : timestamp         # automatic
    """

@schema
class ScanInfo(dj.Manual):
    definition = """ # general data about neuropixel recordings
    -> experiment.Scan
    -> Version                                  # neuropixel version
    ---
    """

@schema
class ScanSet(dj.Computed):
    definition = """ #
    -> ScanInfo
    -> shared.Field
    -> shared.Channel
    -> shared.SegmentationMethod
    """

    class Unit(dj.Part):
        definition = """ # single unit in the scan
        -> master
        -> npx.CuratedClustering.Unit
        """
        
    @property
    def key_source(self):
        return ScanInfo * shared.Field * shared.Channel * shared.SegmentationMethod & {'pipe_version': CURRENT_VERSION} \
               & 'field < 0 and channel < 0 and segmentation_method < 0'
    
    def make(self, key):
        self.insert1(key)
        tup = (ScanInfo * shared.Field * shared.Channel * shared.SegmentationMethod * npx.CuratedClustering.Unit * npx.Session & key).fetch(as_dict=True)
        self.Unit.insert(tup, ignore_extra_fields=True)
        
        
@schema
class ScanDone(dj.Manual):
    definition = """ # neuropixel recordings that are fully processed in the neuropixel_ephys pipeline
    -> ScanInfo
    -> shared.SegmentationMethod
    -> shared.SpikeMethod
    ---
    -> npx.CuratedClustering
    """
    
    def fill(self, curated_clustering_key):
        tup = (npx.Session * npx.CuratedClustering * ScanInfo & curated_clustering_key).fetch1()
        # assert tup['scan_idx'] == tup['insertion_number'], 'scan_idx and insertion_number does not match!'

        if not shared.SegmentationMethod & {'segmentation_method': - tup['paramset_id']}:
            shared.SegmentationMethod.insert1([- tup['paramset_id'], 'neuropixel', 'paramset_id in neuropixel_ephys.ClusteringParamSet for neuropixel spike sorting', 'python'])
        if not shared.SpikeMethod & {'spike_method': - tup['curation_id']}:
            shared.SpikeMethod.insert1([- tup['curation_id'], 'neuropixel', 'curation_id in neuropixel_ephys.Curation for curating clustering results', 'python'])
        tup['segmentation_method'] = - tup['paramset_id']
        tup['spike_method'] = - tup['curation_id']
        
        self.insert1(tup, ignore_extra_fields=True, skip_duplicates=True)
        