# 🔍 Système de Détection de Plagiat Distribué

## 📋 Vue d'ensemble
Système de détection de plagiat de code source utilisant Apache Spark pour le traitement distribué et HDFS pour le stockage. Analyse des fichiers Python, C++, et Java via AST et algorithme Winnowing.

## 🏗️ Architecture

```
┌─────────────────┐
│   App Client    │ (Streamlit - Port 8501)
│   (Streamlit)   │
└────────┬────────┘
         │
    ┌────▼──────────────────┐
    │   Spark Master        │ (Port 8080, 7077)
    │   + HDFS NameNode     │
    └────┬──────────────────┘
         │
    ┌────┴─────────┬────────────┐
    │              │            │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│Worker1│    │Worker2│    │Worker3│
└───────┘    └───────┘    └───────┘
```

## 📁 Structure du Projet

```
CodePlagiat/
├── docker/
│   ├── Dockerfile.base        # Image de base avec Spark/Hadoop/Python
│   ├── Dockerfile.client      # Image pour l'interface Streamlit
│   └── entrypoint.sh          # Script de démarrage conditionnel
├── configs/
│   ├── spark-defaults.conf    # Configuration Spark
│   └── hdfs-site.xml          # Configuration HDFS
├── src/
│   ├── spark_jobs/
│   │   ├── detect_plagiarism.py   # Job PySpark principal
│   │   ├── ast_extractor.py       # Extraction AST
│   │   ├── winnowing.py           # Algorithme Winnowing
│   │   └── similarity.py          # Calcul de similarité
│   ├── client/
│   │   └── app.py                 # Interface Streamlit
│   └── utils/
│       ├── hdfs_utils.py          # Utilitaires HDFS
│       └── spark_utils.py         # Utilitaires Spark
├── data/
│   ├── input/                 # Codes sources à analyser
│   ├── output/                # Résultats
│   └── logs/                  # Logs système
├── docker-compose.yml
└── README.md
```

## 🚀 Démarrage Rapide

### 1. Build des images
```bash
docker-compose build
```

### 2. Démarrage du cluster
```bash
docker-compose up -d
```

### 3. Vérification
- Spark Master UI: http://localhost:8080
- Streamlit App: http://localhost:8501
- HDFS NameNode: http://localhost:9870

### 4. Soumission d'un job
```bash
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /app/src/spark_jobs/detect_plagiarism.py
```

## 📊 Algorithme de Détection

1. **Parsing AST** : Extraction de la structure syntaxique
2. **Winnowing** : Génération d'empreintes digitales (k-grams)
3. **Comparaison** : Calcul de similarité Jaccard
4. **Rapport** : Génération des résultats et visualisation

## 🔧 Technologies

- **Apache Spark 3.3.0** : Traitement distribué
- **Hadoop 3.3.1** : HDFS pour stockage
- **Python 3.9** : Langage principal
- **Streamlit** : Interface utilisateur
- **Tree-sitter** : Parsing AST multi-langage
- **Docker** : Conteneurisation

## 📝 Configuration

### Variables d'environnement
- `SPARK_MASTER_HOST` : Hôte du master Spark
- `SPARK_WORKER_CORES` : Nombre de cœurs par worker
- `SPARK_WORKER_MEMORY` : Mémoire allouée par worker

## 🧪 Tests

```bash
# Test de connexion Spark
docker exec spark-master pyspark --version

# Test HDFS
docker exec spark-master hdfs dfs -ls /
```

## 📖 Documentation

- [Spark Documentation](https://spark.apache.org/docs/latest/)
- [Winnowing Algorithm](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf)

## 👥 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails
