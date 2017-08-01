echo "executing build step!!!"
echo $PWD
whoami

echo "removing virtualenv"
rm -rf env/

echo "installing new virtualenv"
virtualenv --python=python3.6 env

echo "activating virtualenv"
. env/bin/activate

echo "installing required packages"
pip install -r requirements_dev.txt

echo "performing test"

coverage run --source=mooq run_tests.py --unit --integration --output xml --dist ubuntu

coverage xml
coverage html

echo "removing virtualenv"

deactivate
rm -rf env/