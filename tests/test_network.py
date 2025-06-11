import unittest
from network.client import NetworkClient

class TestNetworkClient(unittest.TestCase):
    def test_serialize_deserialize(self):
        client = NetworkClient()
        data = {"temperature": 22.5}
        raw = client._serialize(data)
        parsed = client._deserialize(raw)
        self.assertEqual(data, parsed)
