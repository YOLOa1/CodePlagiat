# 🚀 Guide d'utilisation sans interface Streamlit

Ce guide explique comment utiliser le système de détection de plagiat directement en ligne de commande, sans passer par l'interface web.

## 📋 Table des matières

- [Démarrage du cluster](#démarrage-du-cluster)
- [Gestion des fichiers HDFS](#gestion-des-fichiers-hdfs)
- [Lancement d'une analyse](#lancement-dune-analyse)
- [Consultation des résultats](#consultation-des-résultats)
- [Exemples d'utilisation](#exemples-dutilisation)
- [Commandes avancées](#commandes-avancées)

---

## 🎯 Démarrage du cluster

### Démarrer tous les services
```powershell
# Démarrer le cluster complet (Master + 2 Workers + Client)
docker-compose up -d

# Vérifier que tous les conteneurs sont "healthy"
docker ps

# Attendre ~60 secondes pour que tous les services soient prêts
```

### Arrêter le cluster
```powershell
# Arrêter tous les conteneurs
docker-compose down

# Arrêter ET supprimer les volumes (⚠️ perte de données HDFS)
docker-compose down -v
```

### Redémarrer un service spécifique
```powershell
# Redémarrer uniquement le Master
docker restart spark-master

# Redémarrer un Worker
docker restart spark-worker-1
```

---

## 📁 Gestion des fichiers HDFS

### Structure des répertoires HDFS
```
hdfs://spark-master:9000/
└── app/
    ├── input/          # Fichiers source à analyser
    ├── results/        # Résultats des analyses
    └── logs/           # Logs optionnels
```

### Créer la structure de répertoires
```powershell
# Créer les dossiers nécessaires
docker exec spark-master hdfs dfs -mkdir -p /app/input
docker exec spark-master hdfs dfs -mkdir -p /app/results
docker exec spark-master hdfs dfs -mkdir -p /app/logs
```

### Uploader des fichiers

#### Upload d'un seul fichier
```powershell
# Depuis le conteneur (fichiers déjà dans /app/data/input/)
docker exec spark-master hdfs dfs -put /app/data/input/mon_fichier.py /app/input/

# Avec un fichier de votre machine Windows
docker cp D:\MesFichiers\code.py spark-master:/tmp/code.py
docker exec spark-master hdfs dfs -put /tmp/code.py /app/input/
```

#### Upload de plusieurs fichiers
```powershell
# Uploader tous les fichiers .py d'un dossier
docker exec spark-master sh -c "cd /app/data/input && for f in *.py; do hdfs dfs -put \$f /app/input/ 2>/dev/null || true; done"

# Avec un dossier de votre machine
docker cp D:\MesFichiers\*.py spark-master:/tmp/
docker exec spark-master sh -c "cd /tmp && for f in *.py; do hdfs dfs -put \$f /app/input/; done"
```

### Lister les fichiers
```powershell
# Lister le contenu de /app/input/
docker exec spark-master hdfs dfs -ls /app/input/

# Liste récursive avec tailles
docker exec spark-master hdfs dfs -ls -R -h /app/

# Compter les fichiers
docker exec spark-master hdfs dfs -count /app/input/
```

### Consulter le contenu d'un fichier
```powershell
# Afficher tout le contenu
docker exec spark-master hdfs dfs -cat /app/input/mon_fichier.py

# Afficher les 10 premières lignes
docker exec spark-master hdfs dfs -cat /app/input/mon_fichier.py | head -10

# Afficher les 10 dernières lignes
docker exec spark-master hdfs dfs -cat /app/input/mon_fichier.py | tail -10
```

### Télécharger des fichiers depuis HDFS
```powershell
# Télécharger vers le conteneur
docker exec spark-master hdfs dfs -get /app/input/mon_fichier.py /tmp/

# Puis copier vers Windows
docker cp spark-master:/tmp/mon_fichier.py D:\MesFichiers\
```

### Supprimer des fichiers
```powershell
# Supprimer un fichier
docker exec spark-master hdfs dfs -rm /app/input/vieux_fichier.py

# Supprimer tous les fichiers d'un dossier
docker exec spark-master hdfs dfs -rm /app/input/*

# Supprimer un dossier et son contenu
docker exec spark-master hdfs dfs -rm -r /app/old_results/

# Vider complètement le dossier input
docker exec spark-master hdfs dfs -rm -r /app/input/*
```

### Renommer ou déplacer
```powershell
# Renommer un fichier
docker exec spark-master hdfs dfs -mv /app/input/ancien_nom.py /app/input/nouveau_nom.py

# Déplacer vers un autre dossier
docker exec spark-master hdfs dfs -mv /app/input/fichier.py /app/archive/
```

---

## 🔍 Lancement d'une analyse

### Commande de base (tous contre tous)
```powershell
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/run_$(Get-Date -Format "yyyyMMdd_HHmmss")
```

### Comparaison ciblée (un fichier vs tous les autres)
```powershell
# Comparer un fichier spécifique contre toute la base de données
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/target_$(Get-Date -Format "yyyyMMdd_HHmmss") \
  --target student1.py

# Avec le chemin HDFS complet
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/suspect_check \
  --target hdfs://spark-master:9000/app/input/plagiat1.py
```

### Avec configuration personnalisée
```powershell
# Analyse avec plus de mémoire et de cœurs
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --driver-memory 2g \
  --executor-memory 2g \
  --executor-cores 2 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/analyse_$(Get-Date -Format "yyyyMMdd_HHmmss")
```

### Sauvegarder les logs
```powershell
# Rediriger la sortie vers un fichier
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/run_latest \
  > analyse_log.txt 2>&1
```

---

## 📊 Consultation des résultats

### Lister les dossiers de résultats
```powershell
# Voir tous les runs
docker exec spark-master hdfs dfs -ls /app/results/

# Détails avec dates
docker exec spark-master hdfs dfs -ls -h /app/results/
```

### Afficher les résultats

#### Résultats du dernier run
```powershell
# Afficher le CSV complet
docker exec spark-master hdfs dfs -cat /app/results/run_latest/*.csv

# Afficher uniquement les en-têtes et les 5 premières lignes
docker exec spark-master hdfs dfs -cat /app/results/run_latest/*.csv | head -6
```

#### Filtrer les résultats
```powershell
# Uniquement les similarités > 70% (plagiat)
docker exec spark-master hdfs dfs -cat /app/results/run_latest/*.csv | awk -F',' '$3 > 0.7 {print}'

# Trier par score de similarité décroissant
docker exec spark-master hdfs dfs -cat /app/results/run_latest/*.csv | tail -n +2 | sort -t',' -k3 -rn

# Compter le nombre de plagiats détectés (> 70%)
docker exec spark-master hdfs dfs -cat /app/results/run_latest/*.csv | awk -F',' '$3 > 0.7' | wc -l
```

### Télécharger les résultats
```powershell
# Télécharger le CSV vers Windows
docker exec spark-master hdfs dfs -cat /app/results/run_latest/*.csv > resultats.csv

# Ouvrir avec Excel
Start-Process resultats.csv
```

### Analyser avec Python
```powershell
# Créer un script Python pour analyser
docker exec spark-master python3 -c "
import pandas as pd
import subprocess

# Lire depuis HDFS
result = subprocess.run(['hdfs', 'dfs', '-cat', '/app/results/run_latest/*.csv'], 
                       capture_output=True, text=True)
                       
# Charger dans pandas
from io import StringIO
df = pd.read_csv(StringIO(result.stdout))

# Statistiques
print('Nombre total de comparaisons:', len(df))
print('Plagiats détectés (>70%):', len(df[df['similarity_score'] > 0.7]))
print('Similarité moyenne:', df['similarity_score'].mean())
print('\nTop 5 des similarités:')
print(df.nlargest(5, 'similarity_score'))
"
```

---

## 🎯 Exemples d'utilisation

### Exemple 1: Analyser un devoir d'étudiants

```powershell
# 1. Nettoyer l'ancien contenu
docker exec spark-master hdfs dfs -rm -r /app/input/*

# 2. Uploader les devoirs (depuis votre dossier local)
$devoirs = Get-ChildItem "D:\Devoirs\TP1\*.py"
foreach ($devoir in $devoirs) {
    docker cp $devoir.FullName "spark-master:/tmp/$($devoir.Name)"
    docker exec spark-master hdfs dfs -put "/tmp/$($devoir.Name)" /app/input/
}

# 3. Vérifier l'upload
docker exec spark-master hdfs dfs -ls /app/input/

# 4. Lancer l'analyse (tous contre tous)
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/tp1_$(Get-Date -Format "yyyyMMdd")

# 5. Voir les plagiats détectés
Write-Host "`n=== PLAGIATS DÉTECTÉS ===" -ForegroundColor Red
docker exec spark-master hdfs dfs -cat /app/results/tp1_*/part-*.csv | Select-String -Pattern "0\.[7-9]|1\.0"
```

### Exemple 1bis: Vérifier un devoir suspect

```powershell
# Scénario: Un étudiant a rendu un devoir suspect, vérifier s'il a copié
$fichierSuspect = "etudiant_suspect.py"

# 1. S'assurer que tous les devoirs sont dans HDFS (incluant le suspect)
docker exec spark-master hdfs dfs -ls /app/input/

# 2. Comparer UNIQUEMENT ce fichier contre tous les autres
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/verification_suspect \
  --target $fichierSuspect

# 3. Voir immédiatement les résultats
Write-Host "`n=== VÉRIFICATION: $fichierSuspect ===" -ForegroundColor Yellow
docker exec spark-master hdfs dfs -cat /app/results/verification_suspect/part-*.csv

# 4. Filtrer uniquement les scores élevés
Write-Host "`n=== PLAGIATS POTENTIELS (>80%) ===" -ForegroundColor Red
docker exec spark-master hdfs dfs -cat /app/results/verification_suspect/part-*.csv | Select-String -Pattern "0\.[8-9]|1\.0"
```

### Exemple 2: Analyse comparative entre deux versions

```powershell
# Comparer version 2024 vs version 2025 d'un projet
docker exec spark-master hdfs dfs -rm -r /app/input/*

# Upload version 2024
docker exec spark-master sh -c "cd /app/data/input && for f in version2024_*.py; do hdfs dfs -put \$f /app/input/; done"

# Upload version 2025
docker exec spark-master sh -c "cd /app/data/input && for f in version2025_*.py; do hdfs dfs -put \$f /app/input/; done"

# Analyse
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/comparison_2024_vs_2025

# Filtrer uniquement les comparaisons entre versions différentes
docker exec spark-master hdfs dfs -cat /app/results/comparison_*/part-*.csv | Select-String "version2024.*version2025|version2025.*version2024"
```

### Exemple 3: Batch processing de plusieurs projets

```powershell
# Liste de projets à analyser
$projets = @("ProjetA", "ProjetB", "ProjetC")

foreach ($projet in $projets) {
    Write-Host "`n=== Analyse de $projet ===" -ForegroundColor Cyan
    
    # Nettoyer
    docker exec spark-master hdfs dfs -rm -r /app/input/*
    
    # Upload
    docker exec spark-master sh -c "cd /app/data/input/$projet && for f in *.py; do hdfs dfs -put \$f /app/input/; done"
    
    # Analyse
    docker exec spark-master spark-submit \
      --master spark://spark-master:7077 \
      --py-files /app/src/spark_jobs.zip \
      /app/src/spark_jobs/detect_plagiarism.py \
      --input hdfs://spark-master:9000/app/input \
      --output hdfs://spark-master:9000/app/results/${projet}_$(Get-Date -Format "yyyyMMdd")
    
    # Résumé
    $plagiats = docker exec spark-master hdfs dfs -cat "/app/results/${projet}_*/part-*.csv" | Select-String "0\.[7-9]|1\.0" | Measure-Object -Line
    Write-Host "Plagiats détectés: $($plagiats.Lines)" -ForegroundColor $(if ($plagiats.Lines -gt 0) { "Red" } else { "Green" })
}
```

### Exemple 4: Vérification d'un nouveau fichier contre une base existante

```powershell
# Scénario: Un nouveau devoir arrive, vérifier s'il est copié des anciens
# La base de données contient déjà 100 devoirs des années précédentes

# 1. Uploader UNIQUEMENT le nouveau fichier (sans effacer l'ancien contenu)
$nouveauDevoir = "D:\Nouveaux\etudiant_nouveau.py"
docker cp $nouveauDevoir "spark-master:/tmp/nouveau.py"
docker exec spark-master hdfs dfs -put /tmp/nouveau.py /app/input/

# 2. Vérifier combien de fichiers au total
docker exec spark-master hdfs dfs -count /app/input/

# 3. Comparer SEULEMENT ce nouveau fichier contre les 100 anciens
Write-Host "`n🔍 Vérification du nouveau devoir contre la base..." -ForegroundColor Yellow
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/nouveau_check_$(Get-Date -Format "yyyyMMdd_HHmmss") \
  --target nouveau.py

# 4. Rapport détaillé
Write-Host "`n📊 RAPPORT DE VÉRIFICATION:" -ForegroundColor Cyan
$resultats = docker exec spark-master hdfs dfs -cat /app/results/nouveau_check_*/part-*.csv
$totalComparaisons = ($resultats | Measure-Object -Line).Lines - 1  # -1 pour l'en-tête
$plagiats = $resultats | Select-String -Pattern "0\.[7-9]|1\.0" | Measure-Object -Line

Write-Host "  • Fichier analysé: nouveau.py" -ForegroundColor White
Write-Host "  • Comparaisons effectuées: $totalComparaisons" -ForegroundColor White
Write-Host "  • Plagiats détectés (>70%): $($plagiats.Lines)" -ForegroundColor $(if ($plagiats.Lines -gt 0) { "Red" } else { "Green" })

if ($plagiats.Lines -gt 0) {
    Write-Host "`n⚠️ ATTENTION: Plagiats détectés!" -ForegroundColor Red
    $resultats | Select-String -Pattern "0\.[7-9]|1\.0"
} else {
    Write-Host "`n✅ Aucun plagiat détecté - Devoir original" -ForegroundColor Green
}
```

### Exemple 5: Comparaison rapide d'un fichier reçu par email

```powershell
# Workflow rapide pour vérifier un fichier suspect reçu par email

# 1. Définir le fichier à vérifier
$fichierEmail = "D:\Downloads\code_suspect_from_email.py"
$nomFichier = Split-Path $fichierEmail -Leaf

# 2. Upload rapide (la base existe déjà dans HDFS)
Write-Host "📤 Upload du fichier suspect..." -ForegroundColor Yellow
docker cp $fichierEmail "spark-master:/tmp/suspect.py"
docker exec spark-master hdfs dfs -put -f /tmp/suspect.py /app/input/suspect.py

# 3. Lancer l'analyse ciblée (plus rapide que tous contre tous)
Write-Host "🔍 Analyse en cours..." -ForegroundColor Yellow
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --driver-memory 1g \
  --executor-memory 1g \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/email_check \
  --target suspect.py

# 4. Résultat immédiat
Write-Host "`n📋 RÉSULTATS:" -ForegroundColor Cyan
docker exec spark-master hdfs dfs -cat /app/results/email_check/part-*.csv | 
    ConvertFrom-Csv | 
    Where-Object { [float]$_.similarity_score -gt 0.7 } |
    Sort-Object { [float]$_.similarity_score } -Descending |
    Format-Table -AutoSize

# 5. Nettoyer le fichier temporaire
docker exec spark-master hdfs dfs -rm /app/input/suspect.py
Write-Host "`n✅ Vérification terminée" -ForegroundColor Green
```

---

## 🛠️ Commandes avancées

### Monitoring du cluster

```powershell
# Voir les applications Spark en cours
docker exec spark-master curl -s http://localhost:8080/json/ | ConvertFrom-Json | Select-Object -ExpandProperty activeapps

# Statistiques HDFS
docker exec spark-master hdfs dfsadmin -report

# Santé des DataNodes
docker exec spark-master hdfs dfsadmin -printTopology

# Logs du Master
docker logs spark-master --tail 50

# Logs d'un Worker
docker logs spark-worker-1 --tail 50
```

### Gestion de la mémoire

```powershell
# Voir l'utilisation mémoire des conteneurs
docker stats --no-stream

# Nettoyer le cache Spark
docker exec spark-master rm -rf /tmp/spark-*

# Nettoyer les anciens résultats (garde les 5 derniers)
docker exec spark-master hdfs dfs -ls /app/results/ | tail -n +6 | awk '{print $8}' | xargs -I {} hdfs dfs -rm -r {}
```

### Debugging

```powershell
# Exécuter un job avec plus de logs
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.executor.extraJavaOptions="-Dlog4j.configuration=file:///opt/spark/conf/log4j.properties" \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/debug_run

# Tester la connexion HDFS
docker exec spark-master hdfs dfs -test -e /app/input && echo "Dossier existe" || echo "Dossier n'existe pas"

# Vérifier la santé de Spark
docker exec spark-master curl -s http://localhost:8080/json/ | python3 -m json.tool

# Shell interactif Python avec PySpark
docker exec -it spark-master pyspark --master spark://spark-master:7077
```

### Export et sauvegarde

```powershell
# Exporter tous les résultats vers un dossier local
$date = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Path ".\exports\export_$date" -Force
docker exec spark-master hdfs dfs -get /app/results/* /tmp/export/
docker cp spark-master:/tmp/export/. ".\exports\export_$date\"

# Créer un backup HDFS
docker exec spark-master hdfs dfs -cp /app /app_backup_$(Get-Date -Format "yyyyMMdd")

# Archiver et compresser
docker exec spark-master tar -czf /tmp/hdfs_backup.tar.gz /hdfs/
docker cp spark-master:/tmp/hdfs_backup.tar.gz .\backups\
```

---

## 📚 Ressources supplémentaires

### Interfaces Web disponibles

- **Spark Master UI**: http://localhost:8080 - État du cluster, applications, workers
- **Spark Worker 1 UI**: http://localhost:8081 - Métriques du worker 1
- **Spark Worker 2 UI**: http://localhost:8082 - Métriques du worker 2
- **HDFS NameNode UI**: http://localhost:9870 - Parcourir HDFS, état des DataNodes

### Scripts PowerShell utiles

#### Script de monitoring continu
```powershell
# monitor.ps1
while ($true) {
    Clear-Host
    Write-Host "=== ÉTAT DU CLUSTER ===" -ForegroundColor Green
    docker ps --filter "name=spark" --format "table {{.Names}}\t{{.Status}}"
    
    Write-Host "`n=== FICHIERS HDFS ===" -ForegroundColor Cyan
    docker exec spark-master hdfs dfs -count /app/input /app/results
    
    Write-Host "`n=== APPLICATIONS SPARK ===" -ForegroundColor Yellow
    docker exec spark-master curl -s http://localhost:8080/json/ | ConvertFrom-Json | Select-Object -ExpandProperty activeapps | Format-Table
    
    Start-Sleep 5
}
```

#### Script d'analyse automatique
```powershell
# auto_analyze.ps1
param(
    [string]$InputFolder,
    [string]$OutputName = "batch_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
)

Write-Host "🚀 Démarrage de l'analyse automatique..." -ForegroundColor Green

# 1. Nettoyer HDFS
Write-Host "📁 Nettoyage HDFS..." -ForegroundColor Yellow
docker exec spark-master hdfs dfs -rm -r /app/input/* 2>$null

# 2. Upload des fichiers
Write-Host "📤 Upload des fichiers..." -ForegroundColor Yellow
$files = Get-ChildItem "$InputFolder\*.py"
foreach ($file in $files) {
    docker cp $file.FullName "spark-master:/tmp/$($file.Name)"
    docker exec spark-master hdfs dfs -put "/tmp/$($file.Name)" /app/input/
}

Write-Host "✅ $($files.Count) fichiers uploadés" -ForegroundColor Green

# 3. Lancement de l'analyse
Write-Host "🔍 Lancement de l'analyse..." -ForegroundColor Yellow
docker exec spark-master spark-submit `
  --master spark://spark-master:7077 `
  --py-files /app/src/spark_jobs.zip `
  /app/src/spark_jobs/detect_plagiarism.py `
  --input hdfs://spark-master:9000/app/input `
  --output hdfs://spark-master:9000/app/results/$OutputName

# 4. Affichage des résultats
Write-Host "`n📊 RÉSULTATS:" -ForegroundColor Cyan
docker exec spark-master hdfs dfs -cat "/app/results/$OutputName/part-*.csv"

Write-Host "`n✅ Analyse terminée! Résultats dans: /app/results/$OutputName" -ForegroundColor Green
```

---

## 🆘 Dépannage

### Le cluster ne démarre pas
```powershell
# Vérifier les logs
docker-compose logs

# Reconstruire les images
docker-compose build --no-cache

# Reset complet
docker-compose down -v
docker-compose up -d
```

### Erreur "No space left on device"
```powershell
# Nettoyer les anciens résultats
docker exec spark-master hdfs dfs -rm -r /app/results/run_* | Select-Object -First 10

# Nettoyer Docker
docker system prune -a --volumes
```

### Job Spark échoue
```powershell
# Vérifier que l'archive des modules existe
docker exec spark-master ls -lh /app/src/spark_jobs.zip

# Recréer l'archive si nécessaire
docker exec spark-master python3 -c "import shutil; shutil.make_archive('/app/src/spark_jobs', 'zip', '/app/src', 'spark_jobs')"

# Tester avec moins de mémoire
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --driver-memory 512m \
  --executor-memory 512m \
  --py-files /app/src/spark_jobs.zip \
  /app/src/spark_jobs/detect_plagiarism.py \
  --input hdfs://spark-master:9000/app/input \
  --output hdfs://spark-master:9000/app/results/test
```

---

**💡 Astuce**: Pour une utilisation interactive et plus conviviale, utilisez l'interface Streamlit sur http://localhost:8501 !
