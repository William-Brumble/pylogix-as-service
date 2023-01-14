
Python-based ZeroMQ server that wraps Pylogix, allowing the use of it as a service.
```
usage: main.py [-h] --server-address SERVER_ADDRESS --server-port
                          SERVER_PORT [--simulate SIMULATE]

Wraps pylogix with zeromq to allow multi-language inter process communication.

options:
  -h, --help            show this help message and exit
  --server-address SERVER_ADDRESS
                        The address for this service to bind to, eg. 127.0.0.1.        
  --server-port SERVER_PORT
                        The port for this service to listen on, eg. 7777.
  --simulate SIMULATE   Simulate connection to the PLC, useful for testing, eg. True
```

## INSTALLATION
Download the application.
```
git clone https://github.com/William-Brumble/pylogix-as-service.git
```
Change into the root directory.
```text
cd pylogix-as-service
```
#### <b>DOCKER</b>
Running these two commands will build the docker image and run the app in simulation mode.
Forwarding all requests to localhost port 7777 to the application running inside the container.
```text
docker build -t "pylogix-as-service:v1" .
docker run -p 127.0.0.1:7777:7777 -d --name pylogix-as-service  pylogix-as-service:v1 --server-address 0.0.0.0 --server-port 7777 --simulate True
```
#### <b>WINDOWS</b>
Running these four commands will setup a virtual environment, install the dependencies,
and run the app in simulation mode. Listening for connections on localhost port 7777.
```text
py -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python ./src/main.py --server-address 127.0.0.1 --server-port 7777 --simulate True
```
#### <b>LINUX</b>
Running these four commands will setup a virtual environment, install the dependencies,
and run the app in simulation mode. Listening for connections on localhost port 7777.
```text
python3.10 -m venv venv
source .\venv\bin\activate
pip install -r requirements.txt
python ./src/main.py --server-address 127.0.0.1 --server-port 7777 --simulate True
```
## TESTING
After following the installation instructions above you now have the app running in simulation mode
and listening on localhost port 7777. While running in simulation mode it can be useful to run
the tester script to make sure everything is in running order.
Fire up another terminal, from the repo root dir, activate the virtual environment, and run the following command.
```text
python ./src/tester.py --server-address 127.0.0.1 --server-port 7777
```
The following output is indication that everything is in working order.
```text
..............
----------------------------------------------------------------------
Ran 14 tests in 0.289s
```
## PRODUCTION
Simply run the aforementioned commands with simulation option set to False.\
First connect to a PLC by sending the CONNECT command, then send any of the desired listed requests below.\
Any future calls to CONNECT will close the existing connection and make a new connection.\
You don't need to call CONNECT before every request, there is one connection maintained at a time.\
However if you want to send messages to multiple PLCs you could connect to the desired PLC prior to sending any of the requests shown below.
## MESSAGE REQUEST AND RESPONSE EXAMPLES
Below can be used as a useful reference of the various request message setups and their expected responses.

[CONNECT](#connect)\
[CLOSE](#close)\
[GET CONNECTION SIZE](#get-connection-size)\
[SET CONNECTION SIZE](#set-connection-size)\
[READ SINGLE](#read-single)\
[READ LIST](#read-list)\
[WRITE SINGLE](#write-single)\
[WRITE LIST](#write-list)\
[GET PLC TIME](#get-plc-time)\
[SET PLC TIME](#set-plc-time)\
[GET TAG LIST](#get-tag-list)\
[GET PROGRAM TAG LIST](#get-program-tag-list)\
[GET PROGRAMS TAG LIST](#get-programs-tag-list)\
[DISCOVER](#discover)\
[GET MODULE PROPERTIES](#get-module-properties)\
[GET DEVICE PROPERTIES](#get-device-properties)
#### CONNECT
```python
# request
{
    'command': 'connect', 
    'msg': {
        'ip': '192.168.1.196', 
        'slot': 0, 
        'timeout': 5, 
        'micro800': False
    }
}
# response
{
    'command': 'connect', 
    'msg': {
        'name': None, 
        'value': None, 
        'status': 'Success'
    }
}
```
#### CLOSE
```python
# request
{
    'command': 'close',
    'msg': None
}
# response
{
    'command': 'close',
    'msg': {
        'name': None, 
        'value': None, 
        'status': 'Success'
    }
}
```
#### GET CONNECTION SIZE
```python
# request
{
    'command': 'get-connection-size', 
    'msg': None
}
# response
{
    'command': 'get-connection-size', 
    'msg': {
        'name': None, 
        'value': 508, 
        'status': 
        'Success'
    }
}
```
#### SET CONNECTION SIZE
```python
# request
{
    'command': 'set-connection-size', 
    'msg': {
        'connection_size': 508
    }
}
# response
{
    'command': 'set-connection-size',
    'msg': {
        'name': None,
        'value': 508, 
        'status': 'Success'
    }
}
```
#### READ SINGLE
```python
# request
{
    'command': 'read', 
    'msg': {
        'tag': 'BaseINT', 
        'count': 1, 
        'datatype': 195
    }
}
# response
{
    'command': 'read',
    'msg': {
        'name': 'BaseINT', 
        'value': -30844, 
        'status': 'Success'
    }
}
```
#### READ LIST
```python
# request
{
    'command': 'read', 
    'msg': {
        'tag': [
            'BaseINTArray[0]', 
            'BaseINTArray[1]', 
            'BaseINTArray[2]'
        ], 
        'count': None, 
        'datatype': None
    }
}
# response
{
    'command': 'read', 
    'msg': [
        {'name': 'BaseINTArray[0]', 'value': None, 'status': 'Success'}, 
        {'name': 'BaseINTArray[1]', 'value': None, 'status': 'Success'}, 
        {'name': 'BaseINTArray[2]', 'value': None, 'status': 'Success'}
    ]
}
```
#### WRITE SINGLE
```python
# request
{
    'command': 'write', 
    'msg': {
        'tag': 'BaseINT', 
        'value': 1, 
        'datatype': 195
    }
}
# response
{
    'command': 'write', 
    'msg': {
        'name': 'BaseINT', 
        'value': 1, 
        'status': 'Success'
    }
}
```
#### WRITE LIST
```python
# request
{
    'command': 'write', 
    'msg': [
        ['BaseINTArray[0]', 1], 
        ['BaseINTArray[1]', 2], 
        ['BaseINTArray[2]', 3]
    ]
}
# response
{
    'command': 'write', 
    'msg': [
        {'name': 'BaseINTArray[0]', 'value': 1, 'status': 'Success'},
        {'name': 'BaseINTArray[1]', 'value': 2, 'status': 'Success'}, 
        {'name': 'BaseINTArray[2]', 'value': 3, 'status': 'Success'}
    ]
}
```
#### GET PLC TIME
```python
# request
{
    'command': 'get-plc-time', 
    'msg': {
        'raw': False
    }
}
# response
{
    'command': 'get-plc-time', 
    'msg': {
        'name': None, 
        'value': '2023-01-10 15:41:13.110141', 
        'status': 'Success'
    }
}
```
#### SET PLC TIME
```python
# request
{
    'command': 'set-plc-time', 
    'msg': None
}
# response
{
    'command': 'set-plc-time', 
    'msg': {
        'name': None, 
        'value': 1673386873.3006327, 
        'status': 'Success'
    }
}
```
#### GET TAG LIST
```python
# request
{
    'command': 'get-tag-list', 
    'msg': {
        'all_tags': True
    }
}
# response
{
    'command': 'get-tag-list', 
    'msg': {
        'name': None, 
        'value': [
            {
                'TagName': 'tag-one', 
                'InstanceID': 10,
                'SymbolType': 214, 
                'DataTypeValue': 1750, 
                'DataType': 'AB:ETHERNET_MODULE:C:O', 
                'Array': 0, 
                'Struct': 1, 
                'Size': 0, 
                'AccessRight': None, 
                'Internal': None, 
                'Meta': None, 
                'Scope0': None, 
                'Scope1': None, 
                'Bytes': None
            }, 
            ...
        ], 
    'status': 'Success'
}
```
#### GET PROGRAM TAG LIST
```python
# request
{
    'command': 'get-program-tag-list', 
    'msg': {
        'program_name': ''
    }
}
# response
{
    'command': 'get-program-tag-list', 
    'msg': {
        'name': None, 
        'value': [
            {
                'TagName': 'Program:tag-one', 
                'InstanceID': 10, 
                'SymbolType': 214, 
                'DataTypeValue': 1750, 
                'DataType': 'AB:ETHERNET_MODULE:C:O', 
                'Array': 0, 
                'Struct': 1, 
                'Size': 0, 
                'AccessRight': None, 
                'Internal': None, 
                'Meta': None, 
                'Scope0': None, 
                'Scope1': None, 
                'Bytes': None
            }, 
            ...
        ],
        'status': 'Success'
    }
}
```
#### GET PROGRAMS LIST
```python
# request
{
    'command': 'get-programs-list', 
    'msg': None
}
# response
{
    'command': 'get-programs-list', 
    'msg': {
        'name': None, 
        'value': [
            'Program:program-one', 
            'Program:program-two', 
            'Program:program-three'
        ], 
        'status': 'Success'
    }
}
```
#### DISCOVER
```python
# request
{
    'command': 'discover', 
    'msg': None
}
# response
{
    'command': 'discover', 
    'msg': {
        'name': None, 
        'value': [
            {
                'Length': 0, 
                'EncapsulationVersion': 0, 
                'IPAddress': '192.168.1.100', 
                'VendorID': 1, 
                'Vendor': 'Rockwell Automation/Allen-Bradley', 
                'DeviceID': 14, 
                'DeviceType': None, 
                'ProductCode': 167, 
                'Revision': 20.0, 
                'Status': 12384, 
                'SerialNumber': 16777215, 
                'ProductNameLength': 11, 
                'ProductName': '1756-L84E/B', 
                'State': 66
            }, 
            ...
        ], 
        'status': 'Success'
    }
}
```
#### GET MODULE PROPERTIES
```python
# request
{
    'command': 'get-module-properties', 
    'msg': {
        'slot': 0
    }
}
# response
{
    'command': 'get-module-properties', 
    'msg': {
        'name': None, 
        'value': {
            'Length': 0, 
            'EncapsulationVersion': 0, 
            'IPAddress': '192.168.1.100', 
            'VendorID': 1, 
            'Vendor': 'Rockwell Automation/Allen-Bradley', 
            'DeviceID': 14, 
            'DeviceType': None, 
            'ProductCode': 167, 
            'Revision': 20.0, 
            'Status': 12384, 
            'SerialNumber': 16777215, 
            'ProductNameLength': 11, 
            'ProductName': '1756-L84E/B',
            'State': 66
        }, 
        'status': 'Success'
    }
}
```
#### GET DEVICE PROPERTIES
```python
# request
{
    'command': 'get-device-properties', 
    'msg': None
}
# response
{
    'command': 'get-device-properties',
    'msg': {
        'name': None, 
        'value': {
            'Length': 0, 
            'EncapsulationVersion': 0, 
            'IPAddress': '192.168.1.100', 
            'VendorID': 1, 
            'Vendor': 'Rockwell Automation/Allen-Bradley', 
            'DeviceID': 14, 
            'DeviceType': None, 
            'ProductCode': 167, 
            'Revision': 20.0, 
            'Status': 12384, 
            'SerialNumber': 16777215, 
            'ProductNameLength': 11, 
            'ProductName': '1756-L84E/B', 
            'State': 66
        },
        'status': 'Success'
    }
}
```
### WARNING - DISCLAIMER
NB! state is in heavy development, I'm using this in a lab environment, and it is in working order, however this hasn't been battle tested. If you have any issues please post an issue or submit a pull request. Many thanks.

**PLCs control many kinds of equipment and loss of property, production or even life can happen if mistakes in programming or access are made.  Always use caution when accessing or programming PLCs!**

We make no claims or warrants about the suitability of this code for any purpose.
## LICENSE
The code in this repository is licensed under MIT license.
Refer to the dependencies in requirements.txt and their dependencies for their licenses.\
[pyzmq](https://github.com/zeromq/pyzmq)\
[tornado](https://github.com/tornadoweb/tornado)\
[pylogix](https://github.com/dmroeder/pylogix)