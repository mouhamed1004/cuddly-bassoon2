#!/bin/bash
# Script de démarrage pour Sevalla - gère PORT vide et migrations
set -e

# Port par défaut 8080 si $PORT n'est pas défini (bug connu Sevalla)
PORT="${PORT:-8080}"
export PORT

echo "🚀 Démarrage BLIZZ sur le port $PORT"

# Migrations (obligatoire pour django_site, etc.)
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Démarrer Gunicorn
echo "🌐 Démarrage Gunicorn..."
exec gunicorn socialgame.wsgi:application --bind "0.0.0.0:$PORT" --workers 2 --timeout 120
