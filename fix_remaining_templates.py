#!/usr/bin/env python3
"""
Script pour corriger les templates restants avec des erreurs de syntaxe
"""
import os
import re

def fix_template_file(file_path):
    """Corrige les erreurs de syntaxe dans un fichier template"""
    print(f"🔧 Correction de {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern pour corriger les balises HTML imbriquées incorrectes
        patterns = [
            # Pattern 1: user_profile
            (
                r'<img src="{% if user_profile and user_profile\.profileimg %}{{ user_profile\|cloudinary_or_static:\'profileimg\' }}{% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)">{% endif %}" alt="([^"]+)">',
                r'{% if user_profile and user_profile.profileimg %}<img src="{{ user_profile|cloudinary_or_static:\'profileimg\' }}" alt="\3">{% else %}<img src="{% static \'\1\' %}" alt="\2">{% endif %}'
            ),
            # Pattern 2: user.profile
            (
                r'<img src="{% if user\.profile and user\.profile\.profileimg %}{{ user\.profile\|cloudinary_or_static:\'profileimg\' }}{% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)">{% endif %}" alt="([^"]+)">',
                r'{% if user.profile and user.profile.profileimg %}<img src="{{ user.profile|cloudinary_or_static:\'profileimg\' }}" alt="\3">{% else %}<img src="{% static \'\1\' %}" alt="\2">{% endif %}'
            ),
            # Pattern 3: post.author.profile
            (
                r'<img src="{% if post\.author\.profile and post\.author\.profile\.profileimg %}{{ post\.author\.profile\|cloudinary_or_static:\'profileimg\' }}{% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)" class="([^"]+)">{% endif %}" alt="([^"]+)" class="([^"]+)">',
                r'{% if post.author.profile and post.author.profile.profileimg %}<img src="{{ post.author.profile|cloudinary_or_static:\'profileimg\' }}" alt="\4" class="\5">{% else %}<img src="{% static \'\1\' %}" alt="\2" class="\3">{% endif %}'
            ),
            # Pattern 4: highlight.author.profile
            (
                r'<img src="{% if highlight\.author\.profile and highlight\.author\.profile\.profileimg %}{{ highlight\.author\.profile\|cloudinary_or_static:\'profileimg\' }}{% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)" class="([^"]+)">{% endif %}" alt="([^"]+)" class="([^"]+)">',
                r'{% if highlight.author.profile and highlight.author.profile.profileimg %}<img src="{{ highlight.author.profile|cloudinary_or_static:\'profileimg\' }}" alt="\4" class="\5">{% else %}<img src="{% static \'\1\' %}" alt="\2" class="\3">{% endif %}'
            ),
            # Pattern 5: comment.user.profile
            (
                r'<img src="{% if comment\.user\.profile and comment\.user\.profile\.profileimg %}{{ comment\.user\.profile\|cloudinary_or_static:\'profileimg\' }}{% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)">{% endif %}" alt="([^"]+)">',
                r'{% if comment.user.profile and comment.user.profile.profileimg %}<img src="{{ comment.user.profile|cloudinary_or_static:\'profileimg\' }}" alt="\3">{% else %}<img src="{% static \'\1\' %}" alt="\2">{% endif %}'
            ),
            # Pattern 6: member_data.profile
            (
                r'<img src="{% if member_data\.profile and member_data\.profile\.profileimg %}{{ member_data\.profile\|cloudinary_or_static:\'profileimg\' }}{% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)" class="([^"]+)">{% endif %}" alt="([^"]+)" class="([^"]+)">',
                r'{% if member_data.profile and member_data.profile.profileimg %}<img src="{{ member_data.profile|cloudinary_or_static:\'profileimg\' }}" alt="\4" class="\5">{% else %}<img src="{% static \'\1\' %}" alt="\2" class="\3">{% endif %}'
            ),
            # Pattern 7: subscription.subscribed_to.profile
            (
                r'<img src="{% if subscription\.subscribed_to\.profile and subscription\.subscribed_to\.profile\.profileimg %}{{ subscription\.subscribed_to\.profile\|cloudinary_or_static:\'profileimg\' }}{% else %}<img src="{% static \'([^\']+)\' %}" alt="([^"]+)">{% endif %}" alt="([^"]+)">',
                r'{% if subscription.subscribed_to.profile and subscription.subscribed_to.profile.profileimg %}<img src="{{ subscription.subscribed_to.profile|cloudinary_or_static:\'profileimg\' }}" alt="\3">{% else %}<img src="{% static \'\1\' %}" alt="\2">{% endif %}'
            )
        ]
        
        changes_made = False
        
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True
                print(f"   ✅ Pattern corrigé")
        
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
    print("🚀 CORRECTION DES TEMPLATES RESTANTS")
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
        if fix_template_file(template_file):
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
