from microflask import *
# This package has Intellisence Mappings. Hover over something for documentation!

# You can use networkconnect() to connect to a WiFi with the SSID and Password
#networkconnect('ssid', 'password')

# You can use networkcreate() to create a Wifi with the SSID and Password
networkcreate('ssid', 'password')

app = Flask()

@app.route('/<filename>')
def filefetch(request, filename):
    return send_file(filename)

@app.route('/')
def index(request):
    return send_html('index.html')

@app.error_handler(404)
def errorpage(request):
    return send_html('404.html')

app.run(port=80, debug=True)

