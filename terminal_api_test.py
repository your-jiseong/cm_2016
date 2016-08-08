# -*- coding: utf-8 -*-

import sys, os, json
'''
input_string = "{"
input_string += "'string': 'Which rivers flow through Seoul?', "
input_string += "'language': 'en', "
input_string += "'conf': {'sequence': ['TGM', 'DM', 'QGM', 'AGM']}"
input_string += "}"

input_string = "{"
input_string += "'string': '어떤 강이 서울을 흐르는가?', "
input_string += "'language': 'ko', "
input_string += "'conf': {}"
input_string += "}"
'''

input_string = "{"
input_string += "'string': '어떤 강이 서울을 흐르는가?', "
input_string += "'language': 'ko', "
input_string += "'conf': {'sequence': ['TGM', 'DM', 'QGM', 'AGM']}"
input_string += "}"

input_string = '"' + input_string.replace("'", "\\\"") + '"'
print input_string

os.system('python terminal_api.py ' + input_string)