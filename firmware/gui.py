from flask import Flask, request, render_template, redirect, url_for, flash, send_file # type: ignore[reportMissingImports]
from pathlib import Path # type: ignore[reportMissingImports]
import os, gcodeparser # type: ignore[reportMissingImports]

current_gcode = None

app = Flask(__name__)
app.secret_key = "diwprintersession"
ALLOWED_EXTENSIONS = {".gcode"}
def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return send_file('index.html') 

@app.route("/assets/<filename>")
def assets(filename):
    return send_file('assets/'+filename)

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    global current_gcode
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected.")
            return redirect("/")

        file = request.files["file"]

        if file.filename == "":
            flash("No file selected.")
            return redirect("/")

        if not allowed_file(file.filename):
            flash("Only .gcode files are allowed.")
            return redirect("/")

        current_gcode = file.read().decode("utf-8", errors="replace")
        return redirect("/startprint")

@app.route("/startprint")
def startprint():
    global current_gcode
    current_gcode = list(gcodeparser.parse_gcode_lines(current_gcode, include_comments=False))
    return current_gcode

if __name__ == "__main__":
    app.run(debug=True)