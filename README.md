OKBQA Control Module 2016
=====================================

General description
-----
Please refer to: https://sites.google.com/site/okbqa0/architecture/control.

Updates
-----
* v1.0.0: https://sites.google.com/site/okbqa4/development/documentation/controller?pli=1
* v1.1.0: There is inclusive of the function that each log message is pushed into a mysql database when the message is generated. By this function, a Web interface can trace log messages in the middle of a running pipeline through the mysql database.
* v1.2.0: Now, Controller checks whether I/O formats of user-provided modules are consistent with the standard I/O specification of OKBQA. When Controller faces the inconsistency of I/O formats against the standard specification, it immediately stops the pipeline and reports about the inconsistency to users. This I/O format checking is done only if names of modules specified in the configuration of Controller are one of "TGM", "DM", "QGM", or "AGM". Otherwise, you can use any freely designed I/O formats for your own specification of a pipeline.

Prerequisite
-----
1) Install Python2
2) Install Cherrypy v3.6.0 (the setup file is located in the folder "library")

How to run
-----
python rest_api.py

AUTHOR(S)
---------
* Jiseong Kim, MachineReadingLab@KAIST

License
-------
Released under the MIT license (http://opensource.org/licenses/MIT).