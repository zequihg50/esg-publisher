from esgcet.mk_dataset_autoc import ESGPubMakeAutocDataset
from esgcet.mk_dataset_xarray import ESGPubMakeXArrayDataset
import json, os, sys
import tempfile
from esgcet.generic_pub import BasePublisher
import traceback
import esgcet.logger as logger
import xarray

log = logger.Logger()

class GenericPublisher(BasePublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name

    def __init__(self, argdict):
        super().__init__(argdict)
        
#        if argdict["autoc_command"]:
#            self.autoc_command = argdict["autoc_command"]
#            self.MKD_Construct = ESGPubMakeAutocDataset
#        else:
        self.autoc_command = None
        self.MKD_Construct = ESGPubMakeXArrayDataset
    
        self.publog = log.return_logger('Generic NetCDF Publisher', self.silent, self.verbose)

    def cleanup(self):
        self.scan_file.close()

    def xarray_load(self, map_json_data):
        datafile = map_json_data[0][1]
        destpath = os.path.dirname(datafile)

        filespec = f"{destpath}/*.nc"

        self.xarray_set = xarray.open_mfdataset(filespec)

    def autocurator(self, map_json_data):
        datafile = map_json_data[0][1]

        destpath = os.path.dirname(datafile)
        outname = os.path.basename(datafile)
        idx = outname.rfind('.')

        autstr = self.autoc_command + ' --out_pretty --out_json {} --files "{}/*.nc"'
        stat = os.system(autstr.format(self.scanfn, destpath))
        if os.WEXITSTATUS(stat) != 0:
            self.publog.error("Autocurator exited with exit code: " + str(os.WEXITSTATUS(stat)))
            self.cleanup()
            exit(os.WEXITSTATUS(stat))

    def mk_dataset(self, map_json_data):
        mkd = self.MKD_Construct(self.data_node, self.index_node, self.replica, self.globus, self.data_roots, self.dtn,
                                self.silent, self.verbose)
        mkd.set_project(self.project)

        if self.autoc_command:
            scan_arg = json.load(open(self.scanfn))
        else:
            scan_arg = self.xarray_set
        try:
            out_json_data = mkd.get_records(map_json_data, scan_arg, self.json_file, user_project=self.proj_config)
        except Exception as ex:
            self.publog.exception("Failed to make dataset")
            self.cleanup()
            exit(1)
        return out_json_data

    def workflow(self):

        # step one: convert mapfile
        self.publog.info("Converting mapfile...")
        map_json_data = self.mapfile()


        # step two: autocurator
#        self.publog.info("Running autocurator...")
        self.publog.info("Xarray extraction")
        self.xarray_load(map_json_data)

        # step three: make dataset
        self.publog.info("Making dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        # step four: update record if exists
        self.publog.info("Updating...")
        self.update(out_json_data)

        # step five: publish to database
        self.publog.info("Running index pub...")
        rc = self.index_pub(out_json_data)

        self.publog.info("Done. Cleaning up.")
        self.cleanup()
        return rc
