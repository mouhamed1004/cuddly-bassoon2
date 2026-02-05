#!/usr/bin/env python
"""
Script pour tester avec PostgreSQL local
"""
import os
import sys
import subprocess

def install_postgresql():
    """Instructions pour installer PostgreSQL"""
    print("📋 INSTRUCTIONS POUR INSTALLER POSTGRESQL LOCAL")
    print("=" * 60)
    print("1. Téléchargez PostgreSQL depuis: https://www.postgresql.org/download/")
    print("2. Installez avec les paramètres par défaut")
    print("3. Créez une base de données 'blizzgame_test'")
    print("4. Configurez les variables d'environnement:")
    print("")
    print("   DATABASE_URL=postgresql://postgres:password@localhost:5432/blizzgame_test")
    print("")
    print("5. Exécutez: python test_postgresql_compatibility.py")

def test_with_docker():
    """Alternative avec Docker"""
    print("🐳 ALTERNATIVE AVEC DOCKER")
    print("=" * 60)
    print("1. Installez Docker Desktop")
    print("2. Exécutez cette commande:")
    print("")
    print("   docker run --name postgres-test -e POSTGRES_PASSWORD=password -e POSTGRES_DB=blizzgame_test -p 5432:5432 -d postgres:15")
    print("")
    print("3. Configurez DATABASE_URL:")
    print("   DATABASE_URL=postgresql://postgres:password@localhost:5432/blizzgame_test")
    print("")
    print("4. Exécutez: python test_postgresql_compatibility.py")

def create_test_env():
    """Créer un fichier .env de test"""
    env_content = """# Configuration de test avec PostgreSQL local
DEBUG=True
SECRET_KEY=test-secret-key-for-local-testing
DATABASE_URL=postgresql://postgres:password@localhost:5432/blizzgame_test
ALLOWED_HOSTS=localhost,127.0.0.1
CINETPAY_API_KEY=test-key
CINETPAY_SITE_ID=test-site
CINETPAY_SECRET_KEY=test-secret
EMAIL_HOST_USER=test@example.com
EMAIL_HOST_PASSWORD=test-password
BASE_URL=http://localhost:8000
ENVIRONMENT=development
"""
    
    with open('.env.test', 'w') as f:
        f.write(env_content)
    
    print("✅ Fichier .env.test créé")
    print("📝 Configurez votre mot de passe PostgreSQL dans ce fichier")

def main():
    print("🔧 CONFIGURATION POUR TESTER AVEC POSTGRESQL")
    print("=" * 60)
    
    print("\n🎯 OBJECTIF: Tester la configuration SSL pour Render")
    print("📊 Actuellement: SQLite local (pas de SSL)")
    print("📊 Nécessaire: PostgreSQL local (avec SSL)")
    
    print("\n📋 OPTIONS DISPONIBLES:")
    print("1. Installation PostgreSQL locale")
    print("2. Utilisation Docker (recommandé)")
    print("3. Test direct sur Render (production)")
    
    print("\n🚀 RECOMMANDATION: Option 3 - Test direct sur Render")
    print("   - Plus simple et plus réaliste")
    print("   - Teste la vraie configuration de production")
    print("   - Évite les problèmes d'installation locale")
    
    install_postgresql()
    print("\n" + "="*60)
    test_with_docker()
    print("\n" + "="*60)
    create_test_env()

if __name__ == "__main__":
    main()
