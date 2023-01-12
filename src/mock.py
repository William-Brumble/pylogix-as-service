import time
from enum import Enum
from datetime import datetime
from string import ascii_letters
from random import randint, getrandbits, choice

class _DataType(Enum):
    UNKNOWN = 0x00
    STRUCT  = 0xa0
    BOOL    = 0xc1
    SINT    = 0xc2
    INT     = 0xc3
    DINT    = 0xc4
    LINT    = 0xc5
    USINT   = 0xc6
    UINT    = 0xc7
    UDINT   = 0xc8
    LWORD   = 0xc9
    REAL    = 0xca
    LREAL   = 0xcb
    DWORD   = 0xd3
    STRING  = 0xda

class _MockResponse:
    def __init__(self, TagName, Value, Status) -> None:
        self.TagName = TagName
        self.Value = Value
        self.Status = Status

    def __repr__(self):
        return 'Response(TagName={}, Value={}, Status={})'.format(
            self.TagName, self.Value, self.Status)

    def __str__(self):
        return '{} {} {}'.format(self.TagName, self.Value, self.Status)

class _MockTag:
    def __init__(self, TagName):
        self.TagName = TagName
        self.InstanceID = 10
        self.SymbolType = 214
        self.DataTypeValue = 1750
        self.DataType = "AB:ETHERNET_MODULE:C:O"
        self.Array = 0
        self.Struct = 1
        self.Size = 0
        self.AccessRight = None
        self.Internal = None
        self.Meta = None
        self.Scope0 = None
        self.Scope1 = None
        self.Bytes = None

    def __repr__(self):
        props = ''
        props += 'TagName={}, '.format(self.TagName)
        props += 'InstanceID={}, '.format(self.InstanceID)
        props += 'SymbolType={}, '.format(self.SymbolType)
        props += 'DataTypeValue={}, '.format(self.DataTypeValue)
        props += 'DataType={}, '.format(self.DataType)
        props += 'Array={}, '.format(self.Array)
        props += 'Struct={}, '.format(self.Struct)
        props += 'Size={} '.format(self.Size)
        props += 'AccessRight={} '.format(self.AccessRight)
        props += 'Internal={} '.format(self.Internal)
        props += 'Meta={} '.format(self.Meta)
        props += 'Scope0={} '.format(self.Scope0)
        props += 'Scope1={} '.format(self.Scope1)
        props += 'Bytes={}'.format(self.Bytes)
        return 'Tag({})'.format(props)

    def __str__(self):
        return '{} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(
                self.TagName,
                self.InstanceID,
                self.SymbolType,
                self.DataTypeValue,
                self.DataType,
                self.Array,
                self.Struct,
                self.Size,
                self.AccessRight,
                self.Internal,
                self.Meta,
                self.Scope0,
                self.Scope1,
                self.Bytes)

class _MockDevice:
    def __init__(self, address):
        self.Length=0
        self.EncapsulationVersion=0
        self.IPAddress=address
        self.VendorID=1
        self.Vendor='Rockwell Automation/Allen-Bradley'
        self.DeviceID=14
        self.DeviceType=None
        self.ProductCode=167
        self.Revision=20.00
        self.Status=12384
        self.SerialNumber=0xffffff
        self.ProductNameLength=11
        self.ProductName="1756-L84E/B"
        self.State=66

    def __repr__(self):
        props = ''
        props += 'Length={}, '.format(self.Length)
        props += 'EncapsulationVersion={}, '.format(self.EncapsulationVersion)
        props += 'IPAddress={}, '.format(self.IPAddress)
        props += 'VendorID={}, '.format(self.VendorID)
        props += 'Vendor={}, '.format(self.Vendor)
        props += 'DeviceID={}, '.format(self.DeviceID)
        props += 'DeviceType={}, '.format(self.DeviceType)
        props += 'ProductCode={}, '.format(self.ProductCode)
        props += 'Revision={}, '.format(self.Revision)
        props += 'Status={}, '.format(self.Status)
        props += 'SerialNumber={}, '.format(self.SerialNumber)
        props += 'ProductNameLength={}, '.format(self.ProductNameLength)
        props += 'ProductName={}, '.format(self.ProductName)
        props += 'State={}'.format(self.State)
        return 'LGXDevice({})'.format(props)

    def __str__(self):
        ret = "{} {} {} {} {} {} {} {} {} {} {} {} {} {}".format(
                 self.Length,
                 self.EncapsulationVersion,
                 self.IPAddress,
                 self.VendorID,
                 self.Vendor,
                 self.DeviceID,
                 self.DeviceType,
                 self.ProductCode,
                 self.Revision,
                 self.Status,
                 self.SerialNumber,
                 self.ProductNameLength,
                 self.ProductName,
                 self.State)

class MockPLC:
    def __init__(self,
                 ip_address: str,
                 slot: int = 0,
                 timeout: int = 5,
                 Micro800: bool = False) -> None:
        self.IPAddress = ip_address
        self.ProcessorSlot = slot
        self.SocketTimeout = timeout
        self.Micro800 = Micro800
        self._ConnectionSize: int | None = None

    @property
    def ConnectionSize(self):
        return self._ConnectionSize

    @ConnectionSize.setter
    def ConnectionSize(self, connection_size: int):
        self._ConnectionSize = connection_size

    def Close(self) -> None:
        return

    def Read(self, tag, count = 1, datatype = None):
        if datatype:
            datatype = _DataType(datatype)
        if isinstance(tag, list):
            container: list[_MockResponse] = []
            for x in tag:
                match datatype:
                    case _DataType.BOOL:
                        val = bool(getrandbits(1))
                    case _DataType.SINT:
                        val = randint(-128, 127)
                    case _DataType.INT:
                        val = randint(-32768, 32767)
                    case _DataType.DINT:
                        val = randint(-2147483648, 2147483647)
                    case _DataType.STRING:
                        val = ''.join(choice(ascii_letters) for i in range(10))
                    case _:
                        val = None
                container.append(
                    _MockResponse(TagName=x, Value=val, Status="Success")
                )
            return container
        else:
            match datatype:
                case _DataType.BOOL:
                    val = bool(getrandbits(1))
                case _DataType.SINT:
                    val = randint(-128, 127)
                case _DataType.INT:
                    val = randint(-32768, 32767)
                case _DataType.DINT:
                    val = randint(-2147483648, 2147483647)
                case _DataType.STRING:
                    val = ''.join(choice(ascii_letters) for i in range(10))
                case _:
                    val = None
            return _MockResponse(TagName=tag, Value=val, Status="Success")

    def Write(self, tag, value = None, datatype = None):
        if datatype:
            datatype = _DataType(datatype)
        if isinstance(tag, list):
            container: list[_MockResponse] = []
            for x in tag:
                container.append(
                    _MockResponse(TagName=x[0], Value=x[1], Status="Success")
                )
            return container
        else:
            return _MockResponse(TagName=tag, Value=value, Status="Success")

    def GetPLCTime(self, raw = False):
        if raw:
            return _MockResponse(TagName=None, Value=time.time(), Status="Success")
        else:
            return _MockResponse(TagName=None, Value=datetime.now(), Status="Success")

    def SetPLCTime(self):
        return _MockResponse(TagName=None, Value=time.time(), Status="Success")

    def GetTagList(self, allTags = True):
        values=[
                _MockTag("tag-one"),
                _MockTag("tag-two"),
                _MockTag("tag-three")
        ]
        return _MockResponse(
            TagName=None, 
            Value=values,
            Status="Success"
        )

    def GetProgramTagList(self, programName):
        values=[
                _MockTag("Program:tag-one"),
                _MockTag("Program:tag-two"),
                _MockTag("Program:tag-three")
        ]

        return _MockResponse(
            TagName=None, 
            Value=values,
            Status="Success"
        )

    def GetProgramsList(self):
        return _MockResponse(
            TagName=None, 
            Value=[
                "Program:program-one",
                "Program:program-two",
                "Program:program-three"
            ],
            Status="Success"
        )

    def Discover(self):
        values=[
                _MockDevice(address="192.168.1.100"),
                _MockDevice(address="192.168.1.101"),
                _MockDevice(address="192.168.1.102")
        ]

        return _MockResponse(
            TagName=None, 
            Value=values,
            Status="Success"
        )

    def GetModuleProperties(self, slot):
        device = _MockDevice(address="192.168.1.100")
        return _MockResponse(
            TagName=None, 
            Value=device,
            Status="Success"
        )

    def GetDeviceProperties(self):
        device = _MockDevice(address="192.168.1.100")
        return _MockResponse(
            TagName=None, 
            Value=device,
            Status="Success"
        )
