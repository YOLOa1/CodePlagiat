"""
============================================
Système de Détection de Plagiat Distribué
============================================
Job PySpark Principal - detect_plagiarism.py

Ce script implémente le pipeline complet de détection :
1. Lecture des fichiers sources depuis HDFS
2. Extraction de l'AST (Abstract Syntax Tree)
3. Génération d'empreintes digitales (Winnowing Algorithm)
4. Comparaison par paires (Similarité Jaccard)
5. Sauvegarde des résultats dans HDFS

Utilisation:
    spark-submit --master spark://spark-master:7077 \\
                 --deploy-mode client \\
                 detect_plagiarism.py \\
                 --input hdfs://spark-master:9000/app/input \\
                 --output hdfs://spark-master:9000/app/output
============================================
"""

import sys
import argparse
from datetime import datetime
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType, ArrayType, IntegerType, FloatType, StructType, StructField

# Import des modules locaux
sys.path.append('/app/src')
from spark_jobs.ast_extractor import ASTExtractor
from spark_jobs.winnowing import WinnowingHasher
from spark_jobs.similarity import SimilarityCalculator


class PlagiarismDetector:
    """
    Classe principale pour la détection de plagiat distribuée.
    """
    
    def __init__(self, app_name="PlagiarismDetector", master_url="spark://spark-master:7077"):
        """
        Initialise la session Spark et les extracteurs.
        
        Args:
            app_name (str): Nom de l'application Spark
            master_url (str): URL du Spark Master
        """
        print(f"{'='*60}")
        print(f"🚀 Initialisation du Détecteur de Plagiat")
        print(f"{'='*60}")
        
        # Configuration Spark
        self.conf = SparkConf() \
            .setAppName(app_name) \
            .setMaster(master_url) \
            .set("spark.executor.memory", "2g") \
            .set("spark.driver.memory", "1g") \
            .set("spark.executor.cores", "2") \
            .set("spark.default.parallelism", "4") \
            .set("spark.sql.shuffle.partitions", "4")
        
        # Création de la session Spark
        self.spark = SparkSession.builder.config(conf=self.conf).getOrCreate()
        self.sc = self.spark.sparkContext
        
        # Configuration du niveau de log
        self.sc.setLogLevel("WARN")
        
        print(f"✅ SparkSession créée")
        print(f"   - Master: {master_url}")
        print(f"   - Application ID: {self.spark.sparkContext.applicationId}")
        print(f"   - Parallélisme: 4")
        
        # Initialisation des extracteurs
        self.ast_extractor = ASTExtractor()
        self.winnowing_hasher = WinnowingHasher(k=5, window_size=4)
        self.similarity_calculator = SimilarityCalculator(threshold=0.7)
        
        print(f"✅ Extracteurs initialisés")
        print(f"{'='*60}\n")
    
    def read_source_files(self, input_path):
        """
        Lit les fichiers sources depuis HDFS.
        
        Args:
            input_path (str): Chemin HDFS des fichiers d'entrée
            
        Returns:
            RDD: RDD de tuples (filename, content)
        """
        print(f"📂 Lecture des fichiers depuis: {input_path}")
        
        try:
            # Lecture des fichiers texte
            # wholeTextFiles() retourne (filename, content)
            files_rdd = self.sc.wholeTextFiles(input_path)
            
            # Filtrer par extension (.py, .cpp, .java)
            def is_valid_file(filename):
                return filename.endswith(('.py', '.cpp', '.java', '.c', '.h'))
            
            files_rdd = files_rdd.filter(lambda x: is_valid_file(x[0]))
            
            file_count = files_rdd.count()
            print(f"✅ {file_count} fichiers sources trouvés")
            
            # Afficher quelques exemples
            sample_files = files_rdd.take(3)
            print(f"\n📄 Exemples de fichiers:")
            for filename, _ in sample_files:
                print(f"   - {filename}")
            print()
            
            return files_rdd
            
        except Exception as e:
            print(f"❌ Erreur lors de la lecture des fichiers: {e}")
            raise
    
    def extract_features(self, files_rdd):
        """
        Extrait les features (AST + Winnowing) de chaque fichier.
        
        Args:
            files_rdd (RDD): RDD de (filename, content)
            
        Returns:
            RDD: RDD de (filename, language, fingerprints)
        """
        print(f"🔍 Extraction des features (AST + Winnowing)...")
        
        # Broadcast des paramètres seulement (pas d'objets)
        k_value = self.winnowing_hasher.k
        window_size = self.winnowing_hasher.window_size
        
        def extract_file_features(file_tuple):
            """
            Extrait les features d'un fichier.
            
            Args:
                file_tuple: (filename, content)
                
            Returns:
                tuple: (filename, language, fingerprints) ou None si erreur
            """
            filename, content = file_tuple
            
            try:
                # Imports locaux pour éviter les problèmes de sérialisation
                import sys
                sys.path.append('/app/src')
                from spark_jobs.ast_extractor import ASTExtractor
                from spark_jobs.winnowing import WinnowingHasher
                
                # 1. Déterminer le langage depuis l'extension
                if filename.endswith('.py'):
                    language = 'python'
                elif filename.endswith(('.cpp', '.c', '.h')):
                    language = 'cpp'
                elif filename.endswith('.java'):
                    language = 'java'
                else:
                    return None
                
                # 2. Extraire l'AST
                ast_extractor = ASTExtractor()
                ast_tokens = ast_extractor.extract_tokens(content, language)
                
                if not ast_tokens:
                    return (filename, language, [])
                
                # 3. Générer les empreintes avec Winnowing
                winnowing_hasher = WinnowingHasher(k=k_value, window_size=window_size)
                fingerprints = winnowing_hasher.generate_fingerprints(ast_tokens)
                
                return (filename, language, fingerprints)
                
            except Exception as e:
                print(f"⚠️  Erreur pour {filename}: {e}")
                return (filename, 'unknown', [])
        
        # Extraction parallèle des features
        features_rdd = files_rdd.map(extract_file_features).filter(lambda x: x is not None)
        
        # Cache pour réutilisation
        features_rdd.cache()
        
        feature_count = features_rdd.count()
        print(f"✅ Features extraites pour {feature_count} fichiers")
        
        # Statistiques
        sample_features = features_rdd.take(2)
        print(f"\n📊 Exemples de features:")
        for filename, language, fingerprints in sample_features:
            print(f"   - {filename}")
            print(f"     Langage: {language}")
            print(f"     Empreintes: {len(fingerprints)} hashes")
        print()
        
        return features_rdd
    
    def compare_pairs(self, features_rdd, target_file=None):
        """
        Compare tous les fichiers par paires pour détecter les similarités.
        
        Args:
            features_rdd (RDD): RDD de (filename, language, fingerprints)
            target_file (str): Fichier cible pour comparaison ciblée (optionnel)
            
        Returns:
            RDD: RDD de (file1, file2, similarity_score)
        """
        print(f"🔄 Comparaison par paires...")
        
        # Broadcast du seuil seulement (pas d'objets complexes)
        threshold = self.similarity_calculator.threshold
        
        if target_file:
            # Mode ciblé: comparer le fichier target contre tous les autres
            print(f"   Mode ciblé: {target_file} vs tous les autres")
            
            # Filtrer le fichier target
            target_rdd = features_rdd.filter(lambda x: target_file in x[0])
            target_data = target_rdd.collect()
            
            if not target_data:
                print(f"❌ Erreur: Fichier cible '{target_file}' introuvable dans les données")
                return self.sc.emptyRDD()
            
            target_info = target_data[0]
            print(f"   ✅ Fichier cible trouvé: {target_info[0]}")
            
            # Comparer le target contre tous les autres (sauf lui-même)
            other_files_rdd = features_rdd.filter(lambda x: target_file not in x[0])
            
            # Broadcast du fichier cible
            target_bc = self.sc.broadcast(target_info)
            
            def compare_with_target(other):
                """
                Compare le fichier cible avec un autre fichier.
                """
                target = target_bc.value
                file_target, lang_target, fp_target = target
                file_other, lang_other, fp_other = other
                
                # Ne comparer que les fichiers du même langage
                if lang_target != lang_other:
                    return (file_target, file_other, 0.0)
                
                # Calcul de la similarité Jaccard (sans dépendances)
                set_target = set(fp_target)
                set_other = set(fp_other)
                
                if not set_target or not set_other:
                    score = 0.0
                else:
                    intersection = len(set_target & set_other)
                    union = len(set_target | set_other)
                    score = intersection / union if union > 0 else 0.0
                
                return (file_target, file_other, score)
            
            similarities_rdd = other_files_rdd.map(compare_with_target)
            
        else:
            # Mode standard: créer toutes les paires possibles (cartésien)
            # Pour éviter les doublons, on filtre file1 < file2
            print(f"   Mode standard: tous contre tous")
            pairs_rdd = features_rdd.cartesian(features_rdd) \
                .filter(lambda pair: pair[0][0] < pair[1][0])  # file1 < file2
        
            def calculate_similarity(pair):
                """
                Calcule la similarité entre deux fichiers.
                
                Args:
                    pair: ((file1, lang1, fp1), (file2, lang2, fp2))
                    
                Returns:
                    tuple: (file1, file2, similarity_score)
                """
                (file1, lang1, fp1), (file2, lang2, fp2) = pair
                
                # Ne comparer que les fichiers du même langage
                if lang1 != lang2:
                    return (file1, file2, 0.0)
                
                # Calcul de la similarité Jaccard (sans dépendances)
                set1 = set(fp1)
                set2 = set(fp2)
                
                if not set1 or not set2:
                    score = 0.0
                else:
                    intersection = len(set1 & set2)
                    union = len(set1 | set2)
                    score = intersection / union if union > 0 else 0.0
                
                return (file1, file2, score)
            
            # Calcul parallèle des similarités
            similarities_rdd = pairs_rdd.map(calculate_similarity)
        
        # Filtrer les similarités significatives (> 0.1)
        significant_similarities = similarities_rdd.filter(lambda x: x[2] > 0.1)
        
        # Trier par score décroissant
        sorted_similarities = significant_similarities.sortBy(lambda x: -x[2])
        
        print(f"✅ Comparaisons terminées")
        
        return sorted_similarities
    
    def save_results(self, similarities_rdd, output_path):
        """
        Sauvegarde les résultats dans HDFS.
        
        Args:
            similarities_rdd (RDD): RDD de (file1, file2, similarity_score)
            output_path (str): Chemin HDFS de sortie
        """
        print(f"💾 Sauvegarde des résultats dans: {output_path}")
        
        try:
            # Convertir en DataFrame pour un meilleur format
            schema = StructType([
                StructField("file1", StringType(), False),
                StructField("file2", StringType(), False),
                StructField("similarity_score", FloatType(), False)
            ])
            
            df = self.spark.createDataFrame(similarities_rdd, schema)
            
            # Ajouter un timestamp
            from pyspark.sql.functions import lit, current_timestamp
            df = df.withColumn("detection_time", current_timestamp())
            
            # Sauvegarder en CSV
            df.coalesce(1).write.mode("overwrite").csv(
                output_path,
                header=True
            )
            
            # Afficher les top résultats
            print(f"\n🏆 Top 10 des similarités détectées:")
            top_10 = df.orderBy(col("similarity_score").desc()).limit(10)
            top_10.show(truncate=False)
            
            print(f"✅ Résultats sauvegardés avec succès")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            raise
    
    def run(self, input_path, output_path, target_file=None):
        """
        Exécute le pipeline complet de détection.
        
        Args:
            input_path (str): Chemin HDFS des fichiers d'entrée
            output_path (str): Chemin HDFS de sortie
            target_file (str): Fichier cible à comparer (optionnel)
        """
        start_time = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"🎯 DÉMARRAGE DU PIPELINE DE DÉTECTION")
        print(f"{'='*60}")
        print(f"⏰ Heure de début: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📥 Input: {input_path}")
        print(f"📤 Output: {output_path}")
        if target_file:
            print(f"🎯 Mode: Comparaison ciblée - fichier: {target_file}")
        else:
            print(f"🎯 Mode: Comparaison tous contre tous")
        print(f"{'='*60}\n")
        
        try:
            # Étape 1: Lecture des fichiers
            files_rdd = self.read_source_files(input_path)
            
            # Étape 2: Extraction des features
            features_rdd = self.extract_features(files_rdd)
            
            # Étape 3: Comparaison par paires
            similarities_rdd = self.compare_pairs(features_rdd, target_file)
            
            # Étape 4: Sauvegarde des résultats
            self.save_results(similarities_rdd, output_path)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n{'='*60}")
            print(f"✅ PIPELINE TERMINÉ AVEC SUCCÈS")
            print(f"{'='*60}")
            print(f"⏰ Heure de fin: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Durée totale: {duration:.2f} secondes")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ ERREUR DURANT L'EXÉCUTION")
            print(f"{'='*60}")
            print(f"Message: {e}")
            print(f"{'='*60}\n")
            raise
        
        finally:
            # Nettoyage
            self.spark.stop()
            print("🛑 SparkSession fermée\n")


def main():
    """
    Point d'entrée principal du script.
    """
    # Configuration des arguments en ligne de commande
    parser = argparse.ArgumentParser(
        description="Détection de plagiat de code source avec Spark"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="hdfs://spark-master:9000/app/input",
        help="Chemin HDFS des fichiers d'entrée"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="hdfs://spark-master:9000/app/output",
        help="Chemin HDFS de sortie"
    )
    parser.add_argument(
        "--master",
        type=str,
        default="spark://spark-master:7077",
        help="URL du Spark Master"
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Fichier cible à comparer contre tous les autres (chemin HDFS complet ou nom de fichier)"
    )
    
    args = parser.parse_args()
    
    # Création et exécution du détecteur
    detector = PlagiarismDetector(master_url=args.master)
    detector.run(args.input, args.output, target_file=args.target)


if __name__ == "__main__":
    main()
