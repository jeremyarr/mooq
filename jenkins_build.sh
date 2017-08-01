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

./env/bin/coverage run --source=mooq run_tests.py --unit --integration --output xml --dist ubuntu

./env/bin/coverage xml
./env/bin/coverage html

echo "removing virtualenv"

deactivate
rm -rf env/