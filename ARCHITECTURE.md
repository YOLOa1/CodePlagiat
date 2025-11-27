# 🏗️ Architecture Détaillée - Système de Détection de Plagiat

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Composants Système](#composants-système)
3. [Pipeline de Traitement](#pipeline-de-traitement)
4. [Algorithmes](#algorithmes)
5. [Configuration](#configuration)
6. [Performance et Scalabilité](#performance-et-scalabilité)
7. [Sécurité](#sécurité)

---

## 🎯 Vue d'ensemble

### Architecture Globale

```
┌──────────────────────────────────────────────────────────┐
│                    COUCHE CLIENT                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │        Application Streamlit (Port 8501)           │  │
│  │  - Upload de fichiers                              │  │
│  │  - Soumission de jobs                              │  │
│  │  - Visualisation des résultats                     │  │
│  └───────────────────────┬────────────────────────────┘  │
└────────────────────────────┼─────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────┐
│                    COUCHE SPARK                          │
│  ┌─────────────────────────▼──────────────────────────┐  │
│  │       Spark Master (spark-master:7077)             │  │
│  │  - Orchestration des jobs                          │  │
│  │  - Allocation des ressources                       │  │
│  │  - Monitoring (UI: 8080)                           │  │
│  └────────┬─────────────────────────┬─────────────────┘  │
│           │                         │                    │
│  ┌────────▼─────────┐      ┌───────▼─────────┐          │
│  │  Worker 1:8081   │      │  Worker 2:8082  │          │
│  │  - 2 cores       │      │  - 2 cores      │          │
│  │  - 2GB RAM       │      │  - 2GB RAM      │          │
│  └──────────────────┘      └─────────────────┘          │
└────────────────────────────┼─────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────┐
│                    COUCHE STOCKAGE                       │
│  ┌─────────────────────────▼──────────────────────────┐  │
│  │          HDFS (hdfs://spark-master:9000)           │  │
│  │                                                     │  │
│  │  ┌──────────────┐    ┌──────────────────────────┐  │  │
│  │  │  NameNode    │    │     DataNodes (x2)       │  │  │
│  │  │  (Metadata)  │◄───┤  - Stockage distribué    │  │  │
│  │  │  UI: 9870    │    │  - Réplication: 1        │  │  │
│  │  └──────────────┘    └──────────────────────────┘  │  │
│  │                                                     │  │
│  │  Structure:                                         │  │
│  │  /app/input/  - Fichiers sources                   │  │
│  │  /app/output/ - Résultats d'analyse                │  │
│  │  /app/logs/   - Logs système                       │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 🔧 Composants Système

### 1. Spark Master

**Rôle:** Orchestrateur central du cluster Spark

**Responsabilités:**
- Recevoir les jobs soumis
- Allouer les ressources aux applications
- Coordonner les Workers
- Fournir l'interface de monitoring

**Spécifications:**
- **CPU:** Variable (partagé avec NameNode)
- **RAM:** 1GB pour le Driver
- **Ports:**
  - 7077: Communication Spark
  - 8080: WebUI
  - 9000: HDFS NameNode RPC
  - 9870: HDFS NameNode WebUI

**Configuration clé:**
```properties
spark.master=spark://spark-master:7077
spark.driver.memory=1g
spark.executor.instances=2
```

### 2. Spark Workers

**Rôle:** Nœuds de calcul pour exécuter les tâches

**Configuration par Worker:**
- **Cores:** 2
- **Memory:** 2GB
- **Executor Memory:** 2GB par executor
- **Ports:**
  - Worker 1: 8081 (WebUI), 7078 (Communication)
  - Worker 2: 8082 (WebUI), 7079 (Communication)

**Capacité totale du cluster:**
- **Total Cores:** 4
- **Total Memory:** 4GB
- **Parallélisme:** 4 tâches simultanées

### 3. HDFS

**Architecture:**

```
NameNode (Master)
├── Metadata Storage (/hdfs/namenode)
├── Namespace Management
└── Block Locations

DataNodes (2x)
├── Block Storage (/hdfs/datanode)
├── Heartbeat vers NameNode
└── Réplication: 1 copie
```

**Configuration:**
- **Block Size:** 128MB
- **Replication Factor:** 1 (dev) / 3 (prod)
- **WebHDFS:** Activé (API REST)

### 4. Client Streamlit

**Technologies:**
- **Framework:** Streamlit 1.28.1
- **Backend:** Python 3.9
- **Dépendances:**
  - PySpark (communication)
  - Plotly (visualisation)
  - Pandas (manipulation de données)

**Fonctionnalités:**
- Upload de fichiers vers HDFS
- Soumission de jobs Spark
- Visualisation des résultats
- Export des rapports

---

## 🔄 Pipeline de Traitement

### Étape 1: Ingestion des Données

```python
# Lecture depuis HDFS
files_rdd = sc.wholeTextFiles("hdfs://spark-master:9000/app/input")
# RDD[(filename, content)]

# Filtrage par extension
valid_files = files_rdd.filter(lambda x: x[0].endswith(('.py', '.cpp', '.java')))
```

**Optimisations:**
- Lecture parallèle distribuée
- Filtrage précoce pour réduire le volume
- Cache des données pour réutilisation

### Étape 2: Extraction AST

```python
def extract_ast(file_tuple):
    filename, content = file_tuple
    
    # 1. Détection du langage
    language = detect_language(filename)
    
    # 2. Parsing AST
    tokens = ast_extractor.extract_tokens(content, language)
    
    # 3. Normalisation
    normalized_tokens = normalize(tokens)
    
    return (filename, language, normalized_tokens)

features_rdd = valid_files.map(extract_ast)
```

**Techniques:**
- Tokenization native Python pour `.py`
- Regex-based parsing pour C++/Java (simplifié)
- Option: Tree-sitter pour parsing robuste

### Étape 3: Génération d'Empreintes (Winnowing)

```python
def generate_fingerprints(tokens):
    # 1. Créer les k-grams (k=5)
    kgrams = [tokens[i:i+5] for i in range(len(tokens)-4)]
    
    # 2. Hasher chaque k-gram
    hashes = [hash_kgram(kg) for kg in kgrams]
    
    # 3. Winnowing (window=4)
    fingerprints = []
    for i in range(len(hashes)-3):
        window = hashes[i:i+4]
        min_hash = min(window)
        fingerprints.append(min_hash)
    
    return fingerprints

fp_rdd = features_rdd.map(lambda x: (x[0], x[1], generate_fingerprints(x[2])))
```

**Paramètres Winnowing:**
- **k=5**: Séquence de 5 tokens
- **window=4**: Fenêtre glissante de 4 hashes
- **Garantie:** Détecte tout match de longueur ≥ k+window-1 = 8 tokens

### Étape 4: Comparaison par Paires

```python
# Cartésien pour toutes les paires
pairs = fp_rdd.cartesian(fp_rdd)

# Éviter les doublons et auto-comparaisons
pairs = pairs.filter(lambda p: p[0][0] < p[1][0])

def compare(pair):
    (file1, _, fp1), (file2, _, fp2) = pair
    
    # Similarité Jaccard
    intersection = len(set(fp1) & set(fp2))
    union = len(set(fp1) | set(fp2))
    similarity = intersection / union if union > 0 else 0
    
    return (file1, file2, similarity)

results = pairs.map(compare)
```

**Complexité:**
- **Paires:** O(n²) où n = nombre de fichiers
- **Comparaison:** O(m) où m = taille moyenne des sets
- **Total:** O(n² * m)

### Étape 5: Filtrage et Tri

```python
# Filtrer les similarités significatives
significant = results.filter(lambda x: x[2] > 0.1)

# Trier par score décroissant
sorted_results = significant.sortBy(lambda x: -x[2])

# Top 100 résultats
top_results = sorted_results.take(100)
```

### Étape 6: Sauvegarde

```python
# Convertir en DataFrame
df = spark.createDataFrame(sorted_results, ["file1", "file2", "similarity"])

# Ajouter métadonnées
df = df.withColumn("timestamp", current_timestamp())

# Sauvegarder en CSV
df.coalesce(1).write.csv(output_path, header=True, mode="overwrite")
```

---

## 🧮 Algorithmes

### Algorithme de Winnowing

**Papier de référence:**
> Schleimer, S., Wilkerson, D. S., & Aiken, A. (2003).  
> *Winnowing: Local Algorithms for Document Fingerprinting*  
> ACM SIGMOD Conference

**Principe:**

1. **K-gramming:**
   ```
   Input: [a, b, c, d, e, f]  (k=3)
   Output: [(a,b,c), (b,c,d), (c,d,e), (d,e,f)]
   ```

2. **Hashing:**
   ```
   (a,b,c) → H1 = 45
   (b,c,d) → H2 = 12
   (c,d,e) → H3 = 78
   (d,e,f) → H4 = 34
   ```

3. **Windowing (w=2):**
   ```
   Window 1: [H1=45, H2=12] → min=12 ✓
   Window 2: [H2=12, H3=78] → min=12 (déjà pris)
   Window 3: [H3=78, H4=34] → min=34 ✓
   
   Fingerprints: [12, 34]
   ```

**Garantie:**
- Si deux documents partagent une sous-séquence de longueur ≥ (k + w - 1), au moins une empreinte commune sera détectée.

**Trade-offs:**
- k petit → plus sensible, plus d'empreintes
- k grand → moins sensible, moins d'empreintes
- w petit → plus d'empreintes, détection fine
- w grand → moins d'empreintes, performances

### Similarité de Jaccard

**Formule:**
```
J(A, B) = |A ∩ B| / |A ∪ B|
```

**Propriétés:**
- **Symétrique:** J(A,B) = J(B,A)
- **Borné:** 0 ≤ J(A,B) ≤ 1
- **Identité:** J(A,A) = 1
- **Disjoint:** J(A,B) = 0 si A ∩ B = ∅

**Exemple:**
```python
A = {1, 2, 3, 4, 5}
B = {3, 4, 5, 6, 7}

Intersection = {3, 4, 5}  → |A ∩ B| = 3
Union = {1, 2, 3, 4, 5, 6, 7}  → |A ∪ B| = 7

J(A,B) = 3/7 ≈ 0.43 (43% de similarité)
```

---

## ⚙️ Configuration

### Spark Configuration (spark-defaults.conf)

**Ressources:**
```properties
spark.executor.memory=2g         # Mémoire par executor
spark.driver.memory=1g           # Mémoire du driver
spark.executor.cores=2           # Cores par executor
spark.default.parallelism=4      # Niveau de parallélisme
```

**Performance:**
```properties
spark.sql.shuffle.partitions=4   # Partitions pour shuffles
spark.io.compression.codec=snappy # Compression
spark.rdd.compress=true          # Compression RDD
```

**Réseau:**
```properties
spark.network.timeout=120s       # Timeout réseau
spark.rpc.askTimeout=120s        # Timeout RPC
```

### HDFS Configuration (hdfs-site.xml)

**Stockage:**
```xml
<property>
    <name>dfs.replication</name>
    <value>1</value>  <!-- Dev: 1, Prod: 3 -->
</property>

<property>
    <name>dfs.blocksize</name>
    <value>134217728</value>  <!-- 128 MB -->
</property>
```

**Réseau:**
```xml
<property>
    <name>dfs.namenode.rpc-address</name>
    <value>spark-master:9000</value>
</property>
```

---

## 📈 Performance et Scalabilité

### Métriques de Performance

**Temps d'Exécution (estimé):**
| Nombre de Fichiers | Taille Moy. | Temps Total |
|--------------------|-------------|-------------|
| 10                 | 100 lignes  | ~10 sec     |
| 50                 | 100 lignes  | ~45 sec     |
| 100                | 100 lignes  | ~3 min      |
| 500                | 100 lignes  | ~20 min     |

**Facteurs d'influence:**
- Complexité du code (nombre de tokens)
- Nombre de comparaisons (n²)
- Réseau entre conteneurs
- I/O HDFS

### Optimisations

**1. Augmenter le Parallélisme:**
```yaml
# docker-compose.yml
environment:
  - SPARK_WORKER_CORES=4    # Au lieu de 2
  - SPARK_WORKER_MEMORY=4g  # Au lieu de 2g
```

**2. Ajouter des Workers:**
```yaml
spark-worker-3:
  # Configuration identique aux autres workers
  environment:
    - SPARK_WORKER_PORT=7080
    - SPARK_WORKER_WEBUI_PORT=8083
```

**3. Optimiser les Partitions:**
```python
# Repartitionner selon le nombre de cores
files_rdd = files_rdd.repartition(num_workers * cores_per_worker)
```

**4. Utiliser le Cache:**
```python
# Mettre en cache les RDDs réutilisés
features_rdd.cache()
features_rdd.count()  # Déclencher le cache
```

### Scalabilité

**Horizontale (Ajouter des Workers):**
- ✅ Linéaire pour le traitement des fichiers
- ✅ Quasi-linéaire pour l'extraction AST
- ⚠️ Limité par le cartésien (comparaison)

**Verticale (Plus de Ressources):**
- ✅ Plus de mémoire → plus de cache
- ✅ Plus de cores → plus de parallélisme
- ⚠️ Rendements décroissants au-delà de 8 cores

**Recommandations Production:**
- **Petit déploiement (< 100 fichiers):**
  - 1 Master + 2 Workers (4 cores, 4GB chacun)
  
- **Moyen déploiement (100-1000 fichiers):**
  - 1 Master + 5 Workers (8 cores, 8GB chacun)
  
- **Large déploiement (> 1000 fichiers):**
  - 1 Master + 10+ Workers (16+ cores, 16GB+ chacun)
  - Activer Kryo serialization
  - Optimiser les shuffles

---

## 🔒 Sécurité

### Environnement de Développement

**Configurations actuelles (NON pour production):**
- ❌ Permissions HDFS désactivées
- ❌ Authentification Spark désactivée
- ❌ Pas de SSL/TLS
- ❌ Ports exposés publiquement

### Recommandations Production

**1. HDFS Security:**
```xml
<property>
    <name>dfs.permissions.enabled</name>
    <value>true</value>
</property>

<property>
    <name>hadoop.security.authentication</name>
    <value>kerberos</value>
</property>
```

**2. Spark Security:**
```properties
spark.authenticate=true
spark.authenticate.secret=<secret_key>
spark.network.crypto.enabled=true
spark.ssl.enabled=true
```

**3. Docker Network:**
```yaml
networks:
  spark-network:
    driver: bridge
    internal: true  # Isoler du monde extérieur
```

**4. Reverse Proxy:**
```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name plagiarism.example.com;
    
    location / {
        proxy_pass http://app-client:8501;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📚 Références

### Technologies
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Hadoop HDFS Guide](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsUserGuide.html)
- [Streamlit Documentation](https://docs.streamlit.io/)

### Algorithmes
- Winnowing Paper: [Schleimer et al., 2003](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf)
- Jaccard Similarity: [Wikipedia](https://en.wikipedia.org/wiki/Jaccard_index)

### Détection de Plagiat
- MOSS (Measure Of Software Similarity)
- JPlag
- SIM Software Similarity Tester

---

**Version:** 1.0  
**Dernière mise à jour:** November 2025  
**Auteur:** CodePlagiat Project
