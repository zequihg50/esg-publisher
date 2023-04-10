from esgcet.pub_client import publisherClient
import sys, json

from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.search_check import ESGSearchCheck


import esgcet.logger as logger

log = logger.Logger()



def check_for_pid_proj(dset_arr):

    for dset in dset_arr:

        parts = dset.split('.')
        if parts[0].lower() in ["cmip6", "input4mips"]:
            return True            

    return False


def run(args):

<<<<<<< HEAD
<<<<<<< HEAD
    dset_id = args[0]
    do_delete = args[1]
    data_node = args[2]
    hostname = args[3]
    cert_fn = args[4]
    auth = args[5]
=======
=======
>>>>>>> refactor-esgf
    hostname = args["index_node"]
    verbose = args["verbose"]    
    silent = args["silent"]
    
    pub_log = log.return_logger('Unpublish', args["silent"], args["verbose"])
    searchcheck = ESGSearchCheck(hostname, silent, verbose)
    status = 0
<<<<<<< HEAD
>>>>>>> refactor-esgf
=======
>>>>>>> refactor-esgf

    for dset_id in args["dataset_id_lst"]:

        status += single_unpublish(dset_id, args, pub_log, searchcheck)
    return status

def single_unpublish(dset_id, args, pub_log, searchcheck):

    hostname = args["index_node"]
    do_delete = args["delete"]
    data_node = args["data_node"]
    cert_fn = args["cert"]
    auth = args["auth"]

    second_split = []
    if '|' in dset_id:
        first_split = dset_id.split('|')
        second_split = first_split[0].split('.')
        data_node = first_split[1]
    else:
        second_split = dset_id.split('.')
        dset_id_new = '{}|{}'.format(dset_id, data_node)
        dset_id = dset_id_new


    found, notretracted = searchcheck.run_check(dset_id)

    if not found:
        return(-1)

    if (not notretracted) and (not do_delete):
        pub_log.info("Use --delete to permanently erase the retracted record")
        return(0)

    if "pid_creds" in args and check_for_pid_proj([dset_id]):
        version = second_split[-1][1:]
        master_id = '.'.join(second_split[0:-1])
        pid_module = ESGPubPidCite({}, args["pid_creds"], data_node, False, args["silent"], args["verbose"])
        ret = pid_module.pid_unpublish(master_id, version)
        if not ret:
            pub_log.warning("PID Module did not return success")
    # ensure that dataset id is in correct format, use the set data node as a default
        
<<<<<<< HEAD
<<<<<<< HEAD
    pubCli = publisherClient(cert_fn, hostname, auth=auth)
=======
    pubCli = publisherClient(cert_fn, hostname, auth=auth, verbose=args["verbose"], silent=args["silent"])
>>>>>>> refactor-esgf
=======
    pubCli = publisherClient(cert_fn, hostname, auth=auth, verbose=args["verbose"], silent=args["silent"])
>>>>>>> refactor-esgf

    if do_delete:
        pubCli.delete(dset_id)
    else:
        pubCli.retract(dset_id)
    return(0)


