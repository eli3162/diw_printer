'''
# Serial Communication Pipeline 
The Serial Communication Pipeline by Ethan Li © 2026
'''
import json, hashlib, time

try:
    from base64 import standard_b64decode, standard_b64encode
    mpy = False
except ImportError:
    mpy = True
    from binascii import b2a_base64 as standard_b64encode
    from binascii import a2b_base64 as standard_b64decode
    from binascii import hexlify

'''
Micropython Polyfills
Allow for full Micropython Compatability with Python only functions
'''

def timenow():
    '''
    Polyfill for MicroPython/Python compatability with monotonic clocks
    '''
    if mpy:
        timemono = time.ticks_us()
    else:
        timemono = time.monotonic_ns() // 1000
    return timemono

def hex_hash(binaryhash: bytes):
    '''
    Polyfill for MicroPython/Python compatability with hexadecimal encoding
    '''
    if mpy:
        return hexlify(binaryhash.digest()).decode('utf-8')
    else:
        return binaryhash.hexdigest()


def file_open(filepath: str, mode: str):
    '''
    In Micropython the standard `open()` function does not support additional file metadata, so this will package the file with the filename as metadata.
    
    Usage:
    ```
    #Normal 'open' function:
    open('file', 'mode') -> fileobj
    #file_open function
    serialcom.file_open('file', mode) -> {'file': fileobj, 'name': filename}
    ```
    '''
    return {'file': open(filepath, mode), 'name': filepath.rstrip('/').rsplit('/', 1)[-1]}

def encode_data(data: str | bytes):
    '''
    Encode data in base64 encoding.
    
    Usage:
    ```
    serialcom.encode_data(data_to_encode)
    ```
    '''
    if isinstance(data, str):
        data = data.encode('utf-8')
    return standard_b64encode(data).decode('utf-8')

def decode_data(encoded_data: str | bytes):
    '''
    Decode data from base64 encoding.
    
    Usage:
    ```
    serialcom.decode_data(base64 to decode)
    ```
    '''

    if isinstance(encoded_data, bytes):
        return standard_b64decode(encoded_data)
    else:
        return standard_b64decode(encoded_data).decode('utf-8')

def hash_data(base64string: str):
    '''
    Hashes a string of data with SHA-256:
    
    Usage:
    ```
    serialcom.hash_data('string to hash')
    ```
    '''
    global mpy
    if not isinstance(base64string, bytes):
        base64string = str(base64string).encode('utf-8')
    hash_obj = hashlib.sha256()
    hash_obj.update(base64string)
    return hex_hash(hash_obj)

def localtime():
    '''
    Millisecond Time accurate clocks for Python/Micropython, run using the processor's ***monotonic*** clocks, meaning they do not ever go backwards, and are not affected by timezone changes.
    
    Usage:
    ```
    serialcom.localtime()
    ```
    
    **Note:** Python clock is 1000x more accurate, due to Micropython Processor Limitations
    '''
    return timenow()

def send(datatype: str, data: str | bytes, metadata: dict=None, name: str=None, skip_encode: bool=False):
    '''
    Sends Python/Micropython data with Serialcom JSON, allowing custom datatypes, metadata, and more:
    
    Usage:
    ```
    serialcom.send('custom datatype', 'random data', metadata={'date': '1/12/5'})
    ```
    '''
    if not skip_encode:
        encoded_data = encode_data(data)
    else: 
        encoded_data = data

    # Message Builder
    message = {}

    # Headers
    datahash = hash_data(encoded_data)
    message['type'] = datatype
    message['uuid'] = hash_data(str(localtime())+datahash)
    message['time'] = localtime()
    message['datahash'] = datahash

    # Metadata
    if name:
        message['name'] = name

    if metadata:
        if isinstance(metadata, dict):
            raise 'Please format Metadata as a dictonary'
        message['metadata'] = metadata

    # Data
    message['data'] = str(encoded_data).replace('\n', '')

    if validate_packet(message):
        return json.dumps(message)
    else:
        raise "Error: Corrupted JSON"

def send_file(file_dict, filename: str=None):
    '''
    Packages a file as Serialcom JSON, can either be binary or UTF-8. 

    Usage:
    ```
    serialcom.send_file(file_open('example.txt', 'r'))
    ```
    '''
    if not isinstance(file_dict, dict):
        try: 
            if not filename:
                filename = file_dict.name
            filename = file_dict.read()
        except Exception:
            raise 'Please use the file_open function as the standard open function will not return the filename as metadata'
    else:
        filename = file_dict['name']
        filedata = file_dict['file'].read()

    if isinstance(filedata, str):
        filetype = 'file'
    elif isinstance(filedata, bytes):
        filetype = 'binaryfile'
    else:
        raise 'Filetype not string or bytes'
    encoded_filedata = encode_data(filedata)
    return send(filetype, encoded_filedata, name=filename, skip_encode=True)

def send_exec(command: str):
    '''
    Parse executables into Serialcom JSON data

    Usage:
    ```
    serialcom.send(serialcom.send_exec('print('Hello World!')'))
    ```
    '''
    return send('exec', command)

def validate_packet(data: dict):
    '''
    Check for data corruption with SHA-256 Data Hash

    Usage:
    ```
    serialcom.validate_packet(json_data) -> True / False
    ```
    '''
    if hash_data(data['data']) == data['datahash']:
        valid = True
    else:
        valid = False
    return valid

def file_parse(data: dict):
    '''
    **MODIFIABLE:**
    Action preformed reguarding parsing received file JSON, used by `serialcom.receive()`
    '''
    filename = data['name']
    filedata = decode_data(data['data'])
    with open(filename, "w", encoding="utf-8") as writefile:
        writefile.write(filedata)
        writefile.close()

def binaryfile_parse(data: dict):
    '''
    **MODIFIABLE:**
    Action preformed reguarding parsing received binary file JSON, used by `serialcom.receive()`
    '''
    filebinaryname = data['name']
    filebinarydata = decode_data(data['data'], binary=True)
    with open(filebinaryname, "wb") as writebinaryfile:
        writebinaryfile.write(filebinarydata)
        writebinaryfile.close()

def exec_parse(data: dict):
    '''
    **MODIFIABLE:**
    Action preformed reguarding parsing received client executable JSON, used by `serialcom.receive()`
    '''
    command = decode_data(data['data'])
    try:
        stout = exec(command)
    except Exception as error:
        stout = error
    if stout:
        print(stout)

def receive(json_data: dict):
    '''
    Parse incoming Serialcom JSON data
    
    Usage:
    ```
    serialcom.receive(incoming_json_data)
    ```
    '''
    data = json.loads(json_data)
    datatype = data['type']
    # Data Validation
    valid = validate_packet(data)
    if not valid:
        raise 'Error: Invalid Data: Data Hashes do not match! Possibly corrupted / tampered data?'
    
    if valid:
        # Data Handlers
        if datatype == 'file':
            file_parse(data)
        elif datatype == 'binaryfile':
            binaryfile_parse(data)
        elif datatype == 'exec':
            exec_parse(data)

def save_packet(json_packet):
    '''
    Save a Serialcom JSON Packet as a file
    
    Usage:
    ```
    save_packet(json_data)
    ```
    '''
    global mpy
    json_content = json.loads(json_packet)
    with open((json_content['type'] + '-' + json_content['uuid'] + '.json'), 'w') as savefile:
        json.dump(json_content, savefile)

def load_packet(path: str):
    '''
    Load and parse a Serialcom JSON Packet file
    
    Usage:
    ```
    load_packet(packet_path)
    ```
    '''
    return receive(open(path, 'r').read())
