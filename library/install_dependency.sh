DIR="${PWD}"
# install CherryPy
cd "${DIR}/CherryPy-3.6.0"
python setup.py install
cd ..
# install Python-MySQL connector
pip install mysql-connector==2.1.4