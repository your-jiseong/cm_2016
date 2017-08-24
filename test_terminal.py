# -*- coding: utf-8 -*-

import sys, os, json
from mysql.connector import (connection)

input_string = "{"

input_string += "'input': {'string': 'Which rivers flow through Seoul?', 'language': 'en'}, 'rid': '1212',"
#input_string += "'input': {'string': '서울을 흐르는 강은?', 'language': 'ko'}, "

#input_string += "'input': [{'query': '', 'slots': []}], "

#input_string += "'input': {'ned': [{'classes': [], 'entities': [], 'literals': [], 'properties': [], 'score': 1}]}, "

input_string += "'conf': {'sequence': ['TGM', 'DM', 'QGM', 'AGM']}"
#input_string += "'conf': {'address': {'DM': ['http://ws.okbqa.org:2357/agdistis/run']}, 'sequence': ['DM']}"
#input_string += "'conf': {'address': {'QGM': ['http://ws.okbqa.org:38401/queries']}, 'sequence': ['QGM']}"

input_string += "}"

input_string = '"' + input_string.replace("'", "\\\"") + '"'

print 'python service_terminal.py ', input_string

os.system('python service_terminal.py ' + input_string)