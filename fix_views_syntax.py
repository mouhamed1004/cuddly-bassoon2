#!/usr/bin/env python3
"""
Script pour corriger les erreurs de syntaxe dans blizzgame/views.py
"""
import re

def fix_views_syntax():
    """Corrige les erreurs de syntaxe dans views.py"""
    print("🔧 CORRECTION DES ERREURS DE SYNTAXE")
    print("=" * 60)
    
    try:
        # Lire le fichier
        with open('blizzgame/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 Fichier lu: {len(content)} caractères")
        
        # Corriger les erreurs d'indentation communes
        fixes_applied = 0
        
        # Fix 1: Corriger les blocs try sans except
        # Chercher les patterns problématiques
        patterns_to_fix = [
            # Pattern: try: suivi d'une ligne non indentée
            (r'(\s+)try:\s*\n(\s+)([^#\s].*)', r'\1try:\n\2    \3'),
            # Pattern: else: suivi d'une ligne non indentée
            (r'(\s+)else:\s*\n(\s+)([^#\s].*)', r'\1else:\n\2    \3'),
            # Pattern: except: suivi d'une ligne non indentée
            (r'(\s+)except.*:\s*\n(\s+)([^#\s].*)', r'\1except Exception as e:\n\2    \3'),
        ]
        
        for pattern, replacement in patterns_to_fix:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                content = new_content
                fixes_applied += 1
                print(f"✅ Fix appliqué: {pattern[:50]}...")
        
        # Fix 2: Corriger les context dictionaries mal indentés
        # Chercher les context = { mal indentés
        context_pattern = r'(\s+)context = \{\s*\n(\s+)([^}]+)\n(\s+)\}'
        context_replacement = r'\1context = {\n\2    \3\n\1}'
        
        new_content = re.sub(context_pattern, context_replacement, content, flags=re.MULTILINE | re.DOTALL)
        if new_content != content:
            content = new_content
            fixes_applied += 1
            print("✅ Fix appliqué: context dictionaries")
        
        # Fix 3: Corriger les lignes dans les blocs try/except mal indentées
        # Chercher les lignes qui devraient être indentées dans les blocs
        block_patterns = [
            # Dans les blocs try
            (r'(\s+)try:\s*\n(\s+)([^#\s].*)\n(\s+)([^#\s].*)', r'\1try:\n\2    \3\n\2    \4'),
            # Dans les blocs else
            (r'(\s+)else:\s*\n(\s+)([^#\s].*)\n(\s+)([^#\s].*)', r'\1else:\n\2    \3\n\2    \4'),
        ]
        
        for pattern, replacement in block_patterns:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                content = new_content
                fixes_applied += 1
                print(f"✅ Fix appliqué: blocs mal indentés")
        
        # Sauvegarder le fichier corrigé
        if fixes_applied > 0:
            with open('blizzgame/views.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 Fichier sauvegardé avec {fixes_applied} corrections")
        else:
            print("ℹ️  Aucune correction nécessaire")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_syntax():
    """Test la syntaxe du fichier corrigé"""
    print(f"\n🧪 TEST DE SYNTAXE")
    print("=" * 60)
    
    try:
        import py_compile
        py_compile.compile('blizzgame/views.py', doraise=True)
        print("✅ Syntaxe correcte !")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Erreur de syntaxe: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    print("🚀 CORRECTION DES ERREURS DE SYNTAXE")
    print("=" * 60)
    
    success = True
    
    # Correction
    if not fix_views_syntax():
        success = False
    
    # Test de syntaxe
    if not test_syntax():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 CORRECTION TERMINÉE AVEC SUCCÈS !")
        print("✅ Toutes les erreurs de syntaxe ont été corrigées")
        print("✅ Le fichier est prêt pour le déploiement")
    else:
        print("❌ CERTAINES ERREURS PERSISTENT")
        print("⚠️  Vérifiez manuellement les erreurs restantes")

if __name__ == "__main__":
    main()
