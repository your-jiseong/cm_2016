# -*- coding: utf-8 -*-

import sys, re, time

from bottle import route, run, template, request, response, post
import urllib, urllib2, json

from socket import timeout

# Global variables
defConf = {}
newConf = {}

jInputs = {}
jOutputs = {}
jOutput2jInput = {}

logs = []
answers = []

def main():
  set_inputs()
  set_conf()

  run_pipeline()
  
  bye()


def set_inputs():
  global jInputs
  global jOutputs
  global logs
  global answers

  jInputs['CM'] = json.loads(sys.argv[1])
  jOutputs['CM'] = [{'logs': logs, 'answers': answers}]

  write_log({'1. module': 'CM', '2. input': jInputs['CM']})


def set_conf():
  global defConf
  global newConf
  global jInputs

  get_default()

  newConf = defConf
  newConf.update(jInputs['CM']['conf'])


def get_default():
  global defConf

  if jInputs['CM']['language'] == 'en':
    i_file = open('default_en.conf', 'r')
  elif jInputs['CM']['language'] == 'ko':
    i_file = open('default_ko.conf', 'r')
  sInput = i_file.read()
  i_file.close()

  defConf = json.loads(sInput)
  

def run_pipeline():
  global newConf
  global answers
  global jInputs
  global jOutputs

  answers = []

  pre_module = 'CM'
  modules = newConf['sequence']

  if len(newConf['address']) - 1 != len(modules):
    fault({'exception': 'wrong configuration', 'conf': newConf})

  for module in modules:
    for address in newConf['address'][module]:
      # Input processing
      if module == 'ELU' or address == 'http://143.248.135.150:2222/entity_linking':
        jInput = {}

        jInput['text'] = jInputs['CM']['string']
        jInput['lower_bound'] = 0.75

        try:
          jInputs[module].append(jInput)
        except KeyError:
          jInputs[module] = [jInput]

      elif module == 'TGM' or address == 'http://121.254.173.77:1555/templategeneration/templator/':
        jInput = {}

        if pre_module == 'ELU':
          jInput['entities'] = jOutputs[pre_module]

        jInput['string'] = jInputs['CM']['string']
        jInput['language'] = jInputs['CM']['language']
        
        try:
          jInputs[module].append(jInput)
        except KeyError:
          jInputs[module] = [jInput]

      elif module == 'DM' or address == 'http://121.254.173.77:2357/agdistis/run':
        for jOutput in jOutputs[pre_module]:
          jInput = {}

          jInput['question'] = jInputs['CM']['string']
          jInput.update(jOutput)

          try:
            jInputs[module].append(jInput)
          except KeyError:
            jInputs[module] = [jInput]
      
      elif module == 'QGM' or address == 'http://121.254.173.77:38401/queries':
        for jOutput in jOutputs[pre_module]:
          jInput = {}

          sOutput = json.dumps(jOutput)
          jInput['template'] = jOutput2jInput[sOutput]
          jInput['disambiguation'] = jOutput

          try:
            jInputs[module].append(jInput)
          except KeyError:
            jInputs[module] = [jInput]

      elif module == 'AGM' or module == 'http://121.254.173.77:7744/agm':
        for (kb_address, graph_uri) in newConf['address']['KB']:
          conf = {'kb_addresses': [kb_address], 'graph_uri': [graph_uri]}

          jInput = {}
          jInput['conf'] = conf
          jInput['queries'] = jOutputs[pre_module]

          try:
            jInputs[module].append(jInput)
          except KeyError:
            jInputs[module] = [jInput]

      else:
        jInputs[module] = jOutputs[pre_module]

      for jInput in jInputs[module]:
        # Execution
        start_time = time.time()

        sInput = json.dumps(jInput)
        jOutput = json.loads(exec_module(module, address, sInput))

        elapsed_time = time.time() - start_time

        write_log({'1. module': module, '2. elapsed_time': elapsed_time, '3. input': jInput, '4. output': jOutput})

        # 예외처리 for DM
        if module == 'DM':
          try:
            jOutput = jOutput['ned']
          except KeyError:
            fault({'module': 'DM', 'exception': 'wrong output format', 'output': json.dumps(jOutput)})

        try:
          jOutputs[module] += jOutput
        except KeyError:
          jOutputs[module] = jOutput

        # 예외처리 for QGM
        if module == 'DM':
          for x in jOutput:
            sOutput = json.dumps(x)
            jOutput2jInput[sOutput] = jInput

        # 예외처리 for AGM
        if module == 'AGM':
          if len(jOutputs['AGM']) >= newConf['answer_num']:
            break

    pre_module = module

  try:
    answers = jOutputs['AGM']
  except KeyError:
    fault({'module': 'AGM', 'exception': 'no module exists'})


def exec_module(module, address, sInput):
  sOutput = 'null'

  try:
    # GET / POST transition
    if address == 'http://121.254.173.77:2357/agdistis/run': 
      # AGDISTIS only supports the GET method.
      sOutput = send_getrequest(address + '?data=' + urllib.quote(sInput.replace('\\"','"').replace('|','_')))
    else:
      sOutput = send_postrequest(address, sInput)

  # Fault alarming - Module error
  except Exception as e:
    fault({'module': module, 'address': address, 'exception': str(e), 'input': json.loads(sInput)})
 
  # Fault checking and tolerance
  check_fault(module, address, sInput, sOutput)

  return sOutput


def send_getrequest(url):
  opener = urllib2.build_opener()
  request = urllib2.Request(url)
  return opener.open(request, timeout=newConf['timelimit']).read()
  

def send_postrequest(url, input_string):
  opener = urllib2.build_opener()
  request = urllib2.Request(url, data=input_string, headers={'Content-Type':'application/json'})
  return opener.open(request, timeout=newConf['timelimit']).read()


def check_fault(module, address, sInput, sOutput):
  # Fault alarming - Empty error
  if sOutput == '':
    fault({'module': module, 'exception': 'no result returned', 'address': address, 'input': sInput, 'output': sOutput})
  if sOutput.lower() == 'null':
    fault({'module': module, 'exception': 'null-value returned', 'address': address, 'input': sInput, 'output': sOutput})
  
  # Fault alarming - Encoding error
  try:
    sOutput.decode('utf-8')
  except:
    fault({'module': module, 'exception': 'output is not encoded in UTF-8', 'address': address, 'input': sInput, 'output': sOutput})
  
  # Fault alarming - Output format error
  try:
    json.loads(sOutput)
  except:
    fault({'module': module, 'exception': 'output is not formattd in JSON', 'address': address, 'input': sInput, 'output': sOutput})


def write_log(l):
  global logs

  logs.append(l)


def fault(l):
  write_log(l)
  bye()


def bye():
  output = json.dumps({'logs': logs, 'answers': answers}, indent=5, separators=(',', ': '), sort_keys=True)

  sys.stdout.write(output)
  sys.stdout.flush()
  sys.exit(0)
    

main()