

set -e  # exit immediately if any command fails

echo "── Installing dependencies ──"
pip install -r requirements.txt

echo "── Collecting static files ──"
python manage.py collectstatic --no-input

echo "── Running database migrations ──"
python manage.py migrate --no-input

echo "── Build complete ✓ ──"

