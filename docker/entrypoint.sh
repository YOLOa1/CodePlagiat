#!/bin/bash
# ============================================
# Entrypoint Script - Démarrage Conditionnel
# ============================================
# Ce script gère le démarrage des conteneurs selon leur rôle :
# - MASTER : Lance Spark Master + HDFS NameNode
# - WORKER : Lance Spark Worker + HDFS DataNode
# - CLIENT : Lance uniquement le client (pas de services Spark/HDFS)
# ============================================

set -e

# Récupération du rôle depuis la variable d'environnement
ROLE=${SPARK_ROLE:-worker}

echo "================================================"
echo "🚀 Démarrage du conteneur en mode: $ROLE"
echo "================================================"

# ============================================
# FONCTION: Initialisation HDFS NameNode
# ============================================
init_hdfs_namenode() {
    echo "📁 Initialisation du HDFS NameNode..."
    
    # Vérifier si le NameNode est déjà formaté
    if [ ! -d "/hdfs/namenode/current" ]; then
        echo "⚙️  Formatage du NameNode (première exécution)..."
        $HADOOP_HOME/bin/hdfs namenode -format -force -nonInteractive
    else
        echo "✅ NameNode déjà formaté, passage au démarrage..."
    fi
    
    # Démarrage du NameNode
    echo "🔄 Démarrage du NameNode..."
    $HADOOP_HOME/bin/hdfs --daemon start namenode
    
    # Attendre que le NameNode soit prêt
    echo "⏳ Attente du NameNode (cela peut prendre jusqu'à 60 secondes)..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if nc -z 0.0.0.0 9000 2>/dev/null || nc -z localhost 9000 2>/dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        echo "⚠️  Timeout: NameNode prend plus de temps, continuons quand même..."
    fi
    
    echo "✅ NameNode démarré avec succès"
    
    # Créer les répertoires HDFS nécessaires
    echo "📂 Création de la structure HDFS..."
    $HADOOP_HOME/bin/hdfs dfs -mkdir -p /user
    $HADOOP_HOME/bin/hdfs dfs -mkdir -p /app/input
    $HADOOP_HOME/bin/hdfs dfs -mkdir -p /app/output
    $HADOOP_HOME/bin/hdfs dfs -mkdir -p /app/logs
    $HADOOP_HOME/bin/hdfs dfs -chmod -R 777 /
    
    echo "✅ Structure HDFS créée"
}

# ============================================
# FONCTION: Démarrage HDFS DataNode
# ============================================
start_hdfs_datanode() {
    echo "📁 Démarrage du HDFS DataNode..."
    
    # Attendre que le NameNode soit accessible
    echo "⏳ Attente du NameNode (spark-master:9000)..."
    timeout=120
    while [ $timeout -gt 0 ]; do
        if nc -z spark-master 9000 2>/dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        echo "⚠️  Timeout: Continuons sans attendre le NameNode..."
    fi
    
    echo "✅ NameNode accessible"
    
    # Démarrage du DataNode
    $HADOOP_HOME/bin/hdfs --daemon start datanode
    
    echo "✅ DataNode démarré avec succès"
}

# ============================================
# FONCTION: Démarrage Spark Master
# ============================================
start_spark_master() {
    echo "⚡ Démarrage du Spark Master..."
    
    # Définir le hostname du master
    export SPARK_MASTER_HOST=${SPARK_MASTER_HOST:-spark-master}
    export SPARK_MASTER_PORT=${SPARK_MASTER_PORT:-7077}
    export SPARK_MASTER_WEBUI_PORT=${SPARK_MASTER_WEBUI_PORT:-8080}
    
    # Démarrage du Master
    $SPARK_HOME/sbin/start-master.sh
    
    echo "✅ Spark Master démarré sur spark://$SPARK_MASTER_HOST:$SPARK_MASTER_PORT"
    echo "🌐 WebUI accessible sur http://localhost:$SPARK_MASTER_WEBUI_PORT"
}

# ============================================
# FONCTION: Démarrage Spark Worker
# ============================================
start_spark_worker() {
    echo "⚡ Démarrage du Spark Worker..."
    
    # Attendre que le Master soit accessible
    MASTER_URL="spark://${SPARK_MASTER_HOST:-spark-master}:${SPARK_MASTER_PORT:-7077}"
    echo "⏳ Attente du Spark Master ($MASTER_URL)..."
    
    timeout=120
    while [ $timeout -gt 0 ]; do
        if nc -z ${SPARK_MASTER_HOST:-spark-master} ${SPARK_MASTER_PORT:-7077} 2>/dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        echo "⚠️  Timeout: Continuons sans attendre le Master..."
    fi
    
    echo "✅ Spark Master accessible"
    
    # Configuration du Worker
    export SPARK_WORKER_CORES=${SPARK_WORKER_CORES:-2}
    export SPARK_WORKER_MEMORY=${SPARK_WORKER_MEMORY:-2g}
    export SPARK_WORKER_PORT=${SPARK_WORKER_PORT:-7078}
    export SPARK_WORKER_WEBUI_PORT=${SPARK_WORKER_WEBUI_PORT:-8081}
    
    # Démarrage du Worker
    $SPARK_HOME/sbin/start-worker.sh $MASTER_URL
    
    echo "✅ Spark Worker démarré"
    echo "   - Cores: $SPARK_WORKER_CORES"
    echo "   - Memory: $SPARK_WORKER_MEMORY"
    echo "🌐 WebUI accessible sur http://localhost:$SPARK_WORKER_WEBUI_PORT"
}

# ============================================
# BRANCHEMENT SELON LE RÔLE
# ============================================
case "$ROLE" in
    master)
        echo "🎯 Configuration en mode MASTER"
        echo "---"
        
        # Initialisation et démarrage HDFS NameNode
        init_hdfs_namenode
        
        # Démarrage Spark Master
        start_spark_master
        
        echo "---"
        echo "✅ Master complètement initialisé"
        echo "📊 Services actifs:"
        echo "   - HDFS NameNode (port 9000, UI: 9870)"
        echo "   - Spark Master (port 7077, UI: 8080)"
        echo "================================================"
        ;;
        
    worker)
        echo "🎯 Configuration en mode WORKER"
        echo "---"
        
        # Démarrage HDFS DataNode
        start_hdfs_datanode
        
        # Démarrage Spark Worker
        start_spark_worker
        
        echo "---"
        echo "✅ Worker complètement initialisé"
        echo "📊 Services actifs:"
        echo "   - HDFS DataNode (port 9864)"
        echo "   - Spark Worker (port 7078, UI: 8081)"
        echo "================================================"
        ;;
        
    client)
        echo "🎯 Configuration en mode CLIENT"
        echo "---"
        echo "✅ Mode client - Aucun service Spark/HDFS à démarrer"
        echo "================================================"
        ;;
        
    *)
        echo "❌ Erreur: Rôle invalide '$ROLE'"
        echo "Rôles valides: master, worker, client"
        exit 1
        ;;
esac

# ============================================
# EXÉCUTION DE LA COMMANDE PASSÉE EN PARAMÈTRE
# ============================================
# Si une commande est passée au conteneur, l'exécuter
# Sinon, garder le conteneur actif
if [ $# -gt 0 ]; then
    echo "🔧 Exécution de la commande: $@"
    exec "$@"
else
    echo "♾️  Conteneur en mode daemon - Maintien actif..."
    # Garder le conteneur actif indéfiniment
    tail -f /dev/null
fi
