'''
Universal Data Transmission Format
'''
import json, hashlib, time
from builtins import open as standard_open

try:
    from base64 import standard_b64decode, standard_b64encode
    mpy = False
except ImportError:
    # Polyfills for Micropython
    from binascii import b2a_base64 as standard_b64encode
    from binascii import a2b_base64 as standard_b64decode
    from binascii import hexlify
    mpy = True

def open(filepath, mode):
    return (standard_open(filepath, mode), filepath.rstrip('/').rsplit('/', 1)[-1])

def encode_data(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return standard_b64encode(data).decode('utf-8')

def decode_data(encoded_data, binary=False):
    if binary:
        return standard_b64decode(encoded_data)
    else:
        return standard_b64decode(encoded_data).decode('utf-8')

def hash_data(base64string):
    global mpy
    if not isinstance(base64string, bytes):
        base64string = str(base64string).encode('utf-8')
    hash_obj = hashlib.sha256()
    hash_obj.update(base64string)
    # Hashing Polyfills
    if mpy:
        return hexlify(hash_obj.digest()).decode('utf-8')
    else:
        return hash_obj.hexdigest()

def localtime():
    # Time Polyfills
    try:
        timenow = time.ticks_us()
    except Exception:
        timenow = time.monotonic_ns() // 1000
    return timenow

def send(datatype, data, name=None, skip_encode=False):
    if not skip_encode:
        encoded_data = encode_data(data)
    else: 
        encoded_data = data

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

    # Data
    message['data'] = str(encoded_data)

    return json.dumps(message)

def send_file(file_tuple):
    file_obj = file_tuple[0]
    filename = file_tuple[1]
    filedata = file_obj.read()
    if isinstance(filedata, str):
        filetype = 'file'
    elif isinstance(filedata, bytes):
        filetype = 'binaryfile'
    else:
        raise 'Filetype not string or bytes'
    encoded_filedata = encode_data(filedata)
    return send(filetype, encoded_filedata, name=filename, skip_encode=True)

def send_exec(command):
    return send('exec', command)

def recieve(json_data):
    data = json.loads(json_data)
    datatype = data['type']
    # Data Validation
    if hash_data(data['data']) == data['datahash']:
        valid = True
    else:
        valid = False
        raise 'Invalid Data: Data Hashes do not match! Possibly corrupted data?'

    # Data Archeatype Sorting
    if datatype == 'file':
        filename = data['name']
        filedata = decode_data(data['data'])
        with standard_open(filename, "w", encoding="utf-8") as writefile:
            writefile.write(filedata)
            writefile.close()
    elif datatype == 'binaryfile':
        filebinaryname = data['name']
        filebinarydata = decode_data(data['data'], binary=True)
        with standard_open(filebinaryname, "wb") as writebinaryfile:
            writebinaryfile.write(filebinarydata)
            writebinaryfile.close()
    elif datatype == 'exec':
        command = decode_data(data['data'])
        try:
            stout = exec(command)
        except Exception as error:
            stout = error
        if stout:
            print(stout)

def save_packet(json_packet):
    global mpy
    json_content = json.loads(json_packet)
    with standard_open((json_content['type'] + '-' + json_content['uuid'] + '.json'), 'w') as savefile:
        json.dump(json_content, savefile)
