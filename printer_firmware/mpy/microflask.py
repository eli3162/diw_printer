"""
Microflask
--------

The ``microflask`` mappings map Microdot fuctions to their Flask equivalents, allowing seemless integration from CPython to MicroPython
"""
try:
    import mm_wlan as wireless
    from microdot.microdot import * # type:ignore
    import os, network
except Exception as error:
    print(f'Error, your system is not supported. Check: Are you running Micropython? {error}')

def send_file(path, as_attachment=True):
    """Send File function ported from CPython to Micropython

    This allows the webserver to serve files from the micropython filesystem

    Example::

        from microflask import *

        app = Flask()

        @app.route('/')
        def index(request):
            return send_file('index.html') <-- This would serve the HTML file as raw text, not a webpage(see `send_html()` and `html()`)
    """
    try:
        with open(path, 'rb') as file:
            data = file.read()
            return data
    except Exception as e:
        return None

def networkconnect(ssid, password):
    """Establishes WiFi network connection, allowing you to host a web server to others

    This allows the webserver to serve files from the micropython filesystem

    Example::

        from microflask import *

        networkconnect('ssid', 'password') <--- Must go before the `app = Flask()`

        app = Flask() 

    """
    return wireless.connect_to_network(ssid, password)

def html(content):
    """Converts a string into a `text/html` response, allowing you to serve HTML pages

    This allows the webserver to serve files from the micropython filesystem

    Example::

        from microflask import *

        app = Flask() 

        @app.route('/')
        def index(request):
            return html('<p>Text</p>') <-- First reads html string as text, then converts to `text/html`

    """
    return content, {'Content-Type': 'text/html'}

def send_html(filepath):
    """Converts a file into a `text/html` response, allowing you to serve HTML pages

    This allows the webserver to serve files from the micropython filesystem

    Example::

        from microflask import *

        app = Flask() 

        @app.route('/')
        def index(request):
            return send_html('index.html') <-- First reads file as text, then converts to `text/html`

    """
    file = open(filepath)
    content = file.read()
    file.close()
    return(content, {'Content-Type': 'text/html'})

def networkcreate(ssid, password):
    """Creates a WiFi hotspot with a given SSID and Password, allows you to serve the webpage on it, at the ip address `192.168.4.1`

    Example::

        from microflask import *

        networkcreate('ssid', 'password') <-- Must be before `app = Flask()`

        app = Flask() 

    """
    global ap
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    while ap.active() == False:
        pass
    self_ip = ap.ifconfig()[0]
    print(f'Running at {self_ip} on network {ssid}, {password}.')
    return f'Running at {self_ip} on network {ssid}, {password}.'

def secure_filename(filename):
    filename = filename.replace(' ', '')
    filename = filename.replace('(', '_')
    filename = filename.replace(')', '')
    filename = filename.replace('\n', '')
    return filename