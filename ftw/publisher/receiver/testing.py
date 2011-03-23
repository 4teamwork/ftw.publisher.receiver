from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer


class ReceiverIntegrationLayer(BasePTCLayer):
    """Layer for integration tests."""

    def afterSetUp(self):
        pass

    def beforeTearDown(self):
        pass


receiver_integration_layer = ReceiverIntegrationLayer(bases=[ptc_layer])
