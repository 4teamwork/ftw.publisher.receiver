from Acquisition import aq_base
from DateTime import DateTime
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from ZODB.POSException import ConflictError
from ftw.publisher.core import states, communication
from ftw.publisher.core.interfaces import IDataCollector
from ftw.publisher.receiver import decoder
from ftw.publisher.receiver import getLogger
from ftw.publisher.receiver.events import AfterCreatedEvent, AfterUpdatedEvent
from plone.app.uuid.utils import uuidToObject
from zope import event
from zope.component import getAdapters
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
from zope.publisher.interfaces import Retry
import os.path
import sys
import traceback
import plone.uuid


class ReceiveObject(BrowserView):
    """
    The ReceiveObject View is called be ftw.publisher.sender module.
    It expects a "jsondata"-paremeter in the request. It parses the jsondata
    and runs the specified action.
    """

    def __call__(self, *args, **kwargs):
        """
        @return:    response string containing a representation  of a
        CommunicationState as string.
        """
        # get a logger instance
        self.logger = getLogger()
        try:
            state = self.handleRequest()
        except Exception, e:
            if isinstance(e, states.CommunicationState):
                # if a CommunicationState is raised, we will use it as response
                state = e
            else:
                # otherwise we encapsulate the exception in a UnexpectedError
                exc = ''.join(traceback.format_exception(*sys.exc_info()))
                state = states.UnexpectedError(exc)

            self.logger.error('request failed: %s' % (state.toString()))

        # get the string representation of the CommunicationState
        resp = communication.createResponse(state)
        try:
            # if a exception was thrown, we add the traceback to the response
            resp += ''.join(traceback.format_exception(*sys.exc_info()))
        except:
            pass

        self.request.RESPONSE.setHeader('X-Theme-Disabled', 'True')
        return resp

    def handleRequest(self):
        """
        Handles a request from ftw.publisher.sender. It parses the paremeter
        "jsondata" which should be in the request.

        @raise:     CommunicationState
        @return:    CommunicationState-Object
        """
        # get the jsondata
        jsondata = self.request.get('jsondata', None)
        self.logger.info(
            'Receiving request (data length: %i Byte)' % len(jsondata))
        if not jsondata:
            raise states.InvalidRequestError('No jsondata provided')

        # decode the jsondata to a python dictionary
        # XXX we do this now twice (also in core adapters)
        self.decoder = decoder.Decoder(self.context)
        self.data = self.decoder(jsondata)

        # get the action type ..
        action = self.getAction()

        # .. and run the action specific method ..
        if action == 'push':
            # extract medata from data, we want to pass metadata
            # separatly to dataCollector adapters
            metadata = self.data['metadata']
            return self.pushAction(metadata, self.data)

        elif action == 'move':
            metadata = self.data['metadata']
            return self.moveAction(metadata, self.data)

        elif action == 'delete':
            metadata = self.data['metadata']
            return self.deleteAction(metadata)

        else:
            # ... or raise a UnexpectedError
            raise states.UnknownActionError()

        # should not get here
        raise states.UnexpectedError()

    def getAction(self):
        """
        Returns the action name of the current request.

        @rtype:     string
        @return:    action name ('push', 'move' or 'delete')
        """
        return self.data['metadata']['action']

    def pushAction(self, metadata, data):
        """
        Is called if the action is "push". It creates or updates a object
        (identifiers in metadata) with the given fielddata.
        For more infos about the provided data see
        ftw.publisher.sender.extrator

        @param metadata:        metadata dict containing UID, portal_type,
        action, physicalPath and sibling_positions
        @type metadata:         dict
        @param data:            dictionary contains the values collected by
        DataCollectors
        @type data:        dict
        @return:                CommunicationState instance
        @rtype:                 ftw.publisher.core.states.CommunicationState
        """
        # do we have to update or create? does the object already exist?
        # ... try it with the uid
        absPath = self._getAbsolutePath(metadata['physicalPath'])
        is_root = False

        object = self._getObjectByUID(metadata['UID'])
        if metadata['portal_type'] == 'Plone Site':
            object = self.context.portal_url.getPortalObject()
            is_root = True

        if object:
            # ... is it the right object?
            if '/'.join(object.getPhysicalPath()) != absPath:
                # wrong path -> try to get it by path
                # alias patch because thomas uses to index multiple objects
                # with different paths and the same UID in the reference
                # catalog -.-
                obj1 = object
                object = self._getObjectByPath(absPath)

                if not object:
                    # the object is in a wrong place, so lets try to move it
                    # where it belongs
                    current_path = '/'.join(obj1.getPhysicalPath())
                    expected_path = absPath

                    # if we can't fix it we will raise the followin exception
                    exception = states.UIDPathMismatchError({
                        'problem': 'path wrong',
                        'found path': current_path,
                        'expected path': expected_path,
                    })

                    # is it in the same place? -> rename
                    if current_path.split('/')[:-1] == \
                       expected_path.split('/')[:-1]:
                        putils = obj1.plone_utils
                        success, failure = putils.renameObjectsByPaths(
                            (current_path, ), (expected_path.split('/')[-1], ),
                            (obj1.Title(), ))
                        if failure:
                            raise exception
                        object = self._getObjectByPath(expected_path)

                    # .. so its in another place (another parent) -> move
                    else:
                        old_parent = obj1.aq_inner.aq_parent
                        try:
                            new_parent = self.context.restrictedTraverse(
                                '/'.join(expected_path.split('/')[:-1]))
                        except AttributeError:
                            raise exception
                        try:
                            cutted = old_parent.manage_cutObjects(obj1.id)
                            new_parent.manage_pasteObjects(cutted)
                        except (ConflictError, Retry):
                            raise
                        except:
                            raise exception
                        else:
                            object = self._getObjectByPath(expected_path)

                elif object.UID() != metadata['UID']:
                    raise states.UIDPathMismatchError({
                        'problem': 'UID wrong',
                        'found uid': object.UID(),
                        'expected uid': metadata['UID'],
                    })

        parent_modified_date = None

        # create the object if its not existing ...
        new_object = False
        if not object:
            self.logger.info(
                'Object with UID %s does not existing: creating new object' % (
                    metadata['UID'],
                )
            )
            # ... find container
            container = self._findContainerObjectByPath(absPath)
            try:
                parent_modified_date = container.modified()
            except AttributeError:
                pass
            if not container:
                raise states.ErrorState('Could not find container of %s' %
                                        absPath)
            self.logger.info('... container: "%s" at %s' % (
                container.Title(),
                '/'.join(container.getPhysicalPath()),
            ))
            # ... create object
            object = container.get(container.invokeFactory(
                metadata['portal_type'],
                metadata['id'],
            ))

            if hasattr(aq_base(object), '_setUID'):
                object._setUID(metadata['UID'])

            else:
                setattr(object,
                        plone.uuid.interfaces.ATTRIBUTE_NAME,
                        metadata['UID'])

                notify(ObjectAddedEvent(object))

            # object.processForm()
            new_object = True

        else:
            try:
                parent_modified_date = object.aq_inner.aq_parent.modified()
            except AttributeError:
                pass

        # finalize
        if hasattr(aq_base(object), 'processForm'):
            object.processForm()

        if not is_root:
            # set review_state
            pm = self.context.portal_membership
            current_user = pm.getAuthenticatedMember().getId()
            wt = self.context.portal_workflow
            wf_ids = wt.getChainFor(object)
            state = metadata['review_state']
            if state and wf_ids:
                wf_id = wf_ids[0]
                comment = 'state set to: %s' % state
                wt.setStatusOf(wf_id, object, {'review_state': state,
                                               'action': state,
                                               'actor': current_user,
                                               'time': DateTime(),
                                               'comments': comment, })
                wf = wt.getWorkflowById(wf_id)
                wf.updateRoleMappingsFor(object)

        # updates all data with the registered adapters for IDataCollector
        adapters = sorted(getAdapters((object, ), IDataCollector))
        for name, adapter in adapters:
            data = self.decoder.unserializeFields(object, name)
            adapter.setData(data[name], metadata)

        # set object position
        if not is_root:
            self.updateObjectPosition(object, metadata)

        # reindex
        if not is_root:
            object.reindexObject()

        catalog_tool = self.context.portal_catalog
        # re-set the modification date - this must be the last modifying access
        if metadata.get('modified'):
            modifiedDate = DateTime(metadata['modified'])
            object.setModificationDate(modifiedDate)
            if not is_root:
                catalog_tool.catalog_object(object,
                                            '/'.join(object.getPhysicalPath()))

        if parent_modified_date:
            parent = object.aq_inner.aq_parent
            parent.setModificationDate(parent_modified_date)
            catalog_tool.catalog_object(object,
                                        '/'.join(object.getPhysicalPath()))

        # return the appropriate CommunicationState - notify events
        if new_object:
            event.notify(AfterCreatedEvent(object))
            return states.ObjectCreatedState()
        else:
            event.notify(AfterUpdatedEvent(object))
            return states.ObjectUpdatedState()

    def moveAction(self, metadata, data):
        """
        Move or rename object by the given data.
        'move' contains the following keys
        - newName
        - newParent
        - oldName
        - oldParent
        - newTitle

        @param metadata:        metadata dictionary containing UID,
        portal_type, action, physicalPath and sibling_positions
        @param data
        @type data              dict
        @type metadata:         dict
        @return:                CommunicationState instance
        @rtype:                 ftw.publisher.core.states.CommunicationState
        """
        # find the object
        object = self._getObjectByUID(metadata['UID'])
        if not object:
            raise states.ObjectNotFoundForMovingWarning()

        move_data = 'move' in data and data['move'] or None
        if not move_data:
            return states.PartialError('Missing move part')

        obj_path = '/'.join(object.getPhysicalPath())

        # check if object has moved by comparing the parents
        if move_data['newParent'] == move_data['oldParent']:
            # rename the object
            putils = object.plone_utils
            paths = [obj_path, ]
            new_ids = [move_data['newName'], ]
            new_titles = [move_data['newTitle'].encode('utf-8'), ]
            success, failure = putils.renameObjectsByPaths(
                paths,
                new_ids,
                new_titles)
            if failure:
                return states.CouldNotMoveError(
                    u'Object on %s could not be renamed/moved (%s)' % (
                        obj_path,
                        failure.get(obj_path).__str__()))

        else:
            # object has been moved
            portal_path = '/'.join(
                self.context.portal_url.getPortalObject().getPhysicalPath())
            old_parent_path = portal_path + move_data['oldParent']
            real_old_parent_path = '/'.join(object.aq_parent.getPhysicalPath())
            if old_parent_path == real_old_parent_path:
                # The object is where we expect it
                old_parent = object.restrictedTraverse(old_parent_path)
            else:
                # old parent does not exist
                # try to move the object by using the real_old_parent_path
                old_parent = object.restrictedTraverse(real_old_parent_path)

            try:
                new_parent = object.restrictedTraverse(
                    portal_path + move_data['newParent'])
                cutted = old_parent.manage_cutObjects(object.id)
                new_parent.manage_pasteObjects(cutted)
            except (KeyError, AttributeError):
                # The new parent does not exist.
                # Delete the object, because we cannot move it
                # Raise exception anyway...
                old_parent.manage_delObjects([object.id])
                return states.CouldNotMoveError(
                    u'Object on %s could not be renamed/moved (%s)' % (
                        obj_path,
                        'Target parent does not exist, source object deleted'))

        # return a ObjectMovedState() instance
        return states.ObjectMovedState()

    def deleteAction(self, metadata):
        """
        Deletes the object identified by metadata values.

        @param metadata:        metadata dict containing UID, portal_type,
        action, physicalPath and sibling_positions
        @type metadata:         dict
        @return:                CommunicationState instance
        @rtype:                 ftw.publisher.core.states.CommunicationState
        """
        # find the object
        object = self._getObjectByUID(metadata['UID'])
        if not object:
            raise states.ObjectNotFoundForDeletingWarning()
        # delete the object
        self.logger.info('Removing object with UID %s' % metadata['UID'])
        container = object.aq_inner.aq_parent
        container.manage_delObjects([object.id])
        # return a ObjectDeletedState() instance
        return states.ObjectDeletedState()

    def _getObjectByUID(self, uid):
        """
        Searches a Object by UID in the plone reference_catalog.
        If the Plone-Object could not be found, it will return None.

        @param uid:     UID of the object to search for
        @type uid:      string
        @return:        Plone-Object or None
        """
        return uuidToObject(uid)

    def _getObjectByPath(self, absolutePath):
        """
        Searches a Object by the absolute path of the object.
        Path example: /data-fs/ploneSite/folder/object

        @param absolutePath:    Absolute path to the object to search for
        @type absolutePath:     string
        @return:                Plone-Object or None
        """
        # plone site root is not in catalog ...
        portalObject = self.context.portal_url.getPortalObject()
        portalPath = '/'.join(portalObject.getPhysicalPath())
        if absolutePath == portalPath:
            # plone site root is searched, return it
            return portalObject
        # for any other object we use the catalog tool
        brains = self.context.portal_catalog({
            'path': {
                'query': absolutePath,
                'depth': 0,
            },
        })
        if len(brains) == 0:
            return None
        else:
            return brains[0].getObject()

    def _findContainerObjectByPath(self, absoluteObjectPath):
        """
        Searches the Container of the currently not existing Plone-Object which
        will be created.

        @param absoluteObjectPath:  Absolute path to the object (which does not
        exist yet
        @type absoluteObjectPath:   string
        @return:                    Folderish Plone-Object or None
        """
        # get the path to the "parent" object
        containerPath = os.path.dirname(absoluteObjectPath)
        # search and return the "parent" object
        return self._getObjectByPath(containerPath)

    def _getAbsolutePath(self, relativePath):
        """
        Converts a relative path (relative to Plone Site-Root) to a absolute
        Path (containing the full URI from zope-Root object).
        No path validation is done!
        Example:
        relativePath :=     /folder/object
        absolutePath :=     /ploneSite/folder/object

        @param relativePath:    Any relative path
        @type relativePath:     string
        @return:                Absolute Path
        @rtype:                 string
        """
        # get the portal path (path to plone site)
        portalObject = self.context.portal_url.getPortalObject()
        portalPath = '/'.join(portalObject.getPhysicalPath())
        # concatinate with portalPath with relativePath
        # handle plone root
        if relativePath == '/':
            return portalPath
        return portalPath + relativePath

    def updateObjectPosition(self, object, metadata):
        """
        Updates the position of the object and it siblings (reset position of
        all children of the parent object).
        Objects, which do not exist at the sender instance, are moved to the
        bottom.

        @param metadata:        metadata dict containing UID, portal_type,
        action, physicalPath and sibling_positions
        @type metadata:         dict
        @return:                None
        """
        positions = metadata['sibling_positions']
        parent = object.aq_inner.aq_parent
        object_ids = list(parent.objectIds())

        # move objects with no position info to the bottom
        for id in object_ids:
            if id not in positions.keys():
                positions[id] = len(positions.keys())

        # sort ids by positions
        object_ids.sort(lambda a, b: cmp(positions[a], positions[b]))

        # order objects
        parent.moveObjectsByDelta(object_ids, -len(object_ids))

        # reindex all objects
        for id in object_ids:
            try:
                parent.get(id).reindexObject(
                    idxs=['positionInParent', 'getObjPositionInParent'])
            except:
                pass


class TestConnection(BrowserView):
    """
    This BrowserView is used by the configlet of the module
    ftw.publisher.sender
    to test a connection to the receiever.
    """

    def __call__(self, *args, **kwargs):
        """
        Returns a 'ok' if the context is a Plone Site, otherwise
        it returns 'Not a Plone-Site'.
        @return:        Success message
        @rtype:         string
        """
        if IPloneSiteRoot.providedBy(self.context):
            return 'ok'
        else:
            return 'Not a Plone-Site'
