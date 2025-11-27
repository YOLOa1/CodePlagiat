"""
============================================
Utilitaires Spark
============================================
Module contenant des fonctions utilitaires pour Spark.
Fournit des helpers pour la configuration, soumission de jobs,
et monitoring.

Utilisation:
    from utils.spark_utils import create_spark_session
    
    spark = create_spark_session("MyApp")
============================================
"""

from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession
from typing import Optional, Dict


def create_spark_session(
    app_name: str,
    master: str = "spark://spark-master:7077",
    config: Optional[Dict[str, str]] = None
) -> SparkSession:
    """
    Crée une SparkSession avec configuration par défaut.
    
    Args:
        app_name (str): Nom de l'application
        master (str): URL du Spark Master
        config (Dict[str, str]): Configuration additionnelle
        
    Returns:
        SparkSession: Session Spark configurée
    """
    builder = SparkSession.builder \
        .appName(app_name) \
        .master(master)
    
    # Configuration par défaut
    default_config = {
        "spark.executor.memory": "2g",
        "spark.driver.memory": "1g",
        "spark.executor.cores": "2",
        "spark.default.parallelism": "4",
        "spark.sql.shuffle.partitions": "4",
    }
    
    # Appliquer la configuration par défaut
    for key, value in default_config.items():
        builder = builder.config(key, value)
    
    # Appliquer la configuration personnalisée
    if config:
        for key, value in config.items():
            builder = builder.config(key, value)
    
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    
    return spark


def get_spark_ui_url(spark: SparkSession) -> str:
    """
    Obtient l'URL de l'interface Web Spark.
    
    Args:
        spark (SparkSession): Session Spark
        
    Returns:
        str: URL de l'UI Spark
    """
    app_id = spark.sparkContext.applicationId
    return f"http://spark-master:8080/app/{app_id}"


def print_spark_config(spark: SparkSession):
    """
    Affiche la configuration Spark actuelle.
    
    Args:
        spark (SparkSession): Session Spark
    """
    print(f"\n{'='*60}")
    print(f"⚙️  CONFIGURATION SPARK")
    print(f"{'='*60}")
    
    conf = spark.sparkContext.getConf()
    
    # Informations de base
    print(f"Application: {conf.get('spark.app.name')}")
    print(f"Master: {conf.get('spark.master')}")
    print(f"Application ID: {spark.sparkContext.applicationId}")
    
    print(f"\n📊 Ressources:")
    print(f"   - Executor Memory: {conf.get('spark.executor.memory', 'N/A')}")
    print(f"   - Driver Memory: {conf.get('spark.driver.memory', 'N/A')}")
    print(f"   - Executor Cores: {conf.get('spark.executor.cores', 'N/A')}")
    print(f"   - Parallelism: {conf.get('spark.default.parallelism', 'N/A')}")
    
    print(f"\n🔗 URLs:")
    print(f"   - Spark UI: {get_spark_ui_url(spark)}")
    print(f"{'='*60}\n")


def monitor_job_progress(spark: SparkSession):
    """
    Affiche la progression des jobs Spark.
    
    Args:
        spark (SparkSession): Session Spark
    """
    sc = spark.sparkContext
    status = sc.statusTracker()
    
    print(f"\n{'='*60}")
    print(f"📊 PROGRESSION DES JOBS")
    print(f"{'='*60}")
    
    active_jobs = status.getActiveJobIds()
    print(f"Jobs actifs: {len(active_jobs)}")
    
    for job_id in active_jobs:
        job_info = status.getJobInfo(job_id)
        if job_info:
            print(f"\n🔄 Job ID {job_id}:")
            print(f"   - Stages: {job_info.numTasks}")
    
    print(f"{'='*60}\n")


def test_spark_connection(master: str = "spark://spark-master:7077") -> bool:
    """
    Test la connexion à Spark.
    
    Args:
        master (str): URL du Spark Master
        
    Returns:
        bool: True si connexion réussie, False sinon
    """
    try:
        spark = create_spark_session("TestConnection", master)
        
        # Test simple
        rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5])
        result = rdd.sum()
        
        print(f"✅ Connexion Spark réussie (test sum: {result})")
        
        spark.stop()
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion Spark: {e}")
        return False
