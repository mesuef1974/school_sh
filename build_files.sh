
# build_files.sh
echo "Building the project..."

# Ensure pip is available and install requirements
python3.9 -m ensurepip --default-pip
python3.9 -m pip install -r requirements.txt

echo "Make Migration..."
python3.9 manage.py makemigrations
python3.9 manage.py migrate

echo "Collect Static..."
python3.9 manage.py collectstatic --noinput --clear

echo "Build End"