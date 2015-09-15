from AccessControl.SecurityInfo import ClassSecurityInformation
from Acquisition import aq_base
from Products.Archetypes.Field import FileField
from Products.Archetypes.Field import ImageField
from Products.Archetypes.Field import ReferenceField
from Products.CMFPlone.interfaces import IPloneSiteRoot
from StringIO import StringIO
from ftw.publisher.core import states
from ftw.publisher.core.utils import encode_after_json
from ftw.publisher.receiver import getLogger
import base64
import json
import pkg_resources

try:
    pkg_resources.get_distribution('plone.app.blob')

except pkg_resources.DistributionNotFound:
    HAS_BLOBS = False

else:
    HAS_BLOBS = True
    from plone.app.blob.interfaces import IBlobField


class Decoder(object):
    """
    Decodes json data to dictionary and validates it.
    It also validates and decodes all schema field values.
    """

    security = ClassSecurityInformation()

    def __init__(self, context):
        """
        Constructor: stores context as object attribute
        @param context:         Plone object
        @type:                  Plone Object
        """
        self.context = context
        self.logger = getLogger()

    security.declarePrivate('__call__')
    def __call__(self, jsondata):
        """
        Decodes the jsondata to a dictionary, validates it,
        unserializes the field values and returns it.
        @return:        Data dictionary
        @rtype:         dict
        """
        self.data = self.decodeJson(jsondata)
        self.validate()
        return self.data

    security.declarePrivate('decodeJson')
    def decodeJson(self, jsondata):
        """
        Decodes the JSON data with the json module.
        If the json module cannot decode the string, a
        DecodeError is raised.
        @param jsondata:    JSON data
        @type jsondata:     string
        @return:            Decode Data dictionary
        @rtype:             dict
        @raise:             DecodeError
        """
        try:
            data = json.loads(jsondata)
        except Exception, e:
            raise states.DecodeError(str(e))
        data = encode_after_json(data)
        return data

    security.declarePrivate('validate')
    def validate(self):
        """
        Validates, if all required values are provided. If a
        error occures, a PartialError is raised.
        @raise:             PartialError
        @return:            None
        """
        structure = {
            'metadata': [
                'UID',
                'id',
                'portal_type',
                'action',
                'physicalPath',
                'sibling_positions',
            ]
        }
        for key in structure.keys():
            if key not in self.data.keys():
                raise states.PartialError('Missing "%s"' % key)
            else:
                for subkey in structure[key]:
                    if subkey not in self.data[key]:
                        raise states.PartialError(
                            'Missing "%s.%s"' % (key, subkey))

    security.declarePrivate('getSchema')
    def getSchema(self, object):
        """
        Returns the Schema of the portal_type defined in the metadata.
        @return:        Archetypes Schema object
        @rtype:         Schema
        """
        if not IPloneSiteRoot.providedBy(object):
            schema_path = self.data['metadata']['schema_path']
            path_parts = schema_path.split('.')
            module_path = '.'.join(path_parts[:-2])
            class_name = path_parts[-2]
            var_name = path_parts[-1]
            klass = getattr(__import__(module_path, globals(),
                                       locals(), class_name), class_name)
            schema = getattr(klass, var_name)
            return schema
        else:
            return None

    security.declarePrivate('unserializeFields')
    def unserializeFields(self, object, jsonkey):
        """
        Unserializes the fielddata and optimizes it of the modifiers of
        the fields.
        Gets and sets from / to **self.data**
        """

        # we just have to go throught if we have a dict, with possible
        # schema fields
        if not isinstance(self.data[jsonkey], dict):
            return self.data

        if IPloneSiteRoot.providedBy(object):
            return self.data

        if not hasattr(aq_base(object), 'Schema'):
            # might be dexterity
            return self.data

        fields = object.Schema().fields()

        for field in fields:
            name = field.getName()
            if name not in self.data[jsonkey].keys():
                continue

            # DateTimeField doesnt need to be converted t DateTime
            # FileFields are base64 encoded

            if HAS_BLOBS and IBlobField.providedBy(field) or \
               isinstance(field, (ImageField, FileField)):
                value = self.data[jsonkey][name]

                if isinstance(value, dict) and not value['data']:
                    self.data[jsonkey][name] = None

                elif isinstance(value, dict):
                    # decode it
                    data = StringIO(base64.decodestring(value['data']))
                    data.seek(0)
                    setattr(data, 'filename', value['filename'])
                    self.data[jsonkey][name] = data

            # ReferenceField: remove bad UIDs
            if isinstance(field, ReferenceField):
                # check if field ist multiValued
                if field.multiValued:
                    cleaned = []
                    for uid in self.data[jsonkey][name]:
                        obj = self.context.reference_catalog.lookupObject(uid)
                        if obj:
                            cleaned.append(uid)
                        else:
                            if uid:
                                self.logger.warn(
                                    ('The reference field <%s> of object(%s)'
                                     ' has a broken reference to'
                                     ' the object %s') % (name,
                                                          object.UID(),
                                                          uid))

                    self.data[jsonkey][name] = cleaned

                else:
                    cleaned = None
                    obj = self.context.reference_catalog.lookupObject(
                        self.data[jsonkey][name])
                    if obj:
                        cleaned = self.data[jsonkey][name]
                    else:
                        if self.data[jsonkey][name]:
                            self.logger.warn(
                                ('The reference field <%s> of object(%s) has a'
                                 ' broken reference to the object %s') % (
                                     name,
                                     object.UID(),
                                     self.data[jsonkey][name]))

                    self.data[jsonkey][name] = cleaned

            # ImageField: treat empty files special
            if isinstance(field, ImageField):
                if not self.data[jsonkey][name]:
                    self.data[jsonkey][name] = 'DELETE_IMAGE'

            # FileField (direct): treat empty files special
            if field.__class__ == FileField:
                if not self.data[jsonkey][name]:
                    self.data[jsonkey][name] = 'DELETE_FILE'

        return self.data
