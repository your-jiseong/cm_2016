# -*- coding: utf-8 -*-

import sys, re, subprocess, threading, time
from subprocess import Popen, PIPE
from bottle import route, run, template, request, response, post
import urllib, urllib2
import json

def enable_cors(fn):
  def _enable_cors(*args, **kwargs):
      # set CORS headers
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
      response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

      if request.method != 'OPTIONS':
          # actual request; reply with the actual response
          return fn(*args, **kwargs)
        
  return _enable_cors


def proc_query(i_text):
  i_text = i_text.replace("\\", "\\\\")
  i_text = i_text.replace("\"", "\\\"")
  i_text = '"' + i_text + '"'

  print 'Input:', i_text
  cmd = 'python terminal_api.py ' + i_text

  print 'Command:', cmd
  p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
  stdout, stderr = p.communicate()
  o_text = stdout
  print "o_text: ", stdout 

  print 'Output:', o_text  
  # Returning the results in JSON format
  #response.headers['Content-type'] = 'application/json'
  #return o_text


@route(path='/cm', method=['OPTIONS', 'POST'])
@enable_cors
def query():
  i_text = request.body.read()
  print i_text

  j = json.loads(i_text)
  j['rid'] = long(time.time() * 1000000)
  
  th = threading.Thread(target=proc_query, args=(json.dumps(j),))
  th.start()
  return json.dumps({'rid':j['rid']})


run(host='121.254.173.77', port=7047)
