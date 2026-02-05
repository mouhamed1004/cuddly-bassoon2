#!/usr/bin/env bash
# Script de build pour Render

set -e  # Arrêter en cas d'erreur

echo "🚀 Début du build..."

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Résoudre les conflits de migrations
echo "🗄️ Résolution intelligente des migrations..."
python manage.py smart_migrate

echo "✅ Build terminé avec succès!"
