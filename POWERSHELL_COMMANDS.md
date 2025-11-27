# ⚡ Commandes PowerShell - CodePlagiat

## 🚀 Démarrage Rapide

### Build et Démarrage
```powershell
# Build des images Docker
docker-compose build

# Démarrer le cluster en arrière-plan
docker-compose up -d

# Voir les logs en temps réel
docker-compose logs -f
```

## 📊 Monitoring

### État du Cluster
```powershell
# Voir tous les conteneurs
docker-compose ps

# Statistiques en temps réel
docker stats

# Santé des conteneurs
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Logs
```powershell
# Logs du Master
docker-compose logs -f spark-master

# Logs des Workers
docker-compose logs -f spark-worker-1 spark-worker-2

# Logs du Client
docker-compose logs -f app-client

# Tous les logs (dernières 100 lignes)
docker-compose logs --tail=100

# Logs avec timestamps
docker-compose logs -f -t
```

## 🔧 Gestion des Conteneurs

### Démarrage/Arrêt
```powershell
# Arrêter le cluster
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v

# Redémarrer un service spécifique
docker-compose restart spark-master

# Redémarrer tous les services
docker-compose restart

# Pause/Unpause
docker-compose pause
docker-compose unpause
```

### Reconstruction
```powershell
# Rebuild sans cache
docker-compose build --no-cache

# Rebuild un service spécifique
docker-compose build spark-master

# Rebuild et redémarrer
docker-compose up -d --build
```

## 📁 Interaction avec HDFS

### Commandes de Base
```powershell
# Lister le contenu de HDFS
docker exec spark-master hdfs dfs -ls /

# Lister récursivement
docker exec spark-master hdfs dfs -ls -R /app

# Créer un répertoire
docker exec spark-master hdfs dfs -mkdir -p /app/test

# Supprimer un fichier
docker exec spark-master hdfs dfs -rm /app/input/example.py

# Supprimer un répertoire (récursif)
docker exec spark-master hdfs dfs -rm -r /app/output
```

### Upload/Download
```powershell
# Upload un fichier vers HDFS
docker exec spark-master hdfs dfs -put /app/data/input/example1.py /app/input/

# Upload avec force (écrase si existe)
docker exec spark-master hdfs dfs -put -f /app/data/input/example1.py /app/input/

# Download depuis HDFS
docker exec spark-master hdfs dfs -get /app/output/results.csv /tmp/

# Copier dans HDFS
docker exec spark-master hdfs dfs -cp /app/input/example1.py /app/backup/
```

### Visualisation
```powershell
# Afficher le contenu d'un fichier
docker exec spark-master hdfs dfs -cat /app/input/example1.py

# Afficher les premières lignes
docker exec spark-master hdfs dfs -cat /app/output/results.csv | Select-Object -First 10

# Compter les lignes
docker exec spark-master hdfs dfs -cat /app/output/results.csv | Measure-Object -Line
```

### Informations
```powershell
# Espace disque HDFS
docker exec spark-master hdfs dfs -df -h

# Utilisation par répertoire
docker exec spark-master hdfs dfs -du -h /app

# Rapport HDFS complet
docker exec spark-master hdfs dfsadmin -report

# Statut des DataNodes
docker exec spark-master hdfs dfsadmin -printTopology
```

## ⚡ Jobs Spark

### Soumission de Jobs
```powershell
# Job de base
docker exec spark-master spark-submit `
  --master spark://spark-master:7077 `
  /app/src/spark_jobs/detect_plagiarism.py

# Avec arguments
docker exec spark-master spark-submit `
  --master spark://spark-master:7077 `
  /app/src/spark_jobs/detect_plagiarism.py `
  --input hdfs://spark-master:9000/app/input `
  --output hdfs://spark-master:9000/app/output

# Avec configuration personnalisée
docker exec spark-master spark-submit `
  --master spark://spark-master:7077 `
  --executor-memory 2g `
  --executor-cores 2 `
  --conf spark.default.parallelism=4 `
  /app/src/spark_jobs/detect_plagiarism.py
```

### Shell PySpark
```powershell
# Lancer PySpark interactif
docker exec -it spark-master pyspark --master spark://spark-master:7077

# Avec configuration
docker exec -it spark-master pyspark `
  --master spark://spark-master:7077 `
  --executor-memory 2g `
  --executor-cores 2
```

### Monitoring Jobs
```powershell
# Applications actives via API
docker exec spark-master curl -s http://localhost:8080/json/ | ConvertFrom-Json

# Tuer toutes les applications
docker exec spark-master $SPARK_HOME/sbin/stop-all.sh
docker exec spark-master $SPARK_HOME/sbin/start-all.sh
```

## 🐚 Shell Interactif

### Bash dans les Conteneurs
```powershell
# Shell dans le Master
docker exec -it spark-master bash

# Shell dans le Worker 1
docker exec -it spark-worker-1 bash

# Shell dans le Client
docker exec -it app-client bash
```

### Exécution de Commandes
```powershell
# Exécuter une commande simple
docker exec spark-master ls -la /app

# Exécuter un script Python
docker exec spark-master python3 /app/src/spark_jobs/ast_extractor.py

# Vérifier la version de Spark
docker exec spark-master spark-submit --version

# Tester la connectivité réseau
docker exec spark-master nc -zv spark-master 7077
```

## 🔍 Debugging

### Vérification de l'État
```powershell
# Ping entre conteneurs
docker exec spark-worker-1 ping -c 3 spark-master

# Test des ports
docker exec spark-master netstat -tulpn | Select-String "7077|8080|9000"

# Processus en cours
docker exec spark-master ps aux | Select-String "spark|java"

# Variables d'environnement
docker exec spark-master env | Select-String "SPARK|HADOOP"
```

### Logs Détaillés
```powershell
# Logs Spark (niveau DEBUG)
docker exec spark-master cat $SPARK_HOME/conf/log4j.properties

# Logs HDFS
docker exec spark-master cat $HADOOP_HOME/logs/hadoop-root-namenode-spark-master.log

# Derniers événements Spark
docker exec spark-master ls -lt /tmp/spark-events | Select-Object -First 5
```

### Nettoyage
```powershell
# Nettoyer les logs Spark
docker exec spark-master rm -rf /tmp/spark-events/*

# Nettoyer les données temporaires
docker exec spark-master rm -rf /tmp/hadoop/* /tmp/spark-*

# Reformater le NameNode (ATTENTION: Perte de données)
docker exec spark-master hdfs namenode -format -force
```

## 📦 Gestion des Volumes

### Inspection
```powershell
# Lister les volumes
docker volume ls

# Inspecter un volume
docker volume inspect codeplagiat_spark-master-data

# Espace utilisé
docker system df -v
```

### Nettoyage
```powershell
# Supprimer les volumes non utilisés
docker volume prune

# Supprimer tous les volumes du projet
docker-compose down -v

# Supprimer un volume spécifique
docker volume rm codeplagiat_spark-logs
```

## 🌐 Réseau

### Inspection
```powershell
# Lister les réseaux
docker network ls

# Inspecter le réseau du projet
docker network inspect codeplagiat_spark-network

# Voir les conteneurs connectés
docker network inspect codeplagiat_spark-network --format '{{json .Containers}}' | ConvertFrom-Json
```

### Test de Connectivité
```powershell
# DNS lookup depuis un conteneur
docker exec spark-worker-1 nslookup spark-master

# Tracer la route
docker exec spark-worker-1 traceroute spark-master

# Test HTTP
docker exec spark-master curl -I http://localhost:8080
```

## 🧪 Tests Rapides

### Test HDFS
```powershell
# Créer un fichier test
"Hello World" | docker exec -i spark-master hdfs dfs -put - /test.txt

# Lire le fichier
docker exec spark-master hdfs dfs -cat /test.txt

# Supprimer le fichier
docker exec spark-master hdfs dfs -rm /test.txt
```

### Test Spark
```powershell
# Test simple avec PySpark
docker exec spark-master python3 -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.master('spark://spark-master:7077').appName('Test').getOrCreate(); print('Spark OK'); spark.stop()"
```

### Test Complet
```powershell
# 1. Upload des exemples
docker exec spark-master hdfs dfs -put -f /app/data/input/*.py /app/input/

# 2. Lancer l'analyse
docker exec spark-master spark-submit `
  --master spark://spark-master:7077 `
  /app/src/spark_jobs/detect_plagiarism.py

# 3. Voir les résultats
docker exec spark-master hdfs dfs -ls /app/output
```

## 🔄 Workflow Complet

### Setup Initial
```powershell
# 1. Build
docker-compose build

# 2. Démarrer
docker-compose up -d

# 3. Attendre que tout soit prêt (30 secondes)
Start-Sleep -Seconds 30

# 4. Vérifier l'état
docker-compose ps

# 5. Upload des exemples
docker exec spark-master hdfs dfs -mkdir -p /app/input
docker exec spark-master hdfs dfs -put -f /app/data/input/*.py /app/input/

# 6. Ouvrir l'interface
Start-Process "http://localhost:8501"
```

### Nettoyage Complet
```powershell
# Tout arrêter et supprimer
docker-compose down -v

# Supprimer les images
docker rmi $(docker images 'codeplagiat*' -q)

# Nettoyer le système Docker
docker system prune -a --volumes
```

## 📊 Monitoring Avancé

### Ressources en Temps Réel
```powershell
# CPU et Mémoire
while ($true) {
    Clear-Host
    docker stats --no-stream
    Start-Sleep -Seconds 2
}
```

### Logs Centralisés
```powershell
# Suivre tous les logs avec couleurs
docker-compose logs -f --tail=50 | ForEach-Object {
    if ($_ -match "ERROR") { Write-Host $_ -ForegroundColor Red }
    elseif ($_ -match "WARN") { Write-Host $_ -ForegroundColor Yellow }
    elseif ($_ -match "INFO") { Write-Host $_ -ForegroundColor Green }
    else { Write-Host $_ }
}
```

## 🛠️ Maintenance

### Backup HDFS
```powershell
# Créer un backup
$date = Get-Date -Format "yyyyMMdd_HHmmss"
docker exec spark-master hdfs dfs -get /app "D:\backups\hdfs_$date"
```

### Restauration
```powershell
# Restaurer depuis un backup
docker exec spark-master hdfs dfs -put -f "D:\backups\hdfs_20231125_120000/*" /app/
```

### Mise à Jour
```powershell
# Pull des nouvelles images
docker-compose pull

# Rebuild et redémarrer
docker-compose up -d --build
```

## 💡 Astuces PowerShell

### Alias Utiles
```powershell
# Ajouter au profil PowerShell ($PROFILE)
function dc { docker-compose $args }
function dex { docker exec $args }
function dlogs { docker-compose logs -f --tail=50 }
function dstats { docker stats --no-stream }

# Utilisation:
# dc up -d
# dex spark-master hdfs dfs -ls /
```

### Fonctions Personnalisées
```powershell
# Fonction pour vérifier la santé
function Check-ClusterHealth {
    Write-Host "🔍 Vérification de la santé du cluster..." -ForegroundColor Cyan
    
    $containers = docker-compose ps --services
    foreach ($container in $containers) {
        $status = docker inspect --format='{{.State.Health.Status}}' $container 2>$null
        if ($status -eq "healthy") {
            Write-Host "✅ $container : OK" -ForegroundColor Green
        } else {
            Write-Host "❌ $container : $status" -ForegroundColor Red
        }
    }
}

# Utilisation:
# Check-ClusterHealth
```

---

**💡 Conseil:** Sauvegardez ces commandes dans un fichier `commands.ps1` pour référence rapide !
