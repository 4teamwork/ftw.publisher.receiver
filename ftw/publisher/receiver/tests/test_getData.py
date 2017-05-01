from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.receiver.tests import IntegrationTestCase
from ftw.publisher.receiver.browser.views import GetSavedData
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from Products.CMFCore.utils import getToolByName


class TestGetData(IntegrationTestCase):

    def setUp(self):
        super(TestGetData, self).setUp()

        self.grant('Manager')
        self.types_tool = getToolByName(self.portal, 'portal_types')
        self.types_tool['Plone Site'].allowed_content_types = ('FormFolder',)

        self.formfolder = create(Builder('form folder'))
        self.save_data_adapter = create(Builder(
            'save data adapter').within(self.formfolder))

        self.data_string = "hans@muster.ch, Test, only a Test \n \
                           peter@muster.ch, another Test, Still a Test"

        self.save_data_adapter.setSavedFormInput(self.data_string)

    def test_get_formfolder_data(self):
        view = GetSavedData(self.portal, self.portal.REQUEST)
        self.portal.REQUEST['download_format'] = 'csv'
        self.portal.REQUEST['uid'] = self.save_data_adapter.UID()
        data = view()
        lines = data.split('\r\n')
        self.assertIn("hans@muster.ch, Test, only a Test", lines[0])
        self.assertIn("peter@muster.ch, another Test, Still a Test", lines[1])
