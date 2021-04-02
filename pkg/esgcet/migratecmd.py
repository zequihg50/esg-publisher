from esgcet.esgmigrate import ESGPubMigrate
import argparse, sys, os


DEFAULT_ESGINI = '/esg/config/esgcet'


def get_args():
    parser = argparse.ArgumentParser(description="Migrate old config settings into new format.")

    parser.add_argument("--old-config", dest="cfg", default=DEFAULT_ESGINI, help="Path to old config file.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("--project", dest="project", default=None, help='Name of a particular legacy project to migrate.')

    pub = parser.parse_args()

    return pub


def main():

    a = get_args()
    ini_path = a.cfg
    silent = a.silent
    verbose = a.verbose
    project = a.project

    em = ESGPubMigrate(ini_path, silent=silent, verbose=verbose)

    em.run(project)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
