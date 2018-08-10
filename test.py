# -*- coding: utf-8 -*-

def main():
	test_180808()

# --

def test_180808():
	i_text = '{"input": {"string": "Which rivers flow through Seoul?", "language": "en"}}'

	i_text = '"' + i_text.replace("\"", "\\\"") + '"'

	# --

	command = ' '.join(['python term_api.py', i_text])

	print command

	# --

	import os

	os.system(command)

# --

if __name__ == '__main__':
	main()
