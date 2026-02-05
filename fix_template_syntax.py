#!/usr/bin/env python3
"""
Script pour corriger les erreurs de syntaxe Django dans les templates
"""
import os
import re
import glob

def fix_template_syntax(file_path):
    """Corrige les erreurs de syntaxe dans un fichier template"""
    print(f"🔧 Correction de {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern pour corriger les balises HTML imbriquées incorrectes
        # Exemple: <img src="{% if ... %}{{ ... }}{% else %}<img src="{% static '...' %}" ...>{% endif %}" ...>
        # Doit devenir: {% if ... %}<img src="{{ ... }}" ...>{% else %}<img src="{% static '...' %}" ...>{% endif %}
        
        # Pattern 1: Correction des balises img avec des conditions imbriquées
        pattern1 = r'<img src="{% if ([^%]+)%}([^%]+){% else %}<img src="{% static \'([^\']+)\' %}" ([^>]+)>{% endif %}" ([^>]+)>'
        replacement1 = r'{% if \1 %}<img src="\2" \5>{% else %}<img src="{% static \'\3\' %}" \4>{% endif %}'
        
        # Pattern 2: Correction des balises img avec des conditions imbriquées (variante)
        pattern2 = r'<img src="{% if ([^%]+)%}([^%]+){% else %}<img src="{% static \'([^\']+)\' %}" ([^>]+)>{% endif %}" ([^>]+)>'
        replacement2 = r'{% if \1 %}<img src="\2" \5>{% else %}<img src="{% static \'\3\' %}" \4>{% endif %}'
        
        changes_made = False
        
        # Appliquer les corrections
        if re.search(pattern1, content):
            content = re.sub(pattern1, replacement1, content)
            changes_made = True
            print(f"   ✅ Pattern 1 corrigé")
        
        if re.search(pattern2, content):
            content = re.sub(pattern2, replacement2, content)
            changes_made = True
            print(f"   ✅ Pattern 2 corrigé")
        
        # Correction manuelle pour les cas spécifiques
        manual_fixes = [
            # Fix pour les balises avec des conditions complexes
            (
                r'<img src="{% if ([^%]+)%}([^%]+){% else %}<img src="{% static \'([^\']+)\' %}" ([^>]+)>{% endif %}" ([^>]+)>',
                r'{% if \1 %}<img src="\2" \5>{% else %}<img src="{% static \'\3\' %}" \4>{% endif %}'
            ),
            # Fix pour les balises avec des classes spécifiques
            (
                r'<img src="{% if ([^%]+)%}([^%]+){% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)" class="([^"]+)">{% endif %}" alt="([^"]+)" class="([^"]+)">',
                r'{% if \1 %}<img src="\2" alt="\6" class="\7">{% else %}<img src="{% static \'\3\' %}" alt="\4" class="\5">{% endif %}'
            )
        ]
        
        for pattern, replacement in manual_fixes:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True
                print(f"   ✅ Correction manuelle appliquée")
        
        if changes_made:
            # Sauvegarder le fichier modifié
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ Fichier sauvegardé")
            return True
        else:
            print(f"   ⏭️  Aucune correction nécessaire")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    print("🚀 CORRECTION DES ERREURS DE SYNTAXE DJANGO")
    print("=" * 60)
    
    # Trouver tous les fichiers template
    template_files = []
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                template_files.append(os.path.join(root, file))
    
    print(f"📁 {len(template_files)} fichiers template trouvés")
    
    corrected_files = 0
    for template_file in template_files:
        if fix_template_syntax(template_file):
            corrected_files += 1
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"✅ {corrected_files} fichiers corrigés")
    print(f"📁 {len(template_files)} fichiers traités")
    
    if corrected_files > 0:
        print("🎉 Corrections terminées !")
    else:
        print("ℹ️  Aucune correction nécessaire")

if __name__ == "__main__":
    main()
