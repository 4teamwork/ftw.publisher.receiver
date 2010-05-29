#
# File:     communication.py
# Author:   Jonas Baumann <j.baumann@4teamwork.ch>
# Modified: 06.03.2009
#
# Copyright (c) 2007 by 4teamwork.ch
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
__author__ = """Jonas Baumann <j.baumann@4teamwork.ch>"""

# global imports
import simplejson
import base64

# plone imports
from Products.Archetypes.Field import FileField
from Products.Archetypes.Field import ImageField
from Products.Archetypes.Field import ReferenceField
from Products.CMFPlone.interfaces import IPloneSiteRoot


# ftw.publisher imports
from ftw.publisher.core import states
from ftw.publisher.receiver import getLogger

# zope imports
from zope.component import queryAdapter

#make archetype.schemaextender aware
HAS_AT_SCHEMAEXTENDER = False
try:
    from archetypes.schemaextender.interfaces import ISchemaExtender
    HAS_AT_SCHEMAEXTENDER = True
except ImportError:
    pass

class Decoder(object):
    """
    Decodes json data to dictionary and validates it.
    It also validates and decodes all schema field values.
    """

    def __init__(self, context):
        """
        Constructor: stores context as object attribute
        @param context:         Plone object
        @type:                  Plone Object
        """
        self.context = context
        self.logger = getLogger()

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

    def decodeJson(self, jsondata):
        """
        Decodes the JSON data with the simplejson module.
        If the simplejson module cannot decode the string, a
        DecodeError is raised.
        @param jsondata:    JSON data
        @type jsondata:     string
        @return:            Decode Data dictionary
        @rtype:             dict
        @raise:             DecodeError
        """
        try:
            data = simplejson.loads(jsondata)
        except Exception, e:
            raise states.DecodeError(str(e))
        return data

    def validate(self):
        """
        Validates, if all required values are provided. If a 
        error occures, a PartialError is raised.
        @raise:             PartialError
        @return:            None
        """
        structure = {
            'metadata' : [
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
                        raise states.PartialError('Missing "%s.%s"' % (key, subkey))

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

    def unserializeFields(self,object, jsonkey):
        """
        Unserializes the fielddata and optimizes it of the modifiers of
        the fields.
        Gets and sets from / to **self.data**
        """
        
        # we just have to go throught if we have a dict, with possible
        # schema fields
        if not isinstance(self.data[jsonkey],dict):
            return self.data
        
        schema = self.getSchema(object)
        fields = []
        
        if schema is not None:
            fields = schema.fields()
        if HAS_AT_SCHEMAEXTENDER and queryAdapter(object, ISchemaExtender):
            fields += ISchemaExtender(object).getFields()

        for field in fields:
            name = field.getName()
            if name not in self.data[jsonkey].keys():
                continue
            # DateTimeField doesnt need to be converted t DateTime
            # FileFields are base64 encoded
            if isinstance(field, FileField):
                value = self.data[jsonkey][name]
                if isinstance(value, dict):
                    # decode it
                    data = base64.decodestring(value['data'])
                    filename = value['filename']
                    # process it
                    file, mimetype, filename = field._process_input(data, filename=filename)
                    # we only use the file object
                    self.data[jsonkey][name] = file 
            # ReferenceField: remove bad UIDs
            if isinstance(field, ReferenceField):
                #check if field ist multiValued
                if field.multiValued: 
                    cleaned = []
                    for uid in self.data[jsonkey][name]:
                        obj = self.context.reference_catalog.lookupObject(uid)
                        if obj:
                            cleaned.append(uid)
                        else:
                            if uid:
                                self.logger.warn("The reference field <%s> of object(%s) has a broken reference to the object %s" % (name,object.UID(),uid))
                    self.data[jsonkey][name] = cleaned
                else:
                    cleaned = None
                    obj = self.context.reference_catalog.lookupObject(self.data[jsonkey][name])
                    if obj:
                        cleaned = self.data[jsonkey][name]
                    else:
                        if self.data[jsonkey][name]:
                            self.logger.warn("The reference field <%s> of object(%s) has a broken reference to the object %s" % (name,object.UID(),self.data[jsonkey][name]))
                    self.data[jsonkey][name] = cleaned
                    
            # ImageField: treat empty files special
            if isinstance(field, ImageField):
                if not self.data[jsonkey][name] or len(self.data[jsonkey][name])==0:
                    self.data[jsonkey][name] = 'DELETE_IMAGE'
            # FileField (direct): treat empty files special
            if field.__class__==FileField:
                if not self.data[jsonkey][name] or len(self.data[jsonkey][name])==0:
                    self.data[jsonkey][name] = 'DELETE_FILE'
        
        return self.data
