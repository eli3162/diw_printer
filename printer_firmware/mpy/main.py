from microflask import *
import listtemplate, credentials, os, gc
from microdot.multipart import with_form_data

networkconnect(credentials.ssid, credentials.password)

app = Microdot()
Request.max_content_length = 1024 * 1024

@app.route('/<filename>')
def filefetch(request, filename):
    return send_file(filename)

@app.route('/assets/<filename>')
def filefetch(request, filename):
    if '.css' in filename:
        return send_file('assets/' + filename), {'Content-Type': 'text/css'}
    else:
        return send_file('assets/' + filename)

@app.post('/upload')
@with_form_data
async def upload(request):
    print(await request.files.read)
    return redirect('/')

@app.route('/')
def index(request):
    return html((send_html('assets/index.html')[0].replace('{lists}', listtemplate.html(os.listdir()))).replace('\n', ''))

app.run(port=80, debug=True)
