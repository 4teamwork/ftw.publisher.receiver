from ftw.publisher.receiver.testing import RECEIVER_INTEGRATION
from path import Path
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest2 import TestCase


class IntegrationTestCase(TestCase):
    layer = RECEIVER_INTEGRATION

    def setUp(self):
        self.portal = self.layer['portal']

    def grant(self, *roles):
        setRoles(self.portal, TEST_USER_ID, list(roles))

    def asset(self, filename):
        filepath = Path(__file__).parent.joinpath('jobs', filename)
        assert filepath.isfile(), 'Missing asset "{0}" at {1}'.format(filepath, filepath)
        return filepath
