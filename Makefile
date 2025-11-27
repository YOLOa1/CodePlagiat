# ============================================
# Makefile - Commandes Rapides
# ============================================
# Utilisation: make <commande>
# Exemple: make start
# ============================================

.PHONY: help build start stop restart logs clean status test upload-examples run-job

# Par défaut, afficher l'aide
help:
	@echo "================================================"
	@echo "🔍 Système de Détection de Plagiat - Commandes"
	@echo "================================================"
	@echo ""
	@echo "📦 Gestion du Cluster:"
	@echo "  make build          - Build les images Docker"
	@echo "  make start          - Démarrer le cluster"
	@echo "  make stop           - Arrêter le cluster"
	@echo "  make restart        - Redémarrer le cluster"
	@echo "  make clean          - Tout supprimer (images + volumes)"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  make status         - Voir l'état des conteneurs"
	@echo "  make logs           - Voir les logs (tous les services)"
	@echo "  make logs-master    - Logs du Spark Master"
	@echo "  make logs-worker1   - Logs du Worker 1"
	@echo "  make logs-client    - Logs du Client"
	@echo ""
	@echo "🧪 Tests:"
	@echo "  make test           - Test de connexion Spark"
	@echo "  make upload-examples - Upload les exemples vers HDFS"
	@echo "  make run-job        - Lancer une analyse de plagiat"
	@echo ""
	@echo "🌐 URLs:"
	@echo "  Streamlit:    http://localhost:8501"
	@echo "  Spark Master: http://localhost:8080"
	@echo "  HDFS:         http://localhost:9870"
	@echo ""

# Build des images Docker
build:
	@echo "🔨 Build des images Docker..."
	docker-compose build

# Démarrer le cluster
start:
	@echo "🚀 Démarrage du cluster..."
	docker-compose up -d
	@echo "✅ Cluster démarré!"
	@echo ""
	@echo "🌐 Accéder aux interfaces:"
	@echo "  - Streamlit:    http://localhost:8501"
	@echo "  - Spark Master: http://localhost:8080"
	@echo "  - HDFS:         http://localhost:9870"

# Arrêter le cluster
stop:
	@echo "🛑 Arrêt du cluster..."
	docker-compose down
	@echo "✅ Cluster arrêté!"

# Redémarrer le cluster
restart: stop start

# Tout nettoyer (conteneurs + volumes + images)
clean:
	@echo "🧹 Nettoyage complet..."
	docker-compose down -v
	docker-compose rm -f
	@echo "✅ Nettoyage terminé!"

# Supprimer tout (y compris les images)
clean-all: clean
	@echo "🗑️  Suppression des images..."
	docker rmi -f $$(docker images 'codeplagiat*' -q) 2>/dev/null || true
	@echo "✅ Images supprimées!"

# Voir l'état des conteneurs
status:
	@echo "📊 État des conteneurs:"
	@docker-compose ps

# Voir tous les logs
logs:
	docker-compose logs -f --tail=100

# Logs du Master
logs-master:
	docker-compose logs -f spark-master

# Logs du Worker 1
logs-worker1:
	docker-compose logs -f spark-worker-1

# Logs du Worker 2
logs-worker2:
	docker-compose logs -f spark-worker-2

# Logs du Client
logs-client:
	docker-compose logs -f app-client

# Test de connexion Spark
test:
	@echo "🧪 Test de connexion Spark..."
	docker exec spark-master pyspark --version
	@echo "✅ Test réussi!"

# Upload des exemples vers HDFS
upload-examples:
	@echo "📤 Upload des exemples vers HDFS..."
	docker exec spark-master hdfs dfs -mkdir -p /app/input
	docker exec spark-master hdfs dfs -put -f /app/data/input/*.py /app/input/
	@echo "✅ Exemples uploadés!"
	@echo ""
	@echo "📋 Fichiers dans HDFS:"
	docker exec spark-master hdfs dfs -ls /app/input

# Lancer un job d'analyse
run-job:
	@echo "🔍 Lancement du job d'analyse..."
	docker exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		/app/src/spark_jobs/detect_plagiarism.py \
		--input hdfs://spark-master:9000/app/input \
		--output hdfs://spark-master:9000/app/output
	@echo "✅ Job terminé!"

# Shell interactif dans le Master
shell-master:
	@echo "🐚 Shell dans le Spark Master..."
	docker exec -it spark-master bash

# Shell interactif dans le Worker 1
shell-worker1:
	@echo "🐚 Shell dans le Worker 1..."
	docker exec -it spark-worker-1 bash

# Shell PySpark interactif
pyspark:
	@echo "🐍 Lancement de PySpark..."
	docker exec -it spark-master pyspark --master spark://spark-master:7077

# Lister les fichiers HDFS
hdfs-ls:
	@echo "📁 Contenu de HDFS:"
	docker exec spark-master hdfs dfs -ls -R /app

# Vérifier la santé du système
health:
	@echo "💚 Vérification de la santé du système..."
	@echo ""
	@echo "🐳 Conteneurs Docker:"
	@docker-compose ps
	@echo ""
	@echo "⚡ Spark Workers:"
	@docker exec spark-master curl -s http://localhost:8080/json/ | grep -o '"aliveworkers":[0-9]*' || echo "N/A"
	@echo ""
	@echo "📁 HDFS:"
	@docker exec spark-master hdfs dfsadmin -report | grep -E "Live datanodes|Configured Capacity" || echo "N/A"

# Ouvrir les URLs dans le navigateur (Windows)
open-urls:
	@echo "🌐 Ouverture des interfaces..."
	start http://localhost:8501
	start http://localhost:8080
	start http://localhost:9870

# Installation rapide (première utilisation)
install: build start upload-examples
	@echo ""
	@echo "================================================"
	@echo "✅ Installation terminée avec succès!"
	@echo "================================================"
	@echo ""
	@echo "🎉 Le système est prêt à l'emploi!"
	@echo ""
	@echo "🌐 Accéder à l'application:"
	@echo "   http://localhost:8501"
	@echo ""
	@echo "📚 Voir le guide de démarrage:"
	@echo "   cat QUICKSTART.md"
	@echo ""
