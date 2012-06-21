#!/usr/bin/env python
# encoding: utf-8
import sys
import os
import uuid
import urllib
import time

from flask import Flask, request, redirect, url_for, flash, render_template, abort
from flask import send_from_directory
from werkzeug import secure_filename

UPLOAD_FOLDER = './ibin'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'fdbc2e0e71344d8bab93408192fe281c'

def get_files_info(max_hits=100):
	files = os.listdir(app.config['UPLOAD_FOLDER'])
	files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)))
	files.reverse()
	files = files[:max_hits]
	return_values = []
	for f in files:
		return_values.append({"filename": f, "name": f[33:], "uuid": f[:32], "ts": time.ctime(os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], f))) })
	return return_values

def generate_filename(filename):
	return "_".join([uuid.uuid4().hex, secure_filename(filename)])

def get_url(filename):
	url = request.url if not request.url.endswith("/") else request.url[:-1]
	return url + filename

def download(url):
	filename = os.path.basename(url)
	filename = generate_filename(filename)
	urllib.urlretrieve(request.form['uploadurl'], os.path.join(app.config['UPLOAD_FOLDER'], filename))
	return filename

@app.route('/', methods=['GET', 'POST'])
def paste():
	# For form posting from /
	if request.method == 'POST':
		try:
			if request.form.has_key("uploadurl"):	
				filename = download(request.form['uploadurl'])
				if request.form.has_key("noredirect"):
					return get_url(str(url_for('uploaded_file', filename=filename)))
				else:
					return redirect(url_for('uploaded_file', filename=filename))		
			elif request.files['file']:
				filename = generate_filename(request.files['file'].filename)
				request.files['file'].save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
				if request.form.has_key("noredirect"):
				    return get_url(str(url_for('uploaded_file', filename=filename)))
				else:
				    return redirect(url_for('uploaded_file', filename=filename))
			else:
				app.logger.debug("CRAP")
		except Exception, e:
			return render_template('exception.html',exception=str(e))
			
	# For bookmarklet posting
	elif request.method == 'GET':
		try:
			if request.args.has_key("uploadurl"):
				filename = download(request.args['uploadurl'])
				return redirect(url_for('uploaded_file', filename=filename))
		except Exception, e:
			return render_template('exception.html',exception=str(e))
	
	return render_template('paste.html')

@app.route('/list/<numentries>')
def pastes(numentries):
	numentries = int(numentries) if int(numentries) < 1000 else 1000
	return render_template("list.html", entries=get_files_info(numentries))

@app.route('/feed')
def rssfeeds():
	numentries = 10
	return render_template("rss.html", entries=get_files_info(numentries))

@app.route('/rm/<filename>')
def remove_file(filename):
	if filename.startswith(".") or filename.startswith(".."):
		return redirect(url_for("pastes", numentries=10))
	else:
		path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
		if os.path.exists(path) and os.path.isfile(path):
			os.unlink(path)
		return redirect(url_for("pastes", numentries=10))

@app.route('/flz/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tricks')
def tricks():
	return render_template("tricks.html")

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, threaded=True)