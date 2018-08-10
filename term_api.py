# -*- coding: utf-8 -*-

import sys

# --

import json

# --

conf = {}

module2i_json = {}
module2o_json = {}

ned2template = {}

log = []
result = []

db_conn = None

# --

def main():
	global module2i_json

	module2i_json['CM'] = json.loads(sys.argv[1])

	write_log({'module': 'CM', 'input': module2i_json['CM']})

	# --

	if 'rid' in module2i_json['CM'].keys():	
		set_db()

	set_conf()

	run_pipeline()
			
	bye()

# --

def set_db():
	global db_conn

	# --
			
	db_conn = DBConn(module2i_json['CM']['rid'])

	# --

	db_conn.log(5, "The process was started ...")
	db_conn.log(10, "The process is undergoing ...")

# --

class DBConn:
	def __init__(self, rid=""):
		from mysql.connector import (connection)

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

# --

def set_conf():
	global conf

	# --

	if db_conn:
		db_conn.log(15, "Setting configuration ...")

	# --

	conf = get_default_conf()

	# --

	try:
		conf.update(module2i_json['CM']['conf'])
	
	except:
		pass

	# --

	if db_conn:
		db_conn.log(20, "Configured ...")

# --

def get_default_conf():
	conf = {}

	# --

	with open('config/default.conf', 'r') as i_file:
		i_text = i_file.read()

	# --

	conf = json.loads(i_text)

	# --

	try:
		if module2i_json['CM']['input']['language'] == 'en':
			with open('config/default-en.conf', 'r') as i_file:
				i_text = i_file.read()

		elif module2i_json['CM']['input']['language'] == 'ko':
			with open('config/default-ko.conf', 'r') as i_file:
				i_text = i_file.read()

		conf.update(json.loads(i_text))

	except:
		pass

	# --

	return conf

# --
		
def run_pipeline():
	global module2i_json
	global module2o_json

	global result

	# --

	if db_conn:
		db_conn.log(25, "Pipeline was initiated ...")

		i = 30

	# --

	pre_module = 'CM'

	# --

	modules = conf['sequence']

	for module in modules:
		for address in conf['address'][module]:
			if db_conn:
				db_conn.log(i, module + " is running at " + address + " ...")

				i += 2

			# -- 입력 파싱

			if pre_module == 'CM' and module == 'ELU':
				i_json = {}

				i_json['text'] = module2i_json['CM']['input']['string']
				i_json['lower_bound'] = 0.75

				# --

				try:
					module2i_json[module].append(i_json)

				except KeyError:
					module2i_json[module] = [i_json]

			# --

			elif pre_module == 'CM' and module == 'TGM':
				i_json = {}

				i_json['string'] = module2i_json['CM']['input']['string']
				i_json['language'] = module2i_json['CM']['input']['language']

				# --
				
				try:
					module2i_json[module].append(i_json)

				except KeyError:
					module2i_json[module] = [i_json]

			# --

			elif pre_module == 'ELU' and module == 'TGM':
				for o_json in module2o_json[pre_module]:
					i_json = {}

					i_json['entities'] = o_json
					i_json['string'] = module2i_json['CM']['input']['string']
					i_json['language'] = module2i_json['CM']['input']['language']
					
					# --

					try:
						module2i_json[module].append(i_json)

					except KeyError:
						module2i_json[module] = [i_json]

			# --

			elif pre_module == 'TGM' and module == 'DM':
				for o_json in module2o_json[pre_module]:
					for template in o_json:
						i_json = {}

						i_json['question'] = module2i_json['CM']['input']['string']

						i_json.update(template)

						# --

						try:
							module2i_json[module].append(i_json)

						except KeyError:
							module2i_json[module] = [i_json]

			# --

			elif pre_module == 'DM' and module == 'QGM':
				for o_json in module2o_json[pre_module]:
					for ned in o_json['ned']:
						i_json = {}

						i_json['template'] = ned2template[json.dumps(ned)]

						i_json['disambiguation'] = ned

						# --

						try:
							module2i_json[module].append(i_json)

						except KeyError:
							module2i_json[module] = [i_json]

			# --

			elif pre_module == 'QGM' and module == 'AGM':
				for kb_address, graph_iri in conf['address']['KB']:
					if db_conn:
						db_conn.log(70, "AGM is running on " + graph_iri + " in " + kb_address + " ...")

						i = 70

					# --

					for o_json in module2o_json[pre_module]:
						i_json = {}

						i_json['conf'] = {'kb_addresses': kb_address, 'graph_uri': graph_iri}

						i_json['queries'] = o_json

						# --

						try:
							module2i_json[module].append(i_json)

						except KeyError:
							module2i_json[module] = [i_json]

			# --

			else:
				for o_json in module2o_json[pre_module]:
					try:
						module2i_json[module].append(o_json)

					except KeyError:
						module2i_json[module] = [o_json]

			# -- 모듈 실행

			for i_json in module2i_json[module]:
				import time

				start_time = time.time()

				# --

				i_text = json.dumps(i_json)

				# --

				if db_conn:
					db_conn.log(i, module + " is running at " + address + " ...")

					i += 1

				# --

				o_json = json.loads(exec_module(module, address, i_text))

				# --

				elapsed_time = time.time() - start_time

				# --

				write_log({'module': module, 'elapsed_time': elapsed_time, 'input': i_json, 'output': o_json})

				# -- 출력 파싱

				if module == 'DM':
					for ned in o_json['ned']:
						ned2template[json.dumps(ned)] = i_json
				
				# --

				try:
					module2o_json[module].append(o_json)

				except KeyError:
					module2o_json[module] = [o_json]

		# --

		pre_module = module

	# --

	if modules[-1] == 'AGM':
		for answer_list in module2o_json['AGM']:
			result += answer_list

	else:
		result = module2o_json[modules[-1]]

	bye()

# --

def exec_module(module, address, i_text):
	# -- 입력 포멧 검증

	check_input(module, address, i_text)

	# -- 모듈 실행

	try:
		if 'agdistis/run' in address: 
			import urllib

			o_text = get_request(address + '?data=' + urllib.quote(i_text.replace('\\"','"').replace('|','_')))

		else:
			o_text = post_request(address, i_text)

	except Exception as e:
		alarm_fault({'module': module, 'address': address, 'exception': 'an error occurred while requesting to the module; exception message: ' + str(e), 'input': json.loads(i_text)})
 
	# -- 출력 검증

	check_output(module, address, i_text, o_text)

	# --

	return o_text

# --

def get_request(url):
	import urllib2

	opener = urllib2.build_opener()

	request = urllib2.Request(url)

	# --

	from socket import timeout

	return opener.open(request, timeout=conf['timelimit']).read()
	
def post_request(url, i_text):
	import urllib2

	opener = urllib2.build_opener()

	request = urllib2.Request(url, data=i_text, headers={'Content-Type':'application/json'})

	# --

	from socket import timeout

	return opener.open(request, timeout=conf['timelimit']).read()

# --

def check_input(module, address, i_text):
	i_json = json.loads(i_text)

	# -- input format error

	is_correct = True

	try:
		if module == 'TGM':
			if type(i_json['string']) != type(u''):
				is_correct = False

			if type(i_json['language']) != type(u''):
				is_correct = False

		# --

		elif module == 'DM':
			if type(i_json['query']) != type(u''):
				is_correct = False

			if type(i_json['slots']) != type([]):
				is_correct = False

			if type(i_json['question']) != type(u''):
				is_correct = False

		# --

		elif module == 'QGM':
			if type(i_json['disambiguation']) != type({}):
				is_correct = False

			if type(i_json['template']) != type({}):
				is_correct = False

		# --

		elif module == 'AGM':
			if type(i_json['queries']) != type([]):
				is_correct = False

	except:
		is_correct = False

	# --

	if not is_correct:
		alarm_fault({'module': module, 'address': address, 'exception': 'incorrect input format', 'input': i_json})

def check_output(module, address, i_text, o_text):
	i_json = json.loads(i_text)

	# -- empty error

	if len(o_text) <= 0:
		alarm_fault({'module': module, 'address': address, 'exception': 'empty output', 'input': i_json, 'output': o_text})

	if o_text.lower() == 'null':
		alarm_fault({'module': module, 'address': address, 'exception': 'null output', 'input': i_json, 'output': o_text})
	
	# -- encoding error

	try:
		o_text.decode('utf-8')

	except:
		alarm_fault({'module': module, 'address': address, 'exception': 'output is not UTF-8', 'input': i_json, 'output': o_text})
	
	# -- json error

	try:
		json.loads(o_text)

	except:
		alarm_fault({'module': module, 'address': address, 'exception': 'output is not JSON', 'input': i_json, 'output': o_text})

	# -- output format error

	o_json = json.loads(o_text)

	# --

	is_correct = True

	try:
		if module == 'TGM':
			if type(o_json) != type([]):
				is_correct = False

			for template in o_json:
				if type(template['query']) != type(u''):
					is_correct = False

				if type(template['slots']) != type([]):
					is_correct = False

		# --

		elif module == 'DM':
			if type(o_json['ned']) != type([]):
				is_correct = False

			for ned in o_json['ned']:
				if type(ned['classes']) != type([]):
					is_correct = False

				if type(ned['entities']) != type([]):
					is_correct = False

				if type(ned['literals']) != type([]):
					is_correct = False

				if type(ned['properties']) != type([]):
					is_correct = False

		# --

		elif module == 'QGM':
			if type(o_json) != type([]):
				is_correct = False

			for query in o_json:
				if type(query['query']) != type(u''):
					is_correct = False

		# --
		
		elif module == 'AGM':
			if type(o_json) != type([]):
				is_correct = False

			for answer in o_json:
				if type(answer['answer']) != type(u''):
					is_correct = False

	except:
		is_correct = False

	# --

	if not is_correct:
		alarm_fault({'module': module, 'address': address, 'exception': 'incorrect output format', 'input': i_json, 'output': o_json})

def alarm_fault(message):
	write_log(message)

	bye()

# --

def write_log(message):
	global log
	
	# --

	if db_conn:
		db_conn.log(-1, json.dumps(message))

	# --

	log.append(message)

# --

def bye():
	if db_conn:
		db_conn.log(99, "The process was ended ...")

	# --

	output = json.dumps({'log': log, 'result': result}, indent=4, separators=(',', ': '))

	# --

	if db_conn:
		db_conn.log(100, output)

		db_conn.close()

	# --

	sys.stdout.write(output)
	sys.stdout.flush()
	sys.exit(0)

# --

if __name__ == '__main__':
	main()