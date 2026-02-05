# 🚀 Guide d'optimisation Render - Réduction des coûts

## 📊 Problèmes identifiés

### 1. **Synchronisation Shopify excessive** ⚠️
- **Problème**: Script `sync_shopify_task.bat` qui tourne toutes les 15 minutes (96x/jour)
- **Impact**: 
  - Consommation de bande passante inutile
  - Logs qui s'accumulent (`sync_shopify.log` - 114 entrées en 3 jours)
  - Requêtes API Shopify excessives
- **Solution**: ✅ Désactivé localement, utiliser webhooks Shopify à la place

### 2. **Absence de rotation des logs** 📝
- **Problème**: Les logs s'accumulent indéfiniment sans limite
- **Impact**: Stockage qui augmente continuellement
- **Solution**: ✅ Configuration de `RotatingFileHandler` (max 5MB, 2 backups)

### 3. **Configuration Redis non optimale** 🔴
- **Problème**: 
  - `max_connections: 50` trop élevé pour faible trafic
  - Pas de TTL sur le cache
  - Pas de compression
- **Impact**: Utilisation mémoire Redis excessive
- **Solution**: ✅ Réduit à 10 connexions + compression + TTL 1h

---

## ✅ Optimisations appliquées

### 1. Configuration de logging optimisée
```python
# settings.py
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB max
            'backupCount': 2,  # Seulement 2 fichiers de backup
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',  # Désactiver les logs SQL
        },
    },
}
```

### 2. Redis optimisé pour faible trafic
```python
CACHES = {
    'default': {
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 10,  # Réduit de 50 à 10
            },
            'TIMEOUT': 3600,  # TTL 1 heure
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
    }
}
```

### 3. .gitignore amélioré
- Exclusion des fichiers `.log`
- Exclusion du dossier `logs/`
- Exclusion de `sync_shopify.log`

---

## 🎯 Actions à effectuer

### Sur votre machine locale

1. **Désactiver la tâche planifiée Windows**
   ```powershell
   # Ouvrir le Planificateur de tâches Windows
   # Rechercher "sync_shopify" et désactiver/supprimer
   ```

2. **Supprimer le fichier log existant**
   ```bash
   rm sync_shopify.log
   ```

### Sur Render

1. **Vérifier les variables d'environnement**
   - Assurez-vous que `DEBUG=False` en production
   - Vérifiez que `REDIS_URL` est bien configuré

2. **Monitorer l'utilisation**
   - Dashboard Render → Metrics
   - Vérifier la baisse de consommation après déploiement

3. **Alternative aux cron jobs**
   - Utiliser les **webhooks Shopify** au lieu de polling
   - Configuration: `python manage.py setup_shopify_webhooks --base-url https://votre-site.onrender.com`

---

## 📉 Réductions attendues

| Métrique | Avant | Après | Économie |
|----------|-------|-------|----------|
| Requêtes Shopify/jour | 96 | 0-5 (webhooks) | **95%** |
| Stockage logs | Illimité | Max 15 MB | **~90%** |
| Connexions Redis | 50 max | 10 max | **80%** |
| Logs SQL | Tous | Erreurs seulement | **~70%** |

---

## 🔍 Monitoring continu

### Commandes utiles

```bash
# Vérifier la taille des logs
du -sh logs/

# Vérifier les connexions Redis actives
redis-cli INFO clients

# Monitorer l'utilisation mémoire
free -h

# Vérifier les processus Python
ps aux | grep python
```

### Alertes à configurer sur Render

1. **Stockage > 80%** → Vérifier les logs
2. **Mémoire Redis > 90%** → Vérifier le cache
3. **Bande passante excessive** → Vérifier les requêtes API

---

## 🛠️ Maintenance recommandée

### Hebdomadaire
- Vérifier la taille du dossier `logs/`
- Monitorer les métriques Render

### Mensuel
- Analyser les logs d'erreurs
- Vérifier les webhooks Shopify
- Optimiser les requêtes DB si nécessaire

### Trimestriel
- Revoir la configuration Redis
- Analyser les patterns d'utilisation
- Ajuster les limites si le trafic augmente

---

## 📚 Ressources

- [Documentation Render - Optimisation](https://render.com/docs/optimization)
- [Django Logging Best Practices](https://docs.djangoproject.com/en/stable/topics/logging/)
- [Redis Memory Optimization](https://redis.io/docs/management/optimization/)
- [Shopify Webhooks](https://shopify.dev/docs/api/admin-rest/2024-01/resources/webhook)

---

## 🆘 Support

Si vous rencontrez des problèmes après ces optimisations :

1. Vérifier les logs Render
2. Tester localement avec `DEBUG=True`
3. Vérifier la connectivité Redis
4. Contacter le support Render si nécessaire

**Date de dernière mise à jour**: 4 décembre 2025
