from ftw.builder.testing import BUILDER_LAYER
from ftw.testing import IS_PLONE_5
from ftw.testing.layer import COMPONENT_REGISTRY_ISOLATION
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from zope.configuration import xmlconfig
import ftw.publisher.receiver.tests.builders


class ReceiverLayer(PloneSandboxLayer):
    defaultBases = (COMPONENT_REGISTRY_ISOLATION, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

        z2.installProduct(app, 'Products.PloneFormGen')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'Products.PloneFormGen:default')
        if IS_PLONE_5:
            applyProfile(portal, 'plone.app.contenttypes:default')

RECEIVER_FIXTURE = ReceiverLayer()
RECEIVER_INTEGRATION = IntegrationTesting(
    bases=(RECEIVER_FIXTURE, ),
    name="ftw.publisher.receiver:integration")
