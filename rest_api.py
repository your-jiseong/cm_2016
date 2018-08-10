# -*- coding: utf-8 -*-

import sys

import os

sys.path.append('library')

# --

def enable_cors(fn):
	def _enable_cors(*args, **kwargs):
		from bottle import request
		from bottle import response

		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
		response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

		if request.method != 'OPTIONS':
			return fn(*args, **kwargs)
		
	return _enable_cors

# --

def proc_query(i_text):
	i_text = i_text.replace("\\", "\\\\")
	i_text = i_text.replace("\"", "\\\"")
	i_text = '"' + i_text + '"'

	# --

	import os

	path = os.path.dirname(os.path.abspath(__file__))

	line = ' '.join(['python', path + '/term_api.py', i_text])

	# --

	from subprocess import Popen, PIPE

	p = Popen(line, stdout=PIPE, stderr=PIPE, shell=True)
	stdout, stderr = p.communicate()

	print stdout, stderr

	# --

	o_text = stdout

	return o_text

# --

from bottle import route

@route(path='/cm', method=['OPTIONS', 'POST'])
@enable_cors
def query():
	import json

	# --

	from bottle import request

	i_text = request.body.read()
	
	i_json = json.loads(i_text)

	# --

	try:
		if i_json['conf']['sync'] == 'off':
			import time

			i_json['rid'] = long(time.time() * 1000000)

			import threading

			thread = threading.Thread(target=proc_query, args=(json.dumps(i_json),))
			
			thread.start()
			
			return json.dumps({'rid': i_json['rid']})

		else:
			return proc_query(json.dumps(i_json))
			
	except:
		return proc_query(json.dumps(i_json))
		

# --

from bottle import run

run(server='cherrypy', host='ws.okbqa.org', port=7047)