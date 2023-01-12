import zmq
import json
import unittest
import argparse

import datetime

class TestClient(unittest.TestCase):

    def setUp(self):
        self.provider_address = "192.168.1.196"
        self.context = zmq.Context()
        self.socket  = self.context.socket(zmq.DEALER)
        self.socket.connect(f"tcp://{args.server_address}:{args.server_port}")

        payload =  {
            "command": "connect",
            "msg": {
                "ip": self.provider_address,
                "slot": 0,
                "timeout": 5,
                "micro800": False
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        expected = {
            "command": "connect",
            "msg": {
                "name": None,
                "value": None,
                "status": "Success"
            }
        }
        assert decoded_msg == expected

    def _send(self, payload: dict):
        encoded = json.dumps(payload).encode("utf-8")
        self.socket.send_multipart([encoded,])

    def _recv(self):
        server_id, raw_msg = self.socket.recv_multipart()
        decoded_msg = json.loads(raw_msg.decode("utf-8"))
        return server_id, decoded_msg

    def test_get_connection_size(self):
        payload =  {
            "command": "get-connection-size",
            "msg": None
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "get-connection-size",
            decoded_msg["msg"]["name"] is None,
            decoded_msg["msg"]["status"] == "Success",
            decoded_msg["msg"]["status"] is not None
        ])

    def test_set_connection_size(self):
        payload =  {
            "command": "set-connection-size",
            "msg": {
                "connection_size": 508
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "set-connection-size",
            decoded_msg["msg"]["name"] == None,
            decoded_msg["msg"]["status"] == "Success",
            decoded_msg["msg"]["status"] is not None
        ])

    def test_read_single(self):
        payload =  {
            "command": "read",
            "msg": {
                "tag": "BaseINT",
                "count": 1,
                "datatype": 195
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "read",
            decoded_msg["msg"]["name"] == payload["msg"]["tag"],
            decoded_msg["msg"]["status"] == "Success",
            decoded_msg["msg"]["value"] is not None
        ])

    def test_read_list(self):
        payload =  {
            "command": "read",
            "msg": {
                "tag": [
                    "BaseINTArray[0]",
                    "BaseINTArray[1]",
                    "BaseINTArray[2]"
                ],
                "count": None,
                "datatype": None
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert decoded_msg["command"] == "read"
        for idx, x in enumerate(decoded_msg["msg"]):
            assert all([
                x["name"] == payload["msg"]["tag"][idx],
                x["status"] == "Success"
            ])

    def test_write_single(self):
        payload =  {
            "command": "write",
            "msg": {
                "tag": "BaseINT",
                "value": 1,
                "datatype": 195
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "write",
            decoded_msg["msg"]["name"] == payload["msg"]["tag"],
            decoded_msg["msg"]["status"] == "Success",
            decoded_msg["msg"]["value"] is not None
        ])

    def test_write_list(self):
        payload =  {
            "command": "write",
            "msg": [
                ["BaseINTArray[0]", 1],
                ["BaseINTArray[1]", 2],
                ["BaseINTArray[2]", 3]
            ]
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert decoded_msg["command"] == "write"
        for idx, x in enumerate(decoded_msg["msg"]):
            assert all([
                x["name"] == payload["msg"][idx][0],
                x["status"] == "Success",
                x["value"] is not None
            ])

    def test_get_plc_time(self):
        payload =  {
            "command": "get-plc-time",
            "msg": {
                "raw": False
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "get-plc-time",
            decoded_msg["msg"]["name"] == None,
            decoded_msg["msg"]["status"] == "Success"
        ])
        date_time = datetime.datetime.strptime(decoded_msg["msg"]["value"], '%Y-%m-%d %H:%M:%S.%f')

    def test_set_plc_time(self):
        payload = {
            "command": "set-plc-time",
            "msg": None
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "set-plc-time",
            decoded_msg["msg"]["name"] is None,
            decoded_msg["msg"]["status"] == "Success"
        ])
        date_time = datetime.datetime.utcfromtimestamp(decoded_msg["msg"]["value"])

    def test_get_tag_list(self):
        payload =  {
            "command": "get-tag-list",
            "msg": {
                "all_tags": True
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "get-tag-list",
            decoded_msg["msg"]["name"] is None,
            isinstance(decoded_msg["msg"]["value"], list),
            decoded_msg["msg"]["status"] == "Success"
        ])
        for x in decoded_msg["msg"]["value"]:
            assert all([
                isinstance(x["TagName"], str),
                isinstance(x["InstanceID"], int),
                isinstance(x["SymbolType"], int),
                isinstance(x["DataTypeValue"], (bool, int, float, str)),
                isinstance(x["DataType"], str),
                isinstance(x["Array"], int),
                isinstance(x["Struct"], int),
                isinstance(x["Size"], int),
                x["AccessRight"] is None,
                x["Internal"] is None,
                x["Meta"] is None,
                x["Scope0"] is None,
                x["Scope1"] is None,
                x["Bytes"] is None
            ])

    def test_get_program_tag_list(self):
        payload =  {
            "command": "get-program-tag-list",
            "msg": {
                "program_name": ""
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "get-program-tag-list",
            decoded_msg["msg"]["name"] is None,
            isinstance(decoded_msg["msg"]["value"], list),
            decoded_msg["msg"]["status"] == "Success",
        ])
        for x in decoded_msg["msg"]["value"]:
            assert all([
                isinstance(x["TagName"], str),
                isinstance(x["InstanceID"], int),
                isinstance(x["SymbolType"], int),
                isinstance(x["DataTypeValue"], (bool, int, float, str)),
                isinstance(x["DataType"], str),
                isinstance(x["Array"], int),
                isinstance(x["Struct"], int),
                isinstance(x["Size"], int),
                x["AccessRight"] is None,
                x["Internal"] is None,
                x["Meta"] is None,
                x["Scope0"] is None,
                x["Scope1"] is None,
                x["Bytes"] is None
            ])

    def test_get_programs_list(self):
        payload = {
            "command": "get-programs-list",
            "msg": None
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "get-programs-list",
            decoded_msg["msg"]["name"] == None,
            decoded_msg["msg"]["status"] == "Success"
        ])
        for x in decoded_msg["msg"]["value"]:
           assert isinstance(x, str)

    def test_discover(self):
        payload = {
            "command": "discover",
            "msg": None
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "discover",
            decoded_msg["msg"]["name"] == None,
            decoded_msg["msg"]["status"] == "Success"
        ])
        for x in decoded_msg["msg"]["value"]:
            assert all([
                isinstance(x["Length"], int),
                isinstance(x["EncapsulationVersion"], int),
                isinstance(x["IPAddress"], str),
                isinstance(x["VendorID"], int),
                isinstance(x["Vendor"], str),
                isinstance(x["DeviceID"], int),
                x["DeviceType"] is None,
                isinstance(x["ProductCode"], int),
                isinstance(x["Revision"], float),
                isinstance(x["Status"], int),
                isinstance(x["SerialNumber"], int),
                isinstance(x["ProductNameLength"], int),
                isinstance(x["ProductName"], str),
                isinstance(x["State"], int)
            ])

    def test_get_module_properties(self):
        payload = {
            "command": "get-module-properties",
            "msg": {
                "slot": 0
            }
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "get-module-properties",
            decoded_msg["msg"]["name"] == None,
            isinstance(decoded_msg["msg"]["value"]["Length"], int),
            isinstance(decoded_msg["msg"]["value"]["EncapsulationVersion"], int),
            isinstance(decoded_msg["msg"]["value"]["IPAddress"], str),
            isinstance(decoded_msg["msg"]["value"]["VendorID"], int),
            isinstance(decoded_msg["msg"]["value"]["Vendor"], str),
            isinstance(decoded_msg["msg"]["value"]["DeviceID"], int),
            decoded_msg["msg"]["value"]["DeviceType"] is None,
            isinstance(decoded_msg["msg"]["value"]["ProductCode"], int),
            isinstance(decoded_msg["msg"]["value"]["Revision"], float),
            isinstance(decoded_msg["msg"]["value"]["Status"], int),
            isinstance(decoded_msg["msg"]["value"]["SerialNumber"], int),
            isinstance(decoded_msg["msg"]["value"]["ProductNameLength"], int),
            isinstance(decoded_msg["msg"]["value"]["ProductName"], str),
            isinstance(decoded_msg["msg"]["value"]["State"], int),
            decoded_msg["msg"]["status"] == "Success"
        ])

    def test_get_device_properties(self):
        payload = {
            "command": "get-device-properties",
            "msg": None
        } 
        self._send(payload)
        server_id, decoded_msg = self._recv()
        assert all([
            decoded_msg["command"] == "get-device-properties",
            decoded_msg["msg"]["name"] == None,
            isinstance(decoded_msg["msg"]["value"]["Length"], int),
            isinstance(decoded_msg["msg"]["value"]["EncapsulationVersion"], int),
            isinstance(decoded_msg["msg"]["value"]["IPAddress"], str),
            isinstance(decoded_msg["msg"]["value"]["VendorID"], int),
            isinstance(decoded_msg["msg"]["value"]["Vendor"], str),
            isinstance(decoded_msg["msg"]["value"]["DeviceID"], int),
            decoded_msg["msg"]["value"]["DeviceType"] is None,
            isinstance(decoded_msg["msg"]["value"]["ProductCode"], int),
            isinstance(decoded_msg["msg"]["value"]["Revision"], float),
            isinstance(decoded_msg["msg"]["value"]["Status"], int),
            isinstance(decoded_msg["msg"]["value"]["SerialNumber"], int),
            isinstance(decoded_msg["msg"]["value"]["ProductNameLength"], int),
            isinstance(decoded_msg["msg"]["value"]["ProductName"], str),
            isinstance(decoded_msg["msg"]["value"]["State"], int),
            decoded_msg["msg"]["status"] == "Success"
        ])

    def tearDown(self):
        payload = {
            "command": "close",
            "msg": None
        }
        self._send(payload)
        server_id, decoded_msg = self._recv()
        expected = {
            "command": "close",
            "msg": {
                "name": None,
                "value": None,
                "status": "Success"
            }
        }
        assert decoded_msg == expected
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="pylogix-as-service-tester",
        description="Tests the pylogix as service wrapper."
    )
    parser.add_argument(
        '--server-address',
        dest="server_address",
        required=True,
        help="The address for this service to bind to, eg. 127.0.0.1."
    )
    parser.add_argument(
        '--server-port',
        dest="server_port",
        required=True,
        help="The port for this service to list on, eg. 7777."
    )
    args = parser.parse_args()
    unittest.main(argv=[''])
