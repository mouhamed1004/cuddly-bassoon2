#!/usr/bin/env bash
# Build script pour Render avec gestion des migrations
# Updated: 2025-10-14 - Force rebuild for migration 0100

set -o errexit  # Exit on error

echo "🚀 DÉBUT DU BUILD RENDER"
echo "========================"

# Installation des dépendances Python
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Gestion intelligente des migrations
echo "🔧 Gestion des migrations..."

# Vérifier si les tables existent déjà
if python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'blizzgame_userwarning')\")
    exists = cursor.fetchone()[0]
    exit(0 if exists else 1)
"; then
    echo "⚠️  Tables détectées - Marquage FAKE des migrations..."
    python fix_migrations.py
else
    echo "✨ Nouvelle base - Application normale des migrations..."
    python manage.py migrate
fi

echo "✅ BUILD TERMINÉ AVEC SUCCÈS !"
echo "🎉 Application prête pour le déploiement"
