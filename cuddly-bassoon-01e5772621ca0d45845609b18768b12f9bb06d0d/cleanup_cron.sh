#!/bin/bash
# Script de nettoyage automatique des transactions abandonnées
# À exécuter toutes les 10 minutes

# Aller dans le répertoire du projet
cd /opt/render/project/src

# Exécuter le nettoyage avec timeout de 30 minutes
python3 manage.py cleanup_expired_transactions --timeout-minutes=30

# Log de fin
echo "$(date): Nettoyage des transactions terminé" >> /tmp/cleanup.log
