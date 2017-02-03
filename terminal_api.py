# -*- coding: utf-8 -*-

import sys, re, time

from bottle import route, run, template, request, response, post
import urllib, urllib2, json

from socket import timeout

from mysql.connector import (connection)



class DBConn:
    def __init__(self, rid=""):
        self.cnx = connection.MySQLConnection(user='root', password='okbqa', host='localhost', database='okbqa')
        self.cursor = self.cnx.cursor()
        self.rid = rid

    def log(self, done, log):
        if self.rid:
            self.cursor.execute(("INSERT INTO `web_log`(`rid`, `done`, `log`) VALUES (%s, %s, %s)"), (self.rid, done, log))
            self.cnx.commit()

    def close(self):
        if self.rid:
            self.cursor.close()
            self.cnx.close()

# Global variables
defConf = {}
newConf = {}

jInputs = {}
jOutputs = {}
sOutput2jInput = {}

log = []
result = []

dbc = None

def main():
	set_inputs()
	set_conf()

	run_pipeline()
	        
	bye()


def set_inputs():
	global jInputs
	global jOutputs
        global dbc

	jInputs['CM'] = json.loads(sys.argv[1])

        if 'rid' in jInputs['CM']:
            dbc = DBConn(jInputs['CM']['rid'])
        else:
            dbc = DBConn()
        
	dbc.log(5, "The process was started ...")
	#dbc.close()

	write_log({'1. module': 'CM', '2. input': jInputs['CM']})

        dbc.log(10, "The process is undergoing ...")

def set_conf():
	global defConf
	global newConf
	global jInputs
        global dbc
        dbc.log(15, "Setting configuration ...")

	def get_default():
		global defConf

		i_file = open('default.conf', 'r')
		sInput = i_file.read()
		i_file.close()

		defConf = json.loads(sInput)

		try:
			if jInputs['CM']['input']['language'] == 'en':
				i_file = open('default_en.conf', 'r')

			elif jInputs['CM']['input']['language'] == 'ko':
				i_file = open('default_ko.conf', 'r')

			sInput = i_file.read()
			i_file.close()

			defConf.update(json.loads(sInput))

		except:
			pass

	get_default()

	newConf = defConf
	newConf.update(jInputs['CM']['conf'])
        dbc.log(20, "Configured ...")
        
def run_pipeline():
	global newConf
	global result
	global jInputs
	global jOutputs
        global dbc
        dbc.log(25, "Pipeline was initiated ...")

	pre_module = 'NONE'
	jOutputs['NONE'] = jInputs['CM']['input']

        i = 30
	modules = newConf['sequence']
	for module in modules:
		for address in newConf['address'][module]:
			dbc.log(i, module + " is running at " + address + " ...")
                        i += 2

			# 입력 예외처리
			if pre_module == 'NONE' and module == 'ELU':
				jInput = {}

				jInput['text'] = jOutputs['CM']['input']['string']
				jInput['lower_bound'] = 0.75

				try:
					jInputs[module].append(jInput)
				except KeyError:
					jInputs[module] = [jInput]

			elif pre_module == 'NONE' and module == 'TGM':
				jInput = {}

				jInput['string'] = jInputs['CM']['input']['string']
				jInput['language'] = jInputs['CM']['input']['language']
				
				try:
					jInputs[module].append(jInput)
				except KeyError:
					jInputs[module] = [jInput]

			elif pre_module == 'ELU' and module == 'TGM':
				jInput = {}

				jInput['entities'] = jOutputs[pre_module]
				jInput['string'] = jInputs['CM']['input']['string']
				jInput['language'] = jInputs['CM']['input']['language']
				
				try:
					jInputs[module].append(jInput)
				except KeyError:
					jInputs[module] = [jInput]

			elif pre_module == 'TGM' and module == 'DM':
				for jOutput in jOutputs[pre_module]:
					jInput = {}

					jInput['question'] = jInputs['TGM'][0]['string']
					jInput.update(jOutput)

					try:
						jInputs[module].append(jInput)
					except KeyError:
						jInputs[module] = [jInput]

			elif pre_module == 'DM' and module == 'QGM':
				for jOutput in jOutputs[pre_module]:
					jInput = {}

					jInput['template'] = sOutput2jInput[json.dumps(jOutput)]
					jInput['disambiguation'] = jOutput

					try:
						jInputs[module].append(jInput)
					except KeyError:
						jInputs[module] = [jInput]

			elif pre_module == 'QGM' and module == 'AGM':
				for (kb_address, graph_uri) in newConf['address']['KB']:
					dbc.log(70, "AGM is running on " + graph_uri + " in " + kb_address + " ...")
                                        i = 70
					AGM_conf = {'kb_addresses': kb_address, 'graph_uri': graph_uri}

					jInput = {}
					jInput['conf'] = AGM_conf
					jInput['queries'] = jOutputs[pre_module]

					try:
						jInputs[module].append(jInput)
					except KeyError:
						jInputs[module] = [jInput]

			else:
				jInputs[module] = jOutputs[pre_module]
			# /입력 예외처리

			for jInput in jInputs[module]:
				# Execution
				start_time = time.time()

				sInput = json.dumps(jInput)
                                dbc.log(i, module + " is running at " + address + " ...");
                                i += 1
				jOutput = json.loads(exec_module(module, address, sInput))

				elapsed_time = time.time() - start_time

				write_log({'1. module': module, '2. elapsed_time': elapsed_time, '3. input': jInput, '4. output': jOutput})

				# 출력 예외처리
				if module == 'DM':
					try:
						jOutput = jOutput['ned']
					except KeyError:
						fault({'1. module': 'DM', '2. exception': 'wrong output format', '3. output': json.dumps(jOutput)})

					for x in jOutput:
						sOutput2jInput[json.dumps(x)] = jInput
				# /출력 예외처리

				try:
					jOutputs[module] += jOutput
				except KeyError:
					jOutputs[module] = jOutput

		pre_module = module

	result = jOutputs[modules[-1]]

	bye()


def exec_module(module, address, sInput):
	

	sOutput = 'null'

	try:
		# GET / POST transition
		if address == 'http://ws.okbqa.org:2357/agdistis/run': 
			# AGDISTIS only supports the GET method.
			sOutput = send_getrequest(address + '?data=' + urllib.quote(sInput.replace('\\"','"').replace('|','_')))
		else:
			sOutput = send_postrequest(address, sInput)

	# Fault alarming - Module error
	except Exception as e:
		fault({'1. module': module, '2. address': address, '3. exception': str(e), '4. input': json.loads(sInput)})
 
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
		fault({'1. module': module, '2. exception': 'no result returned', '3. address': address, '4. input': sInput, '5. output': sOutput})
	if sOutput.lower() == 'null':
		fault({'1. module': module, '2. exception': 'null-value returned', '3. address': address, '4. input': sInput, '5. output': sOutput})
	
	# Fault alarming - Encoding error
	try:
		sOutput.decode('utf-8')
	except:
		fault({'1. module': module, '2. exception': 'output is not encoded in UTF-8', '3. address': address, '4. input': sInput, '5. output': sOutput})
	
	# Fault alarming - Output format error
	try:
		json.loads(sOutput)
	except:
		fault({'1. module': module, '2. exception': 'output is not formattd in JSON', '3. address': address, '4. input': sInput, '5. output': sOutput})


def write_log(l):
	global log
        global dbc

        dbc.log(-1, json.dumps(l))

	log.append(l)


def fault(l):
	write_log(l)
	bye()


def bye():
	global result
        global dbc
        dbc.log(99, "The process was ended ...")

	output = json.dumps({'log': log, 'result': result}, indent=5, separators=(',', ': '), sort_keys=True)

        dbc.log(100, output)
        dbc.close()

	sys.stdout.write(output)
	sys.stdout.flush()
	sys.exit(0)
	

main()
