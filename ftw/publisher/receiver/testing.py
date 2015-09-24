from ftw.builder.testing import BUILDER_LAYER
from ftw.testing.layer import COMPONENT_REGISTRY_ISOLATION
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from zope.configuration import xmlconfig


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


RECEIVER_FIXTURE = ReceiverLayer()
RECEIVER_INTEGRATION = IntegrationTesting(
    bases=(RECEIVER_FIXTURE, ),
    name="ftw.publisher.receiver:integration")
