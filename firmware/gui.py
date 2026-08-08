from flask import Flask, request, render_template, redirect, url_for, flash, send_file # type: ignore[reportMissingImports]
from pathlib import Path # type: ignore[reportMissingImports]
import os, gcodeparser, listtemplate # type: ignore[reportMissingImports]
from werkzeug.utils import secure_filename # type: ignore[reportMissingImports]

app = Flask(__name__)
app.secret_key = "diwprintersession"
allowed_filetx = {".gcode", ".nc", ".mpf", ".mpt"}
def allowed_file(filename):
    return Path(filename).suffix.lower() in allowed_filetx

def htmllist(list):
    return listtemplate.html(list)

@app.route("/")
def home():
    with open("assets/index.html", "r") as file:
        content = file.read()
    content = content.replace('{lists}', htmllist(os.listdir('gcode')))
    return content

@app.route("/assets/<filename>")
def assets(filename):
    return send_file('assets/'+filename)

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    global current_gcode
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected.")
            print("No file selected.")
            print(request.files)
            return redirect("/")

        file = request.files["file"]

        if file.filename == "":
            flash("No file selected.")
            print("No file selected.")
            return redirect("/")

        if not allowed_file(file.filename):
            flash("Only .gcode files are allowed.")
            print("Only .gcode files are allowed.")
            return redirect("/")
        
        file.save(os.path.join(os.getcwd(), 'gcode', secure_filename(file.filename)))
        return redirect("/")

@app.route("/gcode/<filename>")
def send_gcode(filename):
    return send_file('gcode/'+filename)

@app.route("/delete/<filename>")
def delete_gcode(filename):
    os.remove('gcode/'+filename)
    return redirect('/')

@app.route("/print/<filename>")
def print_gcode(filename):
    with open('gcode/'+filename, 'r') as f:
        for line in gcodeparser.parse_gcode_lines(f, include_comments=False):
            print(line)
    return 'Parsed'

if __name__ == "__main__":
    app.run(debug=True)