# 🚀 Guide de Démarrage Rapide

## 📋 Prérequis

- Docker Desktop installé et démarré
- Au moins 8 GB de RAM disponible
- Ports disponibles: 8080, 8081, 8082, 8501, 9000, 9870

## ⚡ Démarrage en 5 Minutes

### 1️⃣ Cloner et naviguer vers le projet
```powershell
cd d:\CodePlagiat
```

### 2️⃣ Build des images Docker
```powershell
docker-compose build
```
⏱️ Durée estimée: 10-15 minutes (première fois uniquement)

### 3️⃣ Démarrer le cluster
```powershell
docker-compose up -d
```
⏱️ Durée: 30-60 secondes

### 4️⃣ Vérifier l'état des conteneurs
```powershell
docker-compose ps
```

Vous devriez voir 4 conteneurs:
- ✅ `spark-master` (healthy)
- ✅ `spark-worker-1` (healthy)
- ✅ `spark-worker-2` (healthy)
- ✅ `app-client` (healthy)

### 5️⃣ Accéder aux interfaces

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Application Streamlit** | http://localhost:8501 | Interface utilisateur |
| ⚡ **Spark Master UI** | http://localhost:8080 | Monitoring Spark |
| 👷 **Worker 1 UI** | http://localhost:8081 | État Worker 1 |
| 👷 **Worker 2 UI** | http://localhost:8082 | État Worker 2 |
| 📁 **HDFS NameNode UI** | http://localhost:9870 | Système de fichiers |

## 🧪 Test Rapide

### Option 1: Via l'interface Streamlit

1. Ouvrir http://localhost:8501
2. Uploader des fichiers sources (`.py`, `.cpp`, `.java`)
3. Cliquer sur "Upload vers HDFS"
4. Cliquer sur "Démarrer l'analyse"
5. Consulter les résultats dans l'onglet "Résultats"

### Option 2: Via la ligne de commande

```powershell
# 1. Copier les exemples vers HDFS
docker exec spark-master hdfs dfs -put /app/data/input/*.py /app/input/

# 2. Lancer le job PySpark
docker exec spark-master spark-submit `
  --master spark://spark-master:7077 `
  /app/src/spark_jobs/detect_plagiarism.py `
  --input hdfs://spark-master:9000/app/input `
  --output hdfs://spark-master:9000/app/output

# 3. Voir les résultats
docker exec spark-master hdfs dfs -cat /app/output/part-00000-*.csv
```

## 📊 Commandes Utiles

### Gestion du Cluster

```powershell
# Arrêter le cluster
docker-compose down

# Arrêter et supprimer les volumes (réinitialisation complète)
docker-compose down -v

# Voir les logs d'un conteneur
docker-compose logs -f spark-master

# Redémarrer un service
docker-compose restart spark-worker-1
```

### Interaction avec HDFS

```powershell
# Lister les fichiers HDFS
docker exec spark-master hdfs dfs -ls /app/input

# Créer un répertoire
docker exec spark-master hdfs dfs -mkdir -p /app/test

# Upload un fichier
docker exec spark-master hdfs dfs -put /app/data/input/example1.py /app/input/

# Télécharger un fichier
docker exec spark-master hdfs dfs -get /app/output/results.csv /tmp/

# Supprimer un fichier
docker exec spark-master hdfs dfs -rm /app/input/example1.py
```

### Interaction avec Spark

```powershell
# Lancer un shell PySpark
docker exec -it spark-master pyspark --master spark://spark-master:7077

# Voir les applications Spark actives
docker exec spark-master curl http://localhost:8080/json/

# Tuer une application Spark
docker exec spark-master /opt/spark/sbin/stop-all.sh
docker exec spark-master /opt/spark/sbin/start-all.sh
```

## 🔍 Dépannage

### Problème: Les conteneurs ne démarrent pas

**Solution:**
```powershell
# Vérifier les logs
docker-compose logs

# Réinitialiser complètement
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Problème: HDFS NameNode ne démarre pas

**Solution:**
```powershell
# Reformater le NameNode
docker exec spark-master hdfs namenode -format -force
docker-compose restart spark-master
```

### Problème: Spark Workers ne se connectent pas

**Solution:**
```powershell
# Vérifier que le Master est démarré
docker exec spark-master nc -zv spark-master 7077

# Redémarrer les workers
docker-compose restart spark-worker-1 spark-worker-2
```

### Problème: Port déjà utilisé

**Solution:**
```powershell
# Trouver le processus utilisant le port
netstat -ano | findstr :8080

# Tuer le processus (remplacer PID)
taskkill /PID <PID> /F

# Ou modifier les ports dans docker-compose.yml
```

## 📈 Monitoring

### Vérifier la santé du cluster

```powershell
# Status des conteneurs
docker-compose ps

# Ressources utilisées
docker stats

# Logs en temps réel
docker-compose logs -f --tail=50
```

### Métriques Spark

- **Master UI**: http://localhost:8080
  - Nombre de workers actifs
  - Applications en cours
  - Ressources disponibles

- **Worker UI**: http://localhost:8081 ou 8082
  - Executors actifs
  - Mémoire utilisée
  - Tâches en cours

### Métriques HDFS

- **NameNode UI**: http://localhost:9870
  - Espace disque utilisé
  - Nombre de DataNodes actifs
  - Nombre de fichiers

## 🎓 Prochaines Étapes

1. **Tester avec vos propres fichiers**
   - Uploader vos codes sources
   - Ajuster les paramètres (k, window) dans `winnowing.py`
   - Modifier le seuil de détection dans `similarity.py`

2. **Optimiser les performances**
   - Augmenter la mémoire des workers dans `docker-compose.yml`
   - Ajuster le parallélisme dans `spark-defaults.conf`
   - Activer Kryo serialization pour de meilleures performances

3. **Ajouter des fonctionnalités**
   - Support de nouveaux langages (Ruby, Go, etc.)
   - Rapports HTML détaillés
   - API REST pour intégration externe
   - Détection de patterns spécifiques

## 💡 Astuces

- 💾 Les données HDFS sont persistées dans des volumes Docker
- 🔄 Les logs Spark sont dans `/tmp/spark-events`
- 📊 Utilisez Spark UI pour débugger les jobs lents
- 🐛 Activez le niveau DEBUG dans `spark-defaults.conf` si nécessaire

## 📚 Documentation Complète

Consultez le [README.md](README.md) pour plus de détails sur:
- Architecture détaillée
- Algorithmes utilisés
- Configuration avancée
- API et extensibilité
