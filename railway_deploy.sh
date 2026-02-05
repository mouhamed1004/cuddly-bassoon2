#!/bin/bash
# Script de déploiement Railway avec migrations automatiques

echo "🚀 Démarrage du déploiement Railway..."

# Exécuter les migrations
echo "📊 Exécution des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques (si nécessaire)
# echo "📦 Collecte des fichiers statiques..."
# python manage.py collectstatic --noinput

# Démarrer Gunicorn
echo "🌐 Démarrage de Gunicorn..."
gunicorn socialgame.wsgi:application --bind 0.0.0.0:$PORT
