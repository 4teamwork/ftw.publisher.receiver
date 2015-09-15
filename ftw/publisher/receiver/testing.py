from zope.configuration import xmlconfig
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from ftw.builder.testing import BUILDER_LAYER
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer


class ReceiverLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

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


class ReceiverIntegrationLayer(BasePTCLayer):
    """Layer for integration tests."""

    def afterSetUp(self):
        pass

    def beforeTearDown(self):
        pass


receiver_integration_layer = ReceiverIntegrationLayer(bases=[ptc_layer])
