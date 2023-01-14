import zmq
import zmq.asyncio
import json
import asyncio
from pylogix import PLC

from logger import log_exception
from mock import MockPLC

class Service:
    def __init__(self, url, simulate=False) -> None:
        self.plc = None
        self.simulate_plc = simulate
        self.ctx = zmq.asyncio.Context()
        self.sock = self.ctx.socket(zmq.ROUTER)
        self.sock.setsockopt(zmq.LINGER, 0)
        self.sock.bind(url)
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.sock, zmq.POLLIN)
        self.command_lookup = {
            "connect":               self._connect,
            "close":                 self._close,
            "get-connection-size":   self._get_connection_size,
            "set-connection-size":   self._set_connection_size,
            "read":                  self._read,
            "write":                 self._write,
            "get-plc-time":          self._get_plc_time,
            "set-plc-time":          self._set_plc_time,
            "get-tag-list":          self._get_tag_list,
            "get-program-tag-list":  self._get_program_tag_list,
            "get-programs-list":     self._get_programs_list,
            "discover":              self._discover,
            "get-module-properties": self._get_module_properties,
            "get-device-properties": self._get_device_properties
        }
        self.responses = {
            "UNKNOWN": "Unknown Command",
            "BAD_FORMAT": "Bad Message Format",
            "ERROR": "Internal Server Error",
            "NO_CONNECTION": "No Route To Provider",
            "SUCCESS": "Success"
        }
        self.no_connection_msg = {
            "name":None,
            "value":None,
            "status":self.responses["NO_CONNECTION"]
        }

    async def start(self):
        while True:
            events = await self.poller.poll()
            if self.sock in dict(events):
                try: 

                    # try to receive the request
                    # ----------------------
                    consumer_id, raw_msg = await self.sock.recv_multipart()
                    decoded_msg = json.loads(raw_msg.decode("utf-8"))

                    # try to process the request
                    # ----------------------
                    response = await self._process(decoded_msg)

                    # try to reply to the request
                    # -----------------------
                    encoded = json.dumps(response).encode("utf-8")
                    await self.sock.send_multipart([consumer_id, b'', encoded])

                except Exception as e:
                    await log_exception(
                        message="failed in main loop",
                        payload=None,
                        exception=e
                    )
                    encoded = json.dumps({
                        "name":None,
                        "value":None,
                        "status":self.responses["ERROR"]
                    }).encode("utf-8")
                    await self.sock.send_multipart([
                        consumer_id,
                        b'',
                        encoded
                    ])

    async def _process(self, payload):
        try:
            assert "command" in payload
            process_func = self.command_lookup.get(payload["command"], None)
            if process_func:
                return await process_func(payload)
            else:
                return await self._unknown(payload)
        except AssertionError:
            return await self._bad_format()

    async def _bad_format(self):
        msg = {
            "name":None,
            "value":None,
            "status":self.responses["BAD_FORMAT"]
        }
        return msg

    async def _assert_root_msg(self, payload):
        assert all([
            payload,
            isinstance(payload, dict),
            "command" in payload,
            "msg" in payload
        ])

    # connect
    # ----------------------
    async def _connect(self, payload):
        """Initialize our parameters."""
        try:
            await self._assert_root_msg(payload)
            assert all([
                "ip" in payload["msg"],
                "slot" in payload["msg"],
                "timeout" in payload["msg"],
                "micro800" in payload["msg"]
            ])

            await asyncio.to_thread(self._sync_connect, self.simulate_plc, payload["msg"])

            msg = {
                "name":None,
                "value":None,
                "status":self.responses["SUCCESS"]
            }
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to connect to the plc",
                payload=payload,
                exception=e
            )
            raise e

    def _sync_connect(self, simulate, payload):
        if simulate:
            plc = MockPLC(
                    ip_address=payload["ip"],
                    slot=payload["slot"],
                    timeout=payload["timeout"],
                    Micro800=payload["micro800"]
            )
        else:
            plc = PLC(
                    ip_address=payload["ip"],
                    slot=payload["slot"],
                    timeout=payload["timeout"],
                    Micro800=payload["micro800"]
            )
        self.plc = plc

    # get connection size
    # ----------------------
    async def _get_connection_size(self, payload):
        """ Returns the ConnectionSize value."""
        try:
            await self._assert_root_msg(payload)
            if self.plc:
                connection_size = await asyncio.to_thread(self._sync_get_connection_size)
                msg = {
                    "name":None,
                    "value":connection_size,
                    "status":self.responses["SUCCESS"]
                }
            else:
                msg = self.no_connection_msg
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to get connection size.",
                payload=None,
                exception=e
            )
            raise e 

    def _sync_get_connection_size(self):
        return self.plc.ConnectionSize

    # set connection size
    # ----------------------
    async def _set_connection_size(self, payload):
        """Set the ConnectionSize before initiating the first
        call requiring conn.connect(). The default behavior
        is to attempt a Large followed by a Small Forward Open.
        If an Explicit (Unconnected) session is used, 
        picks a sensible default."""
        try:
            await self._assert_root_msg(payload)
            assert all([
                "connection_size" in payload["msg"]
            ])

            if self.plc:
                await asyncio.to_thread(self._sync_set_connection_size, payload["msg"])
            else:
                pass

            msg = {
                "name":None,
                "value":payload["msg"]["connection_size"],
                "status":self.responses["SUCCESS"]
            }
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to get connection size.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_set_connection_size(self, payload):
        self.plc.ConnectionSize = payload["connection_size"]

    # read
    # ----------------------
    async def _read(self, payload):
        """We have two options for reading depending on
        the arguments, read a single tag, or read an array"""
        try:
            await self._assert_root_msg(payload)
            assert all([
                "tag" in payload["msg"],
                "count" in payload["msg"],
                "datatype" in payload["msg"]
            ])
            if isinstance(payload["msg"]["tag"], list):
                assert all([
                    payload["msg"]["count"] == None,
                    payload["msg"]["datatype"] == None
                ])
                for x in payload["msg"]["tag"]:
                    assert isinstance(x, str)
            else:
                assert all([
                    "tag" in payload["msg"],
                    "count" in payload["msg"],
                    "datatype" in payload["msg"]
                ])

            if self.plc:
                res = await asyncio.to_thread(self._sync_read, payload["msg"])
                if isinstance(res, list):
                    container = []
                    for x in res:
                        container.append({
                            "name":x.TagName, 
                            "value":x.Value, 
                            "status":x.Status
                        })
                    msg = container
                else:
                    msg = {
                        "name":res.TagName,
                        "value":res.Value,
                        "status":res.Status
                    }
            else:
                msg = self.no_connection_msg

            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to read from the target plc",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_read(self, payload):
        if isinstance(payload, list):
            tag      = payload
            count    = None
            datatype = None
        else:
            tag      = payload.get("tag", None)
            count    = payload.get("count", None)
            datatype = payload.get("datatype", None)
        return self.plc.Read(tag=tag, count=count, datatype=datatype)

    # write
    # ----------------------
    async def _write(self, payload):
        """We have two options for writing depending on 
        the arguments, write a single tag, or write an array."""
        try:
            await self._assert_root_msg(payload)
            if isinstance(payload["msg"], list):
                for x in payload["msg"]:
                    assert all([
                        isinstance(x[0], str),
                        isinstance(x[1], (str, int, bool, float))
                    ])
            else:
                assert all([
                    "tag" in payload["msg"],
                    "value" in payload["msg"],
                    "datatype" in payload["msg"]
                ])

            if self.plc:
                res = await asyncio.to_thread(self._sync_write, payload["msg"])
                if isinstance(res, list):
                    container = []
                    for x in res:
                        container.append({
                            "name":x.TagName,
                            "value":x.Value,
                            "status":x.Status
                        })
                    msg = container
                else:
                    msg = {
                        "name":res.TagName,
                        "value":res.Value,
                        "status":res.Status
                    }
            else:
                msg = self.no_connection_msg
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to write to the target plc.",
                payload=payload,
                exception=e
            )
            raise e  

    def _sync_write(self, payload):
        if isinstance(payload, list):
            tag      = payload
            value    = None
            datatype = None
        else:
            tag      = payload.get("tag", None)
            value    = payload.get("value", None)
            datatype = payload.get("datatype", None)
        return self.plc.Write(tag=tag, value=value, datatype=datatype)

    # get plc time
    # ----------------------
    async def _get_plc_time(self, payload):
        """Get the PLC's clock time, return as human
        readable (default) or raw if raw=True."""
        try:
            await self._assert_root_msg(payload)
            assert all([
                "raw" in payload["msg"]
            ])

            if self.plc:
                res = await asyncio.to_thread(self._sync_get_plc_time, payload["msg"])
                msg = {
                    "name":res.TagName,
                    "value":str(res.Value),
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg

            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to get target plc time.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_get_plc_time(self, payload):
        return self.plc.GetPLCTime(raw=payload["raw"])

    # set plc time
    # ----------------------
    async def _set_plc_time(self, payload):
        """Sets the PLC's clock time."""
        try:
            await self._assert_root_msg(payload)

            if self.plc:
                res = await asyncio.to_thread(self._sync_set_plc_time)
                msg = {
                    "name":res.TagName,
                    "value":res.Value,
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg

            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to set the target plc time.",
                payload=payload,
                exception=e
            )
            raise e

    def _sync_set_plc_time(self):
        return self.plc.SetPLCTime()

    # get tag list
    # ----------------------
    async def _get_tag_list(self, payload):
        """Retrieves the tag list from the PLC
        Optional parameter allTags set to True
        If is set to False, it will return only controller
        otherwise controller tags and program tags."""
        try:
            await self._assert_root_msg(payload)
            assert all([
                "all_tags" in payload["msg"]
            ])

            if self.plc:
                res = await asyncio.to_thread(self._sync_get_tag_list, payload["msg"])
                if isinstance(res.Value, list):
                    for idx, x in enumerate(res.Value):
                        res.Value[idx] = {
                            "TagName":x.TagName,
                            "InstanceID":x.InstanceID,
                            "SymbolType":x.SymbolType,
                            "DataTypeValue":x.DataTypeValue,
                            "DataType":x.DataType,
                            "Array":x.Array,
                            "Struct":x.Struct,
                            "Size":x.Size,
                            "AccessRight":x.AccessRight,
                            "Internal":x.Internal,
                            "Meta":x.Meta,
                            "Scope0":x.Scope0,
                            "Scope1":x.Scope1,
                            "Bytes":x.Bytes
                        }
                elif res.Value is not None:
                    res.Value = {
                        "TagName":res.Value.TagName,
                        "InstanceID":res.Value.InstanceID,
                        "SymbolType":res.Value.SymbolType,
                        "DataTypeValue":res.Value.DataTypeValue,
                        "DataType":res.Value.DataType,
                        "Array":res.Value.Array,
                        "Struct":res.Value.Struct,
                        "Size":res.Value.Size,
                        "AccessRight":res.Value.AccessRight,
                        "Internal":res.Value.Internal,
                        "Meta":res.Value.Meta,
                        "Scope0":res.Value.Scope0,
                        "Scope1":res.Value.Scope1,
                        "Bytes":res.Value.Bytes
                    }
                else:
                    pass
                msg = {
                    "name":res.TagName,
                    "value":res.Value,
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg

            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to get tag list.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_get_tag_list(self, payload):
        return self.plc.GetTagList(allTags=payload["all_tags"])

    # get program tag list
    # ----------------------
    async def _get_program_tag_list(self, payload):
        """Retrieves a program tag list from the PLC
        programName = "Program:ExampleProgram"."""
        try:
            await self._assert_root_msg(payload)
            assert all([
                "program_name" in payload["msg"]
            ])

            if self.plc:
                res = await asyncio.to_thread(self._sync_get_program_tag_list, payload["msg"])
                if isinstance(res.Value, list):
                    for idx, x in enumerate(res.Value):
                        res.Value[idx] = {
                            "TagName":x.TagName,
                            "InstanceID":x.InstanceID,
                            "SymbolType":x.SymbolType,
                            "DataTypeValue":x.DataTypeValue,
                            "DataType":x.DataType,
                            "Array":x.Array,
                            "Struct":x.Struct,
                            "Size":x.Size,
                            "AccessRight":x.AccessRight,
                            "Internal":x.Internal,
                            "Meta":x.Meta,
                            "Scope0":x.Scope0,
                            "Scope1":x.Scope1,
                            "Bytes":x.Bytes
                        }
                elif res.Value is not None:
                    res.Value = {
                        "TagName":res.Value.TagName,
                        "InstanceID":res.Value.InstanceID,
                        "SymbolType":res.Value.SymbolType,
                        "DataTypeValue":res.Value.DataTypeValue,
                        "DataType":res.Value.DataType,
                        "Array":res.Value.Array,
                        "Struct":res.Value.Struct,
                        "Size":res.Value.Size,
                        "AccessRight":res.Value.AccessRight,
                        "Internal":res.Value.Internal,
                        "Meta":res.Value.Meta,
                        "Scope0":res.Value.Scope0,
                        "Scope1":res.Value.Scope1,
                        "Bytes":res.Value.Bytes
                    }
                else:
                    pass
                msg = {
                    "name":res.TagName,
                    "value":res.Value,
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg

            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="Provider failed to get program tag list.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_get_program_tag_list(self, payload):
        return self.plc.GetProgramTagList(programName=payload["program_name"])

    # get programs list
    # ----------------------
    async def _get_programs_list(self, payload):
        """Retrieves a program names list from the PLC."""
        try:
            await self._assert_root_msg(payload)
            if self.plc:
                res = await asyncio.to_thread(self._sync_get_programs_list)
                msg = {
                    "name":res.TagName,
                    "value":res.Value,
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to get program tag list.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_get_programs_list(self):
        return self.plc.GetProgramsList()

    # discover
    # ----------------------
    async def _discover(self, payload):
        """Query all the EIP devices on the network."""
        try:
            await self._assert_root_msg(payload)
            if self.plc:
                res = await asyncio.to_thread(self._sync_discover)
                if isinstance(res.Value, list):
                    for idx, x in enumerate(res.Value):
                        res.Value[idx] = {
                            "Length":x.Length,
                            "EncapsulationVersion":x.EncapsulationVersion,
                            "IPAddress":x.IPAddress,
                            "VendorID":x.VendorID,
                            "Vendor":x.Vendor,
                            "DeviceID":x.DeviceID,
                            "DeviceType":x.DeviceType,
                            "ProductCode":x.ProductCode,
                            "Revision":x.Revision,
                            "Status":x.Status,
                            "SerialNumber":x.SerialNumber,
                            "ProductNameLength":x.ProductNameLength,
                            "ProductName":x.ProductName,
                            "State":x.State
                    }
                    msg = res.Value
                elif res.Value is not None:
                    res.Value = {
                        "Length":x.Length,
                        "EncapsulationVersion":x.EncapsulationVersion,
                        "IPAddress":x.IPAddress,
                        "VendorID":x.VendorID,
                        "Vendor":x.Vendor,
                        "DeviceID":x.DeviceID,
                        "DeviceType":x.DeviceType,
                        "ProductCode":x.ProductCode,
                        "Revision":x.Revision,
                        "Status":x.Status,
                        "SerialNumber":x.SerialNumber,
                        "ProductNameLength":x.ProductNameLength,
                        "ProductName":x.ProductName,
                        "State":x.State
                    }
                    msg = res.Value
                else:
                    pass
                msg = {
                    "name":res.TagName,
                    "value":res.Value,
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to discover PLCs.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_discover(self):
        return self.plc.Discover()

    # get module properties
    # ----------------------
    async def _get_module_properties(self, payload):
        """Get the properties of module in specified
        slot."""
        try:
            await self._assert_root_msg(payload)
            assert all([
                "slot" in payload["msg"]
            ])

            if self.plc:
                res = await asyncio.to_thread(self._sync_get_module_properties, payload["msg"])
                msg = {
                    "name":res.TagName,
                    "value": {
                        "Length":res.Value.Length,
                        "EncapsulationVersion":res.Value.EncapsulationVersion,
                        "IPAddress":res.Value.IPAddress,
                        "VendorID":res.Value.VendorID,
                        "Vendor":res.Value.Vendor,
                        "DeviceID":res.Value.DeviceID,
                        "DeviceType":res.Value.DeviceType,
                        "ProductCode":res.Value.ProductCode,
                        "Revision":res.Value.Revision,
                        "Status":res.Value.Status,
                        "SerialNumber":res.Value.SerialNumber,
                        "ProductNameLength":res.Value.ProductNameLength,
                        "ProductName":res.Value.ProductName,
                        "State":res.Value.State
                    },
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg

            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to module properties.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_get_module_properties(self, payload):
        return self.plc.GetModuleProperties(slot=payload["slot"])

    # get device properties
    # ----------------------
    async def _get_device_properties(self, payload):
        """Get the device properties of a device at the
        specified IP address."""
        try:
            await self._assert_root_msg(payload)
            if self.plc:
                res = await asyncio.to_thread(self._sync_get_device_properties)
                msg = {
                    "name":res.TagName,
                    "value": {
                        "Length":res.Value.Length,
                        "EncapsulationVersion":res.Value.EncapsulationVersion,
                        "IPAddress":res.Value.IPAddress,
                        "VendorID":res.Value.VendorID,
                        "Vendor":res.Value.Vendor,
                        "DeviceID":res.Value.DeviceID,
                        "DeviceType":res.Value.DeviceType,
                        "ProductCode":res.Value.ProductCode,
                        "Revision":res.Value.Revision,
                        "Status":res.Value.Status,
                        "SerialNumber":res.Value.SerialNumber,
                        "ProductNameLength":res.Value.ProductNameLength,
                        "ProductName":res.Value.ProductName,
                        "State":res.Value.State
                    },
                    "status":res.Status
                }
            else:
                msg = self.no_connection_msg
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to device properties.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_get_device_properties(self):
        return self.plc.GetDeviceProperties()

    # close
    # ----------------------
    async def _close(self, payload):
        """ Closes the connection to the PLC."""
        try:
            await self._assert_root_msg(payload)
            if self.plc:
                await asyncio.to_thread(self._sync_close)
            else:
                pass
            msg = {
                "name":None,
                "value":None, 
                "status":self.responses["SUCCESS"]
            }
            payload["msg"] = msg
            return payload
        except AssertionError:
            return await self._bad_format()
        except Exception as e:
            await log_exception(
                message="failed to close the connection to the target plc.",
                payload=payload,
                exception=e
            )
            raise e 

    def _sync_close(self):
        self.plc.Close()
