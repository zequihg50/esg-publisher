"Database class, table, and object/relational mapping definitions."
import datetime
import time

from sqlalchemy import Column, MetaData, Table, types, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm.collections import attribute_mapped_collection
from esgcet.exceptions import *

# Set _database to "postgres", "mysql", or "sqllite" to avoid reading the config file twice
_database = "postgres"
if _database is None:
    from esgcet.config import loadConfig1
    import urlparse
    config1 = loadConfig1(None)
    dburl = config1.get('initialize', 'dburl')
    urltuple = urlparse.urlparse(dburl)
    _database = urltuple[0]

# For Postgres:
if _database=="postgres":
    from sqlalchemy.databases.postgres import PGBigInteger as MyBigInteger
    MyDouble = types.Float(precision=53)
    _character_encoding = 'utf-8'

# For MySQL:
elif _database=="mysql":
    from sqlalchemy.databases.mysql import MSBigInteger as MyBigInteger, MSDouble as MyDouble
    _character_encoding = 'latin-1'

# For SQLlite:
elif _database=="sqllite":
    MyBigInteger = types.Integer
    MyDouble = types.Float
    _character_encoding = 'latin-1'

else:
    raise ESGPublishError("No database defined in model/__init__.py")

#-------------------------------------------------------

def validateName(name, cls):
##     if name.find(".")!=-1:
##         raise ESGPublishError("Invalid %s identifier: %s, contains a period."%(cls, name))
    pass

def map_to_charset(value):
    try:
        result = unicode(str(value), _character_encoding, 'replace')
    except:
        result = unicode(str(value), 'utf-8', 'replace')
    return result

# Decorator for object getter functions. Ensures that the object is persistent
def persistent_get(getter):
    def dbwrapper(slf, Session):
        session = Session()
        session.add(slf)
        result = getter(slf, Session)
        session.close()
        return result
    return dbwrapper

metadata = MetaData()

projectTable = Table('project', metadata,
                     Column('name', types.String(64), primary_key=True, nullable=False),
                     Column('description', types.String(64)),
                     mysql_engine='InnoDB',
                     )

modelTable = Table('model', metadata,
                   Column('name', types.String(64), primary_key=True, nullable=False),
                   Column('project', types.String(64), ForeignKey('project.name')),
                   Column('url', types.String(128)),
                   Column('description', types.Text),
                   mysql_engine='InnoDB',
                   )

experimentTable = Table('experiment', metadata,
                        Column('name', types.String(64), primary_key=True, nullable=False),
                        Column('project', types.String(64), ForeignKey('project.name')),
                        Column('description', types.Text),
                        mysql_engine='InnoDB',
                        )

datasetTable = Table('dataset', metadata,
                     Column('id', types.Integer, primary_key=True, autoincrement=True),
                     Column('name', types.String(255), unique=True),
                     Column('project', types.String(64), ForeignKey('project.name')),
                     Column('model', types.String(64), ForeignKey('model.name')),
                     Column('experiment', types.String(64), ForeignKey('experiment.name')),
                     Column('run_name', types.String(64)),
                     Column('calendar', types.String(32)),
                     Column('aggdim_name', types.String(64)),
                     Column('aggdim_units', types.String(64)),
                     Column('status_id', types.String(64)),
                     Column('offline', types.Boolean),
                     Column('master_gateway', types.String(64)),
                     mysql_engine='InnoDB',
                     )

datasetVersionTable = Table('dataset_version', metadata,
                            Column('dataset_id', types.Integer, ForeignKey('dataset.id'), primary_key=True),
                            Column('version', types.Integer, primary_key=True),
                            Column('creation_time', types.DateTime),
                            Column('comment', types.Text),
                            mysql_engine='InnoDB',
                            )

# Index('datasetversion_index', datasetVersionTable.c.dataset_id, datasetVersionTable.c.version, unique=True)

variableTable = Table('variable', metadata,
                      Column('id', types.Integer, primary_key=True, autoincrement=True),
                      Column('dataset_id', types.Integer, ForeignKey('dataset.id')),
                      Column('short_name', types.String(255)),
                      Column('long_name', types.String(255)),
                      Column('standard_name', types.String(128), ForeignKey('standard_name.name')),
                      Column('vertical_granularity', types.String(64)),
                      Column('grid', types.Integer),
                      Column('aggdim_first', MyDouble),
                      Column('aggdim_last', MyDouble),
                      Column('units', types.String(64)),
                      Column('has_errors', types.Boolean),
                      Column('eastwest_range', types.String(64)),
                      Column('northsouth_range', types.String(64)),
                      Column('updown_range', types.String(64)),
                      mysql_engine='InnoDB',
                      )

fileTable = Table('file', metadata,
                  Column('id', types.Integer, primary_key=True, autoincrement=True),
                  Column('dataset_id', types.Integer, ForeignKey('dataset.id'), nullable=False),
                  Column('base', types.String(255), nullable=False),
                  Column('format', types.String(16)),
                  Column('deletion_time', types.DateTime),
                  UniqueConstraint('dataset_id', 'base'),
                  mysql_engine='InnoDB',
                  )

fileVersionTable = Table('file_version', metadata,
                         Column('file_id', types.Integer, ForeignKey('file.id'), primary_key=True),
                         Column('version', types.Integer, primary_key=True),
                         Column('location', types.String(255), nullable=False),
                         Column('size', MyBigInteger),
                         Column('checksum', types.String(64)),
                         Column('checksum_type', types.String(32)),
                         Column('publication_time', types.DateTime),
                         Column('tracking_id', types.String(64)),
                         Column('mod_time', MyDouble),
                         mysql_engine='InnoDB',
                         )
# Index('fileversion_index', fileVersionTable.c.file_id, fileVersionTable.c.version, unique=True)

fileVariableTable = Table('file_variable', metadata,
                          Column('id', types.Integer, primary_key=True, autoincrement=True),
                          Column('file_id', types.Integer, ForeignKey('file.id'), nullable=False),
                          Column('variable_id', types.Integer, ForeignKey('variable.id')),
                          Column('short_name', types.String(255), nullable=False),
                          Column('long_name', types.String(255)),
                          Column('aggdim_first', MyDouble),
                          Column('aggdim_last', MyDouble),
                          Column('aggdim_units', types.String(64)),
                          Column('coord_range', types.String(32)),
                          Column('coord_type', types.String(8)),
                          mysql_engine='InnoDB',
                          )
Index('filevar_index', fileVariableTable.c.file_id, fileVariableTable.c.variable_id, unique=True)

datasetAttrTable = Table('dataset_attr', metadata,
                         Column('dataset_id', types.Integer, ForeignKey('dataset.id'), primary_key=True),
                         Column('name', types.String(64), primary_key=True),
                         Column('value', types.Text, nullable=False),
                         Column('datatype', types.CHAR(1), nullable=False),
                         Column('length', types.Integer, nullable=False),
                         Column('is_category', types.Boolean),
                         Column('is_thredds_category', types.Boolean),
                         UniqueConstraint('dataset_id', 'name'),
                         mysql_engine='InnoDB',
                         )

variableAttrTable = Table('var_attr', metadata,
                          Column('variable_id', types.Integer, ForeignKey('variable.id'), primary_key=True),
                          Column('name', types.String(64), primary_key=True),
                          Column('value', types.Text, nullable=False),
                          Column('datatype', types.CHAR(1), nullable=False),
                          Column('length', types.Integer, nullable=False),
                          UniqueConstraint('variable_id', 'name'),
                          mysql_engine='InnoDB',
                          )

fileAttrTable = Table('file_attr', metadata,
                      Column('file_id', types.Integer, ForeignKey('file.id'), primary_key=True),
                      Column('name', types.String(64), primary_key=True),
                      Column('value', types.Text, nullable=False),
                      Column('datatype', types.CHAR(1), nullable=False),
                      Column('length', types.Integer, nullable=False),
                      UniqueConstraint('file_id', 'name'),
                      mysql_engine='InnoDB',
                      )

fileVariableAttrTable = Table('file_var_attr', metadata,
                              Column('filevar_id', types.Integer, ForeignKey('file_variable.id'), primary_key=True),
                              Column('name', types.String(64), primary_key=True),
                              Column('value', types.Text, nullable=False),
                              Column('datatype', types.CHAR(1), nullable=False),
                              Column('length', types.Integer, nullable=False),
                              UniqueConstraint('filevar_id', 'name'),
                              mysql_engine='InnoDB',
                              )

varDimensionTable = Table('var_dimension', metadata,
                          Column('variable_id', types.Integer, ForeignKey('variable.id'), primary_key=True),
                          Column('name', types.String(64), primary_key=True, nullable=False),
                          Column('length', types.Integer, nullable=False),
                          Column('seq', types.Integer, nullable=False),
                          mysql_engine='InnoDB',
                          )

filevarDimensionTable = Table('filevar_dimension', metadata,
                              Column('filevar_id', types.Integer, ForeignKey('file_variable.id'), primary_key=True),
                              Column('name', types.String(64), primary_key=True, nullable=False),
                              Column('length', types.Integer, nullable=False),
                              Column('seq', types.Integer, nullable=False),
                              mysql_engine='InnoDB',
                              )

standardNameTable = Table('standard_name', metadata,
                          Column('name', types.String(128), primary_key=True, nullable=False),
                          Column('units', types.String(64)),
                          Column('amip', types.String(64)),
                          Column('grib', types.String(64)),
                          Column('description', types.Text),
                          mysql_engine='InnoDB',
                          )

eventTable = Table('event', metadata,
                   Column('id', types.Integer, primary_key=True, autoincrement=True),
                   Column('datetime', types.DateTime, index=True, nullable=False),
                   Column('object_id', types.Integer, ForeignKey('dataset.id')),
                   Column('object_name', types.String(255), nullable=False),
                   Column('object_version', types.Integer),
                   Column('event', types.Integer),
                   mysql_engine='InnoDB',
                   )

catalogTable = Table('catalog', metadata,
                     Column('dataset_name', types.String(255), primary_key=True, nullable=False),
                     Column('location', types.String(255), nullable=False),
                     Column('rootpath', types.String(255)),
                     mysql_engine='InnoDB',
                     )

LASCatalogTable = Table('las_catalog', metadata,
                     Column('dataset_name', types.String(255), primary_key=True, nullable=False),
                     Column('location', types.String(255), nullable=False),
                     mysql_engine='InnoDB',
                     )

datasetStatusTable = Table('dataset_status', metadata,
                           Column('id', types.Integer, primary_key=True, autoincrement=True),
                           Column('datetime', types.DateTime),
                           Column('object_id', types.Integer, ForeignKey('dataset.id')),
                           Column('level', types.Integer),
                           Column('module', types.Integer),
                           Column('status', types.Text),
                           mysql_engine='InnoDB',
                           )

class Project(object):

    def __init__(self, name, description=None):
        validateName(name, "Project")
        self.name = name
        self.description = description

    def __repr__(self):
        return "<Project, name=%s, description=%s>"%(self.name, `self.description`)
    
class Model(object):

    def __init__(self, name, project, url=None, description=None):
        validateName(name, "Model")
        self.name = name
        self.project = project
        self.url = url
        self.description = description

    def __repr__(self):
        return "<Model, name=%s>"%(self.name)
    
class Experiment(object):

    def __init__(self, name, project, description):
        validateName(name, "Experiment")
        self.name = name
        self.project = project
        self.description = description

    def __repr__(self):
        return "<Experiment, name=%s>"%(self.name)
    
class Dataset(object):

    def __init__(self, name, project, model, experiment, run_name, calendar=None, aggdim_name=None, aggdim_units=None, status_id=None, offline=False, masterGateway=None):
        self.name = name
        self.project = project
        self.model = model
        self.experiment = experiment
        self.run_name = run_name
        self.calendar = calendar
        self.aggdim_name = aggdim_name
        self.aggdim_units = aggdim_units
        self.status_id = status_id
        self.offline = offline
        self.master_gateway = masterGateway

    @staticmethod
    def lookup(name, Session):
        "Return the dataset instance having *name*. The instance will be detached from any session."
        session = Session()
        dset = session.query(Dataset).filter_by(name=name).first()
        session.close()
        return dset

    @persistent_get
    def get_id(self, Session):
        "Return the database ID"
        return self.id

    @persistent_get
    def get_name(self, Session):
        "Return the dataset name"
        return self.name

    @persistent_get
    def get_project(self, Session):
        "Return the dataset project"
        return self.project

    @persistent_get
    def get_model(self, Session):
        "Return the dataset model"
        return self.model

    @persistent_get
    def get_experiment(self, Session):
        "Return the dataset experiment"
        return self.experiment

    @persistent_get
    def get_run_name(self, Session):
        "Return the dataset run_name"
        return self.run_name

    def deleteChildren(self, sess):
        """Delete children of this instance from the database with direct SQL calls, for efficiency."""
        if _database=="postgres":
            # var_attr ----------------------
            sess.execute("delete from var_attr using variable as v where var_attr.variable_id=v.id and v.dataset_id=%s"%self.id)

            # dataset_attr ----------------------
            sess.execute("delete from dataset_attr where dataset_id=%s"%self.id)

            # file_attr ----------------------
            sess.execute("delete from file_attr using file as f where file_attr.file_id=f.id and f.dataset_id=%s"%self.id)

            # file_var_attr ----------------------
            sess.execute("delete from file_var_attr using file_variable as fv, file as f where file_var_attr.filevar_id=fv.id and fv.file_id=f.id and f.dataset_id=%s"%self.id)
            
            # var_dimension ----------------------
            sess.execute("delete from var_dimension using variable as v where var_dimension.variable_id=v.id and v.dataset_id=%s"%self.id)
            
            # filevar_dimension ----------------------
            sess.execute("delete from filevar_dimension using file_variable as fv, file as f where filevar_dimension.filevar_id=fv.id and fv.file_id=f.id and f.dataset_id=%s"%self.id)
            
            # filevar ----------------------
            sess.execute("delete from file_variable using file as f where file_variable.file_id=f.id and f.dataset_id=%s"%self.id)
            # file_version ----------------------
            sess.execute("delete from file_version using file as f where file_version.file_id=f.id and f.dataset_id=%s"%self.id)
            # file ----------------------
            sess.execute("delete from file where dataset_id=%s"%self.id)

            # variable ----------------------
            sess.execute("delete from variable where variable.dataset_id=%s"%self.id)

            # dataset_version ----------------------
            sess.execute("delete from dataset_version where dataset_version.dataset_id=%s"%self.id)

            # status ----------------------
            sess.execute("delete from dataset_status where dataset_status.object_id=%s"%self.id)

        else:

            raise ESGPublishError("Database not supported for dataset children delete: %s"%_database)

##             # var_attr ----------------------
##             sess.execute("delete from va using var_attr as va, variable as v where va.variable_id=v.id and v.dataset_id=%s"%self.id)

##             # dataset_attr ----------------------
##             sess.execute("delete from dataset_attr where dataset_id=%s"%self.id)
            
##             # file_attr ----------------------
##             sess.execute("delete from fa using file_attr as fa, file as f where fa.file_id=f.id and f.dataset_id=%s"%self.id)
##             # file_var_attr ----------------------
##             sess.execute("delete from fva using file_var_attr as fva, file_variable as fv, file as f where fva.filevar_id=fv.id and fv.file_id=f.id and f.dataset_id=%s"%self.id)

##             # var_dimension ----------------------
##             sess.execute("delete from vd using var_dimension as vd, variable as v where vd.variable_id=v.id and v.dataset_id=%s"%self.id)

##             # filevar_dimension ----------------------
##             sess.execute("delete from fvd using filevar_dimension as fvd, file_variable as fv, file as f where fvd.filevar_id=fv.id and fv.file_id=f.id and f.dataset_id=%s"%self.id)

##             # filevar ----------------------
##             sess.execute("delete from fv using file_variable as fv, file as f where fv.file_id=f.id and f.dataset_id=%s"%self.id)
##             # file_version ----------------------
##             sess.execute("delete from fv using file_variable as fv, file as f where fv.file_id=f.id and f.dataset_id=%s"%self.id)
##             # file ----------------------
##             sess.execute("delete from file where dataset_id=%s"%self.id)

##             # variable ----------------------
##             sess.execute("delete from variable where variable.dataset_id=%s"%self.id)

##             # status ----------------------
##             sess.execute("delete from dataset_status where dataset_status.object_id=%s"%self.id)

    def warning(self, message, level, module):
        """Create a warning status entry, and issue the warning to the logger.

        Note: the instance must be attached to a database session.
        """
        from esgcet.messaging import warning as warn

        warningStatus = DatasetStatus(message, level, module)
        self.status.append(warningStatus)
        warn(message)

    def has_warnings(self, Session):
        """Check for warnings from the scan of this dataset.

        Returns True if any warnings are associated with the dataset.

        Session
          A database Session.
          
        """
        session = Session()
        session.add(self)
        result = (len(self.status)>0)
        session.close()
        return result

    def get_warnings(self, Session):
        """Get a list of warnings from the scan of this dataset.

        Returns a list of strings.

        Session
          A database Session.
          
        """
        session = Session()
        session.add(self)
        result = [item.status for item in self.status]
        session.close()
        return result

    def get_max_warning_level(self, Session):
        """Get the maximum error level for warnings and errors associated with this dataset.

        Returns one of: INFO_LEVEL, WARNING_LEVEL, ERROR_LEVEL as defined in esgcet.model,
          or None of there are no errors for this dataset.

        Session
          A database Session.
          
        """
        session = Session()
        session.add(self)
        if len(self.status)>0:
            result = max([item.level for item in self.status])
        else:
            result = None
        session.close()
        return result

    def clear_warnings(self, session, module):
        """Clear the list of warnings.

        Session
          A database session instance.

        module
          module identifier, e.g., PUBLISH_MODULE
          
        """
        session.add(self)
        for item in self.status:
            if item.module==module:
                session.delete(item)
        session.commit()

    def get_publication_status(self, Session=None):
        """Get the most recent publication event.

        Returns one of these values, as defined in esgcet.model:

        - ADD_FILE_EVENT
        - CREATE_DATASET_EVENT
        - DELETE_DATASET_EVENT
        - DELETE_DATASET_FAILED_EVENT
        - DELETE_FILE_EVENT
        - DELETE_GATEWAY_DATASET_EVENT
        - PUBLISH_DATASET_EVENT
        - PUBLISH_FAILED_EVENT
        - PUBLISH_STATUS_UNKNOWN_EVENT
        - START_DELETE_DATASET_EVENT
        - START_PUBLISH_DATASET_EVENT
        - START_UNPUBLISH_DATASET_EVENT
        - UNPUBLISH_DATASET_EVENT
        - UNPUBLISH_GATEWAY_DATASET_EVENT
        - UNPUBLISH_DATASET_FAILED_EVENT
        - UPDATE_DATASET_EVENT
        - WRITE_LAS_CATALOG_EVENT
        - WRITE_THREDDS_CATALOG_EVENT

        Session
          A database Session. May be None if the object is persistent
          
        """
        if Session is not None:
            session = Session()
            session.add(self)
        result = self.events[-1].event  # events is ordered by datetime
        if Session is not None:
            session.close()
        return result

    def getVersion(self):
        return self.versions[-1].version

    def setVersion(self, version):
        self.versions[-1].version = version

    def getFiles(self):
        return [f for f in self.files if f.deletion_time is None]

    def __repr__(self):
        return "<Dataset, id=%s, name=%s, project=%s, model=%s, experiment=%s, run_name=%s>"%(`self.id`, self.name, `self.project`, `self.model`, `self.experiment`, self.run_name)
    
class DatasetVersion(object):

    def __init__(self, version, creation_time=None, comment=None):
        self.version = version
        if creation_time is None:
            creation_time = datetime.datetime.now()
        self.creation_time = creation_time
        self.comment = comment

    @persistent_get
    def get_version(self, Session):
        "Return the dataset version"
        return self.version

    def __repr__(self):
        return "<DatasetVersion, version=%s, creation_time=%s>"%(`self.version`, `self.creation_time`)
    
class Variable(object):

    def __init__(self, short_name, long_name, standard_name=None, aggdim_first=None, aggdim_last=None, units=None, has_errors=False, eastwest_range=None, northsouth_range=None, updown_range=None):
        self.short_name = short_name
        self.long_name = long_name
        self.standard_name = standard_name
        self.aggdim_first = aggdim_first
        self.aggdim_last = aggdim_last
        self.units = units
        self.has_errors = has_errors
        self.eastwest_range = eastwest_range
        self.northsouth_range = northsouth_range
        self.updown_range = updown_range

    def lookupAttr(self, attname):
        """Helper function for aggregateVariables:
        Lookup an attribute of the variable."""
        result = None
        for attr in self.attributes:
            if attr.name==attname:
                result = attr.value
                break
        return result

    def __repr__(self):
        return "<Variable, id=%s, dataset_id=%s, short_name=%s, long_name=%s, standard_name=%s>"%(`self.id`, `self.dataset_id`, self.short_name, self.long_name, `self.standard_name`)

def FileFactory(base, location, session, format='netCDF', deletedFileDictionary=None):
    """
    Create a new File object. If the file location is a key in
    the deletedFileDictionary dictionary, the file is 'undeleted' and the existing file object is reused.

    Returns the tuple (file_object, version_no).

    base
      String basename, unique wrt to all files in the dataset. Typically this is the basename of the file path.

    format
      String format of the file.

    deletedFileDictionary
      dictionary with keys of the locations of all files in the parent dataset that have been deleted.
      If 
    """
    if deletedFileDictionary is not None and deletedFileDictionary.has_key(location):
        fileobj = deletedFileDictionary[location]
        fileobj.base = base
        fileobj.format = format
        fileobj.undelete()              # 'undelete' the file
        versionNo = fileobj.getVersion()+1 # and bump the version number
        fileobj.deleteChildren(session)
        session.commit()
    else:
        fileobj = File(base, format)
        versionNo = 1

    return (fileobj, versionNo)

class File(object):

    def __init__(self, base, format, deletion_time=None):
        self.base = base
        self.format = format
        self.deletion_time = deletion_time # File is deleted if not None

    def delete(self, sess):
        self.deletion_time = datetime.datetime.now()
        self.deleteChildren(sess)
        sess.commit()

    def undelete(self):
        self.deletion_time = None

    def isDeleted(self):
        return (self.deletion_time is not None)

    def deleteChildren(self, sess):
        """Delete children of this instance from the database with direct SQL calls, for efficiency."""

        if _database!="postgres":
            raise ESGPublishError("Database not supported for file children delete: %s"%_database)

        # file_attr ----------------------
        sess.execute("delete from file_attr using file as f where file_attr.file_id=%s"%self.id)

        # file_var_attr ----------------------
        sess.execute("delete from file_var_attr using file_variable as fv, file as f where file_var_attr.filevar_id=fv.id and fv.file_id=%s"%self.id)

        # filevar_dimension ----------------------
        sess.execute("delete from filevar_dimension using file_variable as fv, file as f where filevar_dimension.filevar_id=fv.id and fv.file_id=%s"%self.id)

        # filevar ----------------------
        sess.execute("delete from file_variable using file as f where file_variable.file_id=%s"%self.id)

    def getModificationFtime(self):
        latest = self.versions[-1]
        return latest.getModificationFtime()

    def getLocation(self):
        return self.versions[-1].location

    def getSize(self):
        return self.versions[-1].size

    def getVersion(self):
        return self.versions[-1].version

    def getModtime(self):
        return self.versions[-1].mod_time

    def getChecksum(self):
        return self.versions[-1].checksum

    def getChecksumType(self):
        return self.versions[-1].checksum_type

    def getTrackingID(self):
        return self.versions[-1].tracking_id

    def __repr__(self):
        return "<File, id=%s, dataset_id=%s, base=%s, format=%s"%(`self.id`, `self.dataset_id`, self.base, self.format)

class FileVersion(object):

    def __init__(self, version, location, size, checksum=None, checksum_type=None, publication_time=None, tracking_id=None, mod_time=None):
        self.version = version
        self.location = location        # May differ from previous versions if the file has moved during versioning
        self.size = size
        self.checksum = checksum
        self.checksum_type = checksum_type
        if publication_time is None:
            publication_time = datetime.datetime.now()
        self.publication_time = publication_time
        self.tracking_id = tracking_id
        self.mod_time = mod_time        # Floating point seconds since epoch

    def getModificationFtime(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.mod_time))

    def __repr__(self):
        return "<FileVersion, version=%s, location=%s, size=%s, checksum=%s, publication_time=%s, tracking_id=%s, mod_time=%s>"%(`self.version`, self.location, `self.size`, self.checksum, `self.publication_time`, self.tracking_id, `self.mod_time`)

class FileVariable(Variable):

    def __init__(self, short_name, long_name, aggdim_first=None, aggdim_last=None, aggdim_units=None, coord_range=None, coord_type=None):
        Variable.__init__(self, short_name, long_name, aggdim_first, aggdim_last)
        self.aggdim_units = aggdim_units
        self.coord_range = coord_range
        self.coord_type = coord_type
        
    def __repr__(self):
        return "<FileVariable, id=%s, file_id=%s, variable_id=%s, short_name=%s, long_name=%s, aggdim_first=%s, aggdim_last=%s>"%(`self.id`, `self.file_id`, `self.variable_id`, `self.short_name`, `self.long_name`, `self.aggdim_first`, `self.aggdim_last`)

class Attribute(object):

    def __init__(self, name, value, datatype, length):
        self.name = name
        self.value = value
        self.datatype = datatype
        self.length = length

    def __repr__(self):
        return "name=%s, value=%s, datatype=%s, length=%d"%(self.name, self.value, self.datatype, self.length)

class DatasetAttribute(Attribute):
    
    def __init__(self, name, value, datatype, length, is_category=False, is_thredds_category=False):

        Attribute.__init__(self, name, value, datatype, length)
        self.is_category = is_category
        self.is_thredds_category = is_thredds_category

    def __repr__(self):
        return "<Attribute, dataset_id=%s, %s>"%(`self.dataset_id`, Attribute.__repr__(self))

class VariableAttribute(Attribute):
    
    def __init__(self, name, value, datatype, length):

        Attribute.__init__(self, name, value, datatype, length)

    def __repr__(self):
        return "<VariableAttribute, variable_id=%s, %s>"%(`self.variable_id`, Attribute.__repr__(self))

class FileAttribute(Attribute):
    
    def __init__(self, name, value, datatype, length):

        Attribute.__init__(self, name, value, datatype, length)

    def __repr__(self):
        return "<FileAttribute, file_id=%s, %s>"%(`self.file_id`, Attribute.__repr__(self))

class FileVariableAttribute(Attribute):
    
    def __init__(self, name, value, datatype, length):

        Attribute.__init__(self, name, value, datatype, length)

    def __repr__(self):
        return "<FileVariableAttribute, filevar_id=%s, %s>"%(`self.filevar_id`, Attribute.__repr__(self))

class VariableDimension(object):
        
    def __init__(self, name, length, seq):
        self.name = name
        self.length = length
        self.seq = seq

    def __repr__(self):
        return "<VariableDimension, variable_id=%s, name=%s, length=%d, seq=%d>"%(`self.variable_id`, self.name, self.length, self.seq)

class FileVariableDimension(object):
        
    def __init__(self, name, length, seq):
        self.name = name
        self.length = length
        self.seq = seq

    def __repr__(self):
        return "<FileDimension, filevar_id=%s, name=%s, length=%d, seq=%d>"%(`self.filevar_id`, self.name, self.length, self.seq)

class StandardName(object):

    def __init__(self, name, units, amip='', grib='', description=''):
        self.name = name
        self.units = units
        self.amip = amip
        self.grib = grib
        self.description = description

    def __repr__(self):
        return "<StandardName, name=%s, units=%s, amip=%s, grib=%s, description=%s>"%(self.name, self.units, self.amip, self.grib, self.description)

CREATE_DATASET_EVENT = 1
UPDATE_DATASET_EVENT = 2
PUBLISH_DATASET_EVENT = 3
DELETE_DATASET_EVENT = 4
ADD_FILE_EVENT = 5
DELETE_FILE_EVENT = 6
UNPUBLISH_DATASET_EVENT = 7
WRITE_THREDDS_CATALOG_EVENT = 8
START_PUBLISH_DATASET_EVENT = 9
PUBLISH_FAILED_EVENT = 10
START_DELETE_DATASET_EVENT = 11
DELETE_GATEWAY_DATASET_EVENT = 12
DELETE_DATASET_FAILED_EVENT = 13
WRITE_LAS_CATALOG_EVENT = 14
PUBLISH_STATUS_UNKNOWN_EVENT = 15
START_UNPUBLISH_DATASET_EVENT = 16
UNPUBLISH_GATEWAY_DATASET_EVENT = 17
UNPUBLISH_DATASET_FAILED_EVENT = 18

eventName = {
    ADD_FILE_EVENT : "ADD_FILE",
    CREATE_DATASET_EVENT : "CREATE_DATASET",
    DELETE_DATASET_EVENT : "DELETE_DATASET",
    DELETE_DATASET_FAILED_EVENT : "DELETE_DATASET_FAILED",
    DELETE_FILE_EVENT : "DELETE_FILE",
    DELETE_GATEWAY_DATASET_EVENT : "DELETE_GATEWAY_DATASET", 
    PUBLISH_DATASET_EVENT : "PUBLISH_DATASET",
    PUBLISH_FAILED_EVENT : "PUBLISH_FAILED_EVENT",
    PUBLISH_STATUS_UNKNOWN_EVENT : "PUBLISH_STATUS_UNKNOWN_EVENT",
    START_DELETE_DATASET_EVENT : "START_DELETE_DATASET",
    START_PUBLISH_DATASET_EVENT : "START_PUBLISH_DATASET",
    START_UNPUBLISH_DATASET_EVENT : "START_RETRACT_DATASET",
    UNPUBLISH_DATASET_EVENT : "RETRACT_DATASET",
    UNPUBLISH_DATASET_FAILED_EVENT : "RETRACT_DATASET_FAILED",
    UNPUBLISH_GATEWAY_DATASET_EVENT : "RETRACT_GATEWAY_DATASET",
    UPDATE_DATASET_EVENT : "UPDATE_DATASET",
    WRITE_LAS_CATALOG_EVENT : "WRITE_LAS_CATALOG",
    WRITE_THREDDS_CATALOG_EVENT : "WRITE_THREDDS_CATALOG",
    }

eventShortName = {
    ADD_FILE_EVENT : "Added",
    CREATE_DATASET_EVENT : "Scanned",
    DELETE_DATASET_EVENT : "Deleted",
    DELETE_DATASET_FAILED_EVENT : "Failed GW Deletion",
    DELETE_FILE_EVENT : "Deleted File",
    DELETE_GATEWAY_DATASET_EVENT : "Gateway Deletion", 
    PUBLISH_DATASET_EVENT : "Published",
    PUBLISH_FAILED_EVENT : "Publish Failed",
    PUBLISH_STATUS_UNKNOWN_EVENT : "Unknown Status",
    START_DELETE_DATASET_EVENT : "Start Dataset Deletion",
    START_PUBLISH_DATASET_EVENT : "Processing",
    START_UNPUBLISH_DATASET_EVENT : "Start Gateway Retraction",
    UNPUBLISH_DATASET_EVENT : "Unpublished",
    UNPUBLISH_DATASET_FAILED_EVENT : "Failed GW Retraction",
    UNPUBLISH_GATEWAY_DATASET_EVENT : "Gateway Retraction",
    UPDATE_DATASET_EVENT : "Updated",
    WRITE_LAS_CATALOG_EVENT : "LAS...",
    WRITE_THREDDS_CATALOG_EVENT : "Thredds...",
    }

eventNumber = {
    "ADD_FILE" : ADD_FILE_EVENT,
    "CREATE_DATASET" : CREATE_DATASET_EVENT,
    "DELETE_DATASET" : DELETE_DATASET_EVENT,
    "DELETE_DATASET_FAILED" : DELETE_DATASET_FAILED_EVENT,
    "DELETE_FILE" : DELETE_FILE_EVENT,
    "DELETE_GATEWAY_DATASET" : DELETE_GATEWAY_DATASET_EVENT, 
    "PUBLISH_DATASET" : PUBLISH_DATASET_EVENT,
    "PUBLISH_FAILED_EVENT" : PUBLISH_FAILED_EVENT,
    "PUBLISH_STATUS_UNKNOWN_EVENT" : PUBLISH_STATUS_UNKNOWN_EVENT,
    "START_DELETE_DATASET" : START_DELETE_DATASET_EVENT,
    "START_PUBLISH_DATASET" : START_PUBLISH_DATASET_EVENT,
    "START_RETRACT_DATASET" : START_UNPUBLISH_DATASET_EVENT,
    "RETRACT_DATASET" : UNPUBLISH_DATASET_EVENT,
    "RETRACT_DATASET_FAILED" : UNPUBLISH_DATASET_FAILED_EVENT,
    "RETRACT_GATEWAY_DATASET" : UNPUBLISH_GATEWAY_DATASET_EVENT,
    "UPDATE_DATASET" : UPDATE_DATASET_EVENT,
    "WRITE_LAS_CATALOG" : WRITE_LAS_CATALOG_EVENT,
    "WRITE_THREDDS_CATALOG" : WRITE_THREDDS_CATALOG_EVENT,
    }

class Event(object):

    def __init__(self, object_name, object_version, event, dtime=None):
        self.object_name = object_name
        self.object_version = object_version
        self.event = event
        if dtime is None:
            dtime = datetime.datetime.now()
        self.datetime = dtime

    def __repr__(self):
        return "<Event, datetime=%s, object_id=%s, object_name=%s, object_version=%d, event=%s>"%(`self.datetime`, `self.object_id`, self.object_name, self.object_version, eventName[self.event])

class Catalog(object):

    def __init__(self, dataset_name, location, rootpath=None):
        self.dataset_name = dataset_name
        self.location = location
        self.rootpath = rootpath        # Used to generate TDS datasetRoot elements

    def __repr__(self):
        return "<Catalog, dataset_name=%s, location=%s, rootpath=%s>"%(self.dataset_name, self.location, str(self.rootpath))

class LASCatalog(object):

    def __init__(self, dataset_name, location):
        self.dataset_name = dataset_name
        self.location = location

    def __repr__(self):
        return "<LASCatalog, dataset_name=%s, location=%s>"%(self.dataset_name, self.location)

INFO_LEVEL = 1
WARNING_LEVEL = 2
ERROR_LEVEL = 3

EXTRACT_MODULE = 1
AGGREGATE_MODULE = 2
THREDDS_MODULE = 3
LAS_MODULE = 4
PUBLISH_MODULE = 5

class DatasetStatus(object):

    def __init__(self, status, level, module, dtime=None):
        self.status = status
        self.level = level              # WARNING_LEVEL or ERROR_LEVEL
        self.module = module            # e.g., THREDDS_MODULE
        if dtime is None:
            dtime = datetime.datetime.now()
        self.datetime = dtime

    def __repr__(self):
        return "<DatasetStatus, datetime=%s, status=%s, level=%s, module=%s>"%(`self.datetime`, self.status, `self.level`, `self.module`)

mapper(Project, projectTable, properties={'models':relation(Model, cascade="all, delete, delete-orphan"),
                                          'experiments':relation(Experiment, cascade="all, delete, delete-orphan")
                                          })
mapper(Model, modelTable)
mapper(Experiment, experimentTable)

# Note: dataset.attributes is a dictionary keyed on attribute.name. This allows handler.saveContext to
#   save category values without worrying about duplicate attribute names.
mapper(Dataset, datasetTable, properties={'variables':relation(Variable, cascade="all, delete, delete-orphan"),
                                          'files':relation(File, cascade="all, delete, delete-orphan"),
                                          'attributes':relation(DatasetAttribute, cascade="all, delete, delete-orphan",
                                                                collection_class=attribute_mapped_collection('name')),
                                          'events':relation(Event, order_by=[eventTable.c.datetime]),
                                          'status':relation(DatasetStatus, order_by=[datasetStatusTable.c.datetime]),
                                          'versions':relation(DatasetVersion, order_by=[datasetVersionTable.c.version], cascade="all, delete, delete-orphan"),
                                          })
mapper(Variable, variableTable, properties={'attributes':relation(VariableAttribute, cascade="all, delete, delete-orphan"),
                                            'dimensions':relation(VariableDimension, cascade="all, delete, delete-orphan"),
                                            'file_variables':relation(FileVariable), # No cascading
                                            })
mapper(File, fileTable, properties={'attributes':relation(FileAttribute, cascade="all, delete, delete-orphan"),
                                    'file_variables':relation(FileVariable, backref='file', cascade="all, delete, delete-orphan"),
                                    'versions':relation(FileVersion, order_by=[fileVersionTable.c.version], cascade="all, delete, delete-orphan"),
                                    })
mapper(FileVariable, fileVariableTable, properties={'attributes':relation(FileVariableAttribute, cascade="all, delete, delete-orphan"),
                                                    'dimensions':relation(FileVariableDimension, cascade="all, delete, delete-orphan")})
mapper(DatasetAttribute, datasetAttrTable)
mapper(VariableAttribute, variableAttrTable)
mapper(FileAttribute, fileAttrTable)
mapper(FileVariableAttribute, fileVariableAttrTable)
mapper(VariableDimension, varDimensionTable)
mapper(FileVariableDimension, filevarDimensionTable)
mapper(StandardName, standardNameTable)
mapper(Event, eventTable)
mapper(Catalog, catalogTable)
mapper(LASCatalog, LASCatalogTable)
mapper(DatasetStatus, datasetStatusTable)
mapper(DatasetVersion, datasetVersionTable)
mapper(FileVersion, fileVersionTable)