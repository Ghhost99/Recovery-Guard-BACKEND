#!/bin/bash

echo "🔄 Starting prelaunch migration process..."

# List your apps explicitly here
APPS=("accounts" "cases" "chat" "notifications")

for app in "${APPS[@]}"; do
  echo "📁 Making migrations for $app..."
  python manage.py makemigrations "$app" --noinput
done

echo "📦 Applying all migrations..."
python manage.py migrate --noinput

echo "✅ Prelaunch migration complete!"
python manage.py runserver
