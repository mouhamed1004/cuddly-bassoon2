#!/usr/bin/env python3
"""
Script pour corriger automatiquement tous les templates avec des erreurs profileimg
"""
import os
import re
import glob

def fix_template_file(file_path):
    """Corrige un fichier template"""
    print(f"🔧 Correction de {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern pour trouver les utilisations problématiques de profileimg
        patterns = [
            # Pattern 1: {{ user.profile|cloudinary_or_static:'profileimg' }}
            (r'(\{\{\s*user\.profile\|cloudinary_or_static:\'profileimg\'\s*\}\})', 
             r'{% if user.profile and user.profile.profileimg %}\1{% else %}<img src="{% static \'images/default-avatar.png\' %}" alt="Profile">{% endif %}'),
            
            # Pattern 2: {{ user_profile|cloudinary_or_static:'profileimg' }}
            (r'(\{\{\s*user_profile\|cloudinary_or_static:\'profileimg\'\s*\}\})', 
             r'{% if user_profile and user_profile.profileimg %}\1{% else %}<img src="{% static \'images/default-avatar.png\' %}" alt="Profile">{% endif %}'),
            
            # Pattern 3: {{ post.author.profile|cloudinary_or_static:'profileimg' }}
            (r'(\{\{\s*post\.author\.profile\|cloudinary_or_static:\'profileimg\'\s*\}\})', 
             r'{% if post.author.profile and post.author.profile.profileimg %}\1{% else %}<img src="{% static \'images/default-avatar.png\' %}" alt="Photo de profil" class="seller-profile-img">{% endif %}'),
            
            # Pattern 4: {{ highlight.author.profile|cloudinary_or_static:'profileimg' }}
            (r'(\{\{\s*highlight\.author\.profile\|cloudinary_or_static:\'profileimg\'\s*\}\})', 
             r'{% if highlight.author.profile and highlight.author.profile.profileimg %}\1{% else %}<img src="{% static \'images/default-avatar.png\' %}" alt="Profile">{% endif %}'),
            
            # Pattern 5: {{ comment.user.profile|cloudinary_or_static:'profileimg' }}
            (r'(\{\{\s*comment\.user\.profile\|cloudinary_or_static:\'profileimg\'\s*\}\})', 
             r'{% if comment.user.profile and comment.user.profile.profileimg %}\1{% else %}<img src="{% static \'images/default-avatar.png\' %}" alt="Profile">{% endif %}'),
            
            # Pattern 6: {{ member_data.profile|cloudinary_or_static:'profileimg' }}
            (r'(\{\{\s*member_data\.profile\|cloudinary_or_static:\'profileimg\'\s*\}\})', 
             r'{% if member_data.profile and member_data.profile.profileimg %}\1{% else %}<img src="{% static \'images/default-avatar.png\' %}" alt="Profile">{% endif %}'),
            
            # Pattern 7: {{ subscription.subscribed_to.profile|cloudinary_or_static:'profileimg' }}
            (r'(\{\{\s*subscription\.subscribed_to\.profile\|cloudinary_or_static:\'profileimg\'\s*\}\})', 
             r'{% if subscription.subscribed_to.profile and subscription.subscribed_to.profile.profileimg %}\1{% else %}<img src="{% static \'images/default-avatar.png\' %}" alt="Profile">{% endif %}'),
        ]
        
        changes_made = False
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True
                print(f"   ✅ Pattern corrigé: {pattern[:50]}...")
        
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
    print("🚀 CORRECTION AUTOMATIQUE DES TEMPLATES PROFILEIMG")
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
