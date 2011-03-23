from Products.PloneTestCase import ptc
from ftw.publisher.receiver.testing import receiver_integration_layer


class ReceiverTestCase(ptc.PloneTestCase):
    """Base class for integration tests."""

    layer = receiver_integration_layer
