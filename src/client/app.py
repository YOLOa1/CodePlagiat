"""
============================================
Application Client Streamlit
============================================
Interface Web pour le système de détection de plagiat.

Fonctionnalités:
    - Upload de fichiers sources (Python, C++, Java)
    - Lancement de l'analyse distribuée
    - Visualisation des résultats
    - Téléchargement des rapports

Utilisation:
    streamlit run app.py --server.port=8501
============================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime
import time

# Ajouter le chemin src au PYTHONPATH
sys.path.append('/app/src')

from utils.hdfs_utils import HDFSClient
from utils.spark_utils import test_spark_connection


# ============================================
# CONFIGURATION DE LA PAGE
# ============================================
st.set_page_config(
    page_title="Détection de Plagiat - CodePlagiat",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# STYLE CSS PERSONNALISÉ
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #856404;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# INITIALISATION DE LA SESSION
# ============================================
if 'hdfs_client' not in st.session_state:
    st.session_state.hdfs_client = HDFSClient("hdfs://spark-master:9000")

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

if 'latest_job_type' not in st.session_state:
    st.session_state.latest_job_type = None

if 'latest_target_file' not in st.session_state:
    st.session_state.latest_target_file = None


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def check_system_health():
    """
    Vérifie l'état du système (Spark + HDFS).
    
    Returns:
        dict: État des composants
    """
    health = {
        'spark': False,
        'hdfs': False
    }
    
    # Test Spark
    try:
        health['spark'] = test_spark_connection()
    except:
        health['spark'] = False
    
    # Test HDFS
    try:
        hdfs_client = st.session_state.hdfs_client
        health['hdfs'] = hdfs_client.exists('/')
    except:
        health['hdfs'] = False
    
    return health


def upload_to_hdfs(uploaded_file):
    """
    Upload un fichier vers HDFS.
    
    Args:
        uploaded_file: Fichier uploadé via Streamlit
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Créer un fichier temporaire
        temp_path = f"/tmp/{uploaded_file.name}"
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Upload vers HDFS
        hdfs_path = f"/app/input/{uploaded_file.name}"
        hdfs_client = st.session_state.hdfs_client
        
        success = hdfs_client.upload_file(temp_path, hdfs_path)
        
        # Nettoyer le fichier temporaire
        os.remove(temp_path)
        
        return success
    
    except Exception as e:
        st.error(f"Erreur lors de l'upload: {e}")
        return False


def submit_spark_job(target_file=None):
    """
    Soumet le job Spark pour analyse.
    
    Args:
        target_file: Nom du fichier cible pour comparaison ciblée (optionnel)
    
    Returns:
        bool: True si soumission réussie, False sinon
    """
    try:
        import subprocess
        import os
        
        # Créer l'archive des modules si elle n'existe pas
        zip_path = "/app/src/spark_jobs.zip"
        if not os.path.exists(zip_path):
            import shutil
            shutil.make_archive('/app/src/spark_jobs', 'zip', '/app/src', 'spark_jobs')
        
        # Timestamp pour un dossier unique
        timestamp = int(time.time())
        job_type = "target" if target_file else "all"
        output_path = f"hdfs://spark-master:9000/app/results/run_{job_type}_{timestamp}"
        
        # Commande spark-submit avec py-files
        command = [
            "/opt/spark/bin/spark-submit",
            "--master", "spark://spark-master:7077",
            "--deploy-mode", "client",
            "--driver-memory", "1g",
            "--executor-memory", "1g",
            "--executor-cores", "1",
            "--py-files", zip_path,
            "/app/src/spark_jobs/detect_plagiarism.py",
            "--input", "hdfs://spark-master:9000/app/input",
            "--output", output_path
        ]
        
        # Ajouter le paramètre --target si spécifié
        if target_file:
            command.extend(["--target", target_file])
        
        # Exécuter et attendre la fin
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Afficher la progression
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for line in process.stdout:
            # Afficher les lignes importantes
            if any(keyword in line for keyword in ['✅', '🔍', '📊', '💾', 'TERMINÉ', 'ERREUR']):
                status_text.text(line.strip())
            
            # Mettre à jour la barre de progression basée sur les étapes
            if 'Lecture des fichiers' in line:
                progress_bar.progress(20)
            elif 'Extraction des features' in line:
                progress_bar.progress(40)
            elif 'Comparaison par paires' in line:
                progress_bar.progress(60)
            elif 'Sauvegarde des résultats' in line:
                progress_bar.progress(80)
            elif 'TERMINÉ AVEC SUCCÈS' in line:
                progress_bar.progress(100)
        
        process.wait()
        
        # Sauvegarder le chemin de sortie dans la session
        if process.returncode == 0:
            st.session_state.latest_output = output_path
            st.session_state.latest_job_type = "target" if target_file else "all"
            st.session_state.latest_target_file = target_file
            return True
        else:
            st.error(f"Le job a échoué avec le code: {process.returncode}")
            return False
    
    except Exception as e:
        st.error(f"Erreur lors de la soumission: {e}")
        import traceback
        st.error(traceback.format_exc())
        return False


def get_hdfs_files():
    """
    Récupère la liste des fichiers disponibles dans HDFS /app/input.
    
    Returns:
        list: Liste des noms de fichiers
    """
    try:
        import subprocess
        
        result = subprocess.run(
            ['hdfs', 'dfs', '-ls', '/app/input'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return []
        
        # Extraire les noms de fichiers
        files = []
        for line in result.stdout.strip().split('\n'):
            if '/app/input/' in line and not line.strip().startswith('Found'):
                parts = line.split()
                if len(parts) > 0:
                    filepath = parts[-1]
                    filename = filepath.split('/')[-1]
                    if filename and filename.strip() and not filename.startswith('.'):
                        files.append(filename.strip())
        
        return sorted(files)
    
    except Exception as e:
        st.error(f"Erreur lors de la récupération des fichiers HDFS: {e}")
        return []


def count_hdfs_files():
    """
    Compte le nombre de fichiers dans HDFS /app/input.
    
    Returns:
        int: Nombre de fichiers
    """
    return len(get_hdfs_files())


def delete_latest_results():
    """
    Supprime les derniers résultats d'analyse de HDFS.
    
    Returns:
        bool: True si succès, False sinon
    """
    try:
        import subprocess
        
        # Lister les dossiers dans /app/results
        result = subprocess.run(
            ['hdfs', 'dfs', '-ls', '/app/results'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            return False
        
        # Extraire le dossier le plus récent (run_*)
        lines = result.stdout.strip().split('\n')
        run_dirs = []
        for line in lines:
            if 'run_' in line:
                parts = line.split()
                if len(parts) > 0:
                    run_dirs.append(parts[-1])
        
        if not run_dirs:
            return False
        
        # Prendre le plus récent
        latest_dir = sorted(run_dirs)[-1]
        
        # Supprimer le dossier
        result = subprocess.run(
            ['hdfs', 'dfs', '-rm', '-r', latest_dir],
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
    
    except Exception as e:
        st.error(f"Erreur lors de la suppression: {e}")
        return False


def load_results():
    """
    Charge les résultats depuis HDFS.
    
    Returns:
        pd.DataFrame: DataFrame des résultats, None si erreur
    """
    try:
        import subprocess
        import io
        
        # Utiliser le dernier output si disponible, sinon chercher le plus récent
        if hasattr(st.session_state, 'latest_output') and st.session_state.latest_output:
            result_path = st.session_state.latest_output.replace('hdfs://spark-master:9000', '')
        else:
            # Lister les dossiers dans /app/results
            result = subprocess.run(
                ['hdfs', 'dfs', '-ls', '/app/results'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                st.warning("Aucun dossier de résultats trouvé dans HDFS")
                return None
            
            # Extraire le dossier le plus récent (run_*)
            lines = result.stdout.strip().split('\n')
            run_dirs = [line.split()[-1] for line in lines if 'run_' in line]
            
            if not run_dirs:
                st.warning("Aucun dossier run_* trouvé")
                return None
            
            result_path = sorted(run_dirs)[-1]
        
        st.info(f"📂 Chargement depuis: {result_path}")
        
        # Lire directement le contenu CSV avec hdfs dfs -cat
        # Utiliser un pattern pour capturer tous les fichiers part-*.csv
        csv_pattern = f"{result_path}/part-*.csv"
        
        result = subprocess.run(
            ['hdfs', 'dfs', '-cat', csv_pattern],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            st.error(f"Erreur lors de la lecture du CSV: {result.stderr}")
            return None
        
        # Vérifier si on a du contenu
        csv_content = result.stdout.strip()
        if not csv_content or csv_content == "file1,file2,similarity_score,detection_time":
            st.warning("Le fichier de résultats est vide (aucune similarité détectée)")
            return None
        
        # Charger le CSV depuis le contenu texte
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Vérifier si le dataframe est vide
        if df.empty:
            st.warning("Aucune similarité détectée dans les résultats")
            return None
        
        # Nettoyer les noms de fichiers pour affichage (garder juste le nom)
        if 'file1' in df.columns:
            df['file1'] = df['file1'].apply(lambda x: x.split('/')[-1] if isinstance(x, str) and '/' in x else x)
        if 'file2' in df.columns:
            df['file2'] = df['file2'].apply(lambda x: x.split('/')[-1] if isinstance(x, str) and '/' in x else x)
        
        return df
    
    except Exception as e:
        st.error(f"Erreur lors du chargement des résultats: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None


# ============================================
# INTERFACE PRINCIPALE
# ============================================

def main():
    """
    Interface principale de l'application.
    """
    
    # ========================================
    # HEADER
    # ========================================
    st.markdown('<div class="main-header">🔍 Détection de Plagiat Distribué</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Analyse de code source avec Apache Spark</div>', 
                unsafe_allow_html=True)
    
    # ========================================
    # SIDEBAR - ÉTAT DU SYSTÈME
    # ========================================
    with st.sidebar:
        st.header("⚙️ État du Système")
        
        if st.button("🔄 Vérifier la santé du système"):
            with st.spinner("Vérification en cours..."):
                health = check_system_health()
            
            if health['spark']:
                st.success("✅ Spark Master: Opérationnel")
            else:
                st.error("❌ Spark Master: Indisponible")
            
            if health['hdfs']:
                st.success("✅ HDFS: Opérationnel")
            else:
                st.error("❌ HDFS: Indisponible")
        
        st.markdown("---")
        
        st.header("📊 Statistiques")
        hdfs_file_count = count_hdfs_files()
        st.metric("Fichiers dans HDFS", hdfs_file_count)
        
        if st.button("🔄 Actualiser"):
            st.rerun()
        
        st.markdown("---")
        
        st.header("ℹ️ À propos")
        st.info("""
        **CodePlagiat v1.0**
        
        Système de détection de plagiat distribué utilisant:
        - Apache Spark 3.3.0
        - Hadoop HDFS 3.3.1
        - Algorithme Winnowing
        - Similarité Jaccard
        """)
    
    # ========================================
    # ONGLETS PRINCIPAUX
    # ========================================
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyse", "📊 Résultats", "📖 Documentation"])
    
    # ========================================
    # ONGLET 1: UPLOAD & ANALYSE
    # ========================================
    with tab1:
        st.header("📤 Upload de fichiers sources")
        
        st.info("""
        **Instructions:**
        1. Uploadez vos fichiers sources (Python, C++, Java)
        2. Vérifiez la liste des fichiers
        3. Lancez l'analyse distribuée
        """)
        
        # Upload de fichiers
        uploaded_files = st.file_uploader(
            "Sélectionnez les fichiers à analyser",
            type=['py', 'cpp', 'c', 'h', 'java'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
            
            # Afficher la liste
            with st.expander("📋 Voir la liste des fichiers"):
                for f in uploaded_files:
                    st.write(f"- {f.name} ({f.size} octets)")
            
            # Bouton d'upload vers HDFS
            if st.button("⬆️ Upload vers HDFS", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"Upload de {file.name}...")
                    success = upload_to_hdfs(file)
                    
                    if success:
                        st.session_state.uploaded_files.append(file.name)
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("✅ Upload terminé!")
                st.success("Tous les fichiers ont été uploadés vers HDFS")
        
        st.markdown("---")
        
        # Lancement de l'analyse
        st.header("🚀 Lancement de l'analyse")
        
        st.info("""
        **Analyse complète**: Compare tous les fichiers entre eux pour détecter les similarités.
        """)
        
        # Vérifier les fichiers dans HDFS
        hdfs_files = get_hdfs_files()
        hdfs_file_count = len(hdfs_files)
        
        # Vérification avant lancement
        if hdfs_file_count < 2:
            st.warning(f"⚠️ Veuillez uploader au moins 2 fichiers pour démarrer l'analyse (actuellement: {hdfs_file_count} fichier(s) dans HDFS)")
            
            if hdfs_file_count > 0:
                with st.expander("📋 Fichiers disponibles dans HDFS"):
                    for f in hdfs_files:
                        st.write(f"- {f}")
        else:
            st.success(f"📁 {hdfs_file_count} fichiers prêts pour l'analyse dans HDFS")
            
            with st.expander("📋 Voir la liste des fichiers"):
                for f in hdfs_files:
                    st.write(f"- {f}")
            
            if st.button("🔍 Analyser tous les fichiers", type="primary"):
                with st.spinner("🔄 Soumission du job Spark en cours..."):
                    success = submit_spark_job()
                
                if success:
                    st.success("✅ Job Spark soumis avec succès!")
                    st.info("""
                    L'analyse complète est en cours d'exécution sur le cluster Spark.
                    Consultez l'onglet **Résultats** dans quelques instants.
                    """)
                    
                    # Lien vers Spark UI
                    st.markdown("[🌐 Voir le statut sur Spark UI](http://localhost:8080)")
                else:
                    st.error("❌ Erreur lors de la soumission du job")
    
    # ========================================
    # ONGLET 2: RÉSULTATS
    # ========================================
    with tab2:
        st.header("📊 Résultats de l'analyse")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🔄 Charger les résultats", use_container_width=True):
                with st.spinner("Chargement des résultats depuis HDFS..."):
                    df = load_results()
                
                if df is not None:
                    st.session_state.analysis_results = df
                    st.success("✅ Résultats chargés!")
                else:
                    st.warning("⚠️ Aucun résultat disponible. Lancez d'abord une analyse.")
        
        with col2:
            if st.button("🗑️ Supprimer", use_container_width=True, help="Supprimer les derniers résultats"):
                with st.spinner("Suppression en cours..."):
                    success = delete_latest_results()
                
                if success:
                    st.success("✅ Résultats supprimés!")
                    st.session_state.analysis_results = None
                    st.rerun()
                else:
                    st.error("❌ Aucun résultat à supprimer ou erreur")
        
        st.markdown("---")
        
        # Affichage des résultats
        if st.session_state.analysis_results is not None:
            df = st.session_state.analysis_results
            
            # Section de filtrage par fichier en haut
            st.subheader("🔍 Filtrer les résultats par fichier")
            
            # Récupérer la liste des fichiers uniques
            all_files = sorted(set(df['file1'].tolist() + df['file2'].tolist()))
            
            filter_options = ["Tous les résultats"] + all_files
            
            selected_filter = st.selectbox(
                "Afficher les comparaisons pour:",
                options=filter_options,
                help="Sélectionnez un fichier pour voir uniquement ses comparaisons",
                key="file_filter_selector"
            )
            
            # Filtrer le dataframe si un fichier est sélectionné
            if selected_filter != "Tous les résultats":
                filtered_df = df[
                    (df['file1'] == selected_filter) | (df['file2'] == selected_filter)
                ].copy()
                
                # Créer une colonne "Autre fichier" pour simplifier l'affichage
                filtered_df['other_file'] = filtered_df.apply(
                    lambda row: row['file2'] if row['file1'] == selected_filter else row['file1'],
                    axis=1
                )
                
                # Trier par score décroissant
                filtered_df = filtered_df.sort_values('similarity_score', ascending=False)
                
                st.info(f"📄 Affichage des comparaisons pour: **{selected_filter}**")
            else:
                filtered_df = df
                st.info("📊 Affichage de toutes les comparaisons")
            
            st.markdown("---")
            
            # Statistiques globales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Comparaisons affichées", len(filtered_df))
            
            with col2:
                plagiarism_count = len(filtered_df[filtered_df['similarity_score'] >= 0.7])
                st.metric("Plagiats détectés (>70%)", plagiarism_count)
            
            with col3:
                avg_similarity = filtered_df['similarity_score'].mean()
                st.metric("Similarité moyenne", f"{avg_similarity:.2%}")
            
            # Graphique de distribution
            st.subheader("📈 Distribution des similarités")
            
            fig = px.histogram(
                filtered_df,
                x='similarity_score',
                nbins=20,
                title="Distribution des scores de similarité",
                labels={'similarity_score': 'Score de similarité', 'count': 'Nombre de paires'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Top 10 des similarités
            st.subheader("🏆 Top 10 des similarités")
            
            top_10 = filtered_df.nlargest(10, 'similarity_score')
            
            # Ajouter un indicateur visuel pour les plagiats
            def highlight_plagiarism(row):
                if row['similarity_score'] >= 0.95:
                    return ['background-color: #ff6b6b'] * len(row)
                elif row['similarity_score'] >= 0.80:
                    return ['background-color: #ffa07a'] * len(row)
                elif row['similarity_score'] >= 0.70:
                    return ['background-color: #fff4a3'] * len(row)
                else:
                    return [''] * len(row)
            
            # Préparer le dataframe pour le top 10
            if selected_filter != "Tous les résultats":
                # Si filtré, afficher avec la colonne other_file
                top_10_display = top_10[['other_file', 'similarity_score']].copy()
                top_10_display.columns = ['Fichier comparé', 'Score de similarité']
                top_10_display['Score de similarité'] = top_10_display['Score de similarité'].apply(lambda x: f"{x:.2%}")
            else:
                # Sinon afficher file1 et file2
                top_10_display = top_10[['file1', 'file2', 'similarity_score']].copy()
                top_10_display['similarity_score'] = top_10_display['similarity_score'].apply(lambda x: f"{x:.2%}")
            
            st.dataframe(top_10_display, use_container_width=True, hide_index=True)
            
            st.caption("🔴 Rouge: Identique (95-100%) | 🟠 Orange: Très élevé (80-95%) | 🟡 Jaune: Élevé (70-80%)")
            
            # Graphique pour le fichier sélectionné (si filtré)
            if selected_filter != "Tous les résultats" and len(filtered_df) > 1:
                st.markdown("---")
                st.subheader(f"📊 Graphique des similarités pour {selected_filter}")
                
                fig_file = px.bar(
                    filtered_df,
                    x='other_file',
                    y='similarity_score',
                    title=f"Similarités de {selected_filter} avec les autres fichiers",
                    labels={'other_file': 'Fichier', 'similarity_score': 'Score de similarité'},
                    color='similarity_score',
                    color_continuous_scale=['green', 'yellow', 'orange', 'red']
                )
                fig_file.add_hline(y=0.7, line_dash="dash", line_color="red", 
                                  annotation_text="Seuil de plagiat (70%)")
                st.plotly_chart(fig_file, use_container_width=True)
            
            # Tableau complet
            st.markdown("---")
            st.subheader("📋 Résultats complets")
            
            # Préparer le dataframe d'affichage
            if selected_filter != "Tous les résultats":
                display_full = filtered_df[['other_file', 'similarity_score']].copy()
                display_full.columns = ['Fichier comparé', 'Score de similarité']
            else:
                display_full = filtered_df.copy()
            
            st.dataframe(display_full, use_container_width=True, hide_index=True)
            
            # Export
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            filename_suffix = f"_{selected_filter}" if selected_filter != "Tous les résultats" else "_all"
            st.download_button(
                label="💾 Télécharger les résultats (CSV)",
                data=csv_data,
                file_name=f"plagiarism_results{filename_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # ========================================
    # ONGLET 3: DOCUMENTATION
    # ========================================
    with tab3:
        st.header("📖 Documentation")
        
        st.markdown("""
        ## 🎯 Objectif
        
        Ce système détecte automatiquement les similarités entre des fichiers de code source
        en utilisant un algorithme distribué sur Apache Spark.
        
        ## 🆕 Modes d'Analyse
        
        ### 1. Comparaison Complète (All-to-All)
        - Compare **tous les fichiers** entre eux
        - Génère une matrice complète de comparaisons
        - Idéal pour détecter le plagiat dans un groupe de soumissions
        - Complexité: O(n²)
        
        ### 2. Comparaison Ciblée (Target vs Database)
        - Compare **un fichier spécifique** avec tous les autres
        - Performance optimisée avec broadcast du fichier cible
        - Idéal pour vérifier une soumission suspecte ou une nouvelle soumission
        - Complexité: O(n)
        
        **Cas d'usage typiques:**
        - 🎓 Vérifier un étudiant suspect contre toute la base
        - 📧 Analyser rapidement une pièce jointe reçue par email
        - 🆕 Tester un nouveau fichier contre l'historique complet
        
        ## 🔬 Algorithme
        
        ### 1. Extraction AST
        - Parsing du code source pour extraire la structure syntaxique
        - Support de Python, C++, et Java
        - Normalisation des tokens
        
        ### 2. Algorithme Winnowing
        - Génération de k-grams (séquences de tokens)
        - Hashing de chaque k-gram
        - Sélection des empreintes minimales par fenêtre glissante
        - **Paramètres**: k=5, window=4
        
        ### 3. Calcul de Similarité
        - Comparaison par paires de tous les fichiers
        - Métrique: **Similarité de Jaccard**
        - Formule: J(A,B) = |A ∩ B| / |A ∪ B|
        
        ## 📊 Interprétation des Résultats
        
        | Score | Catégorie | Interprétation |
        |-------|-----------|----------------|
        | 95-100% | Identique | Copie quasi-parfaite |
        | 80-95% | Très élevée | Plagiat probable |
        | 60-80% | Élevée | Forte similarité, à investiguer |
        | 40-60% | Modérée | Similarité notable |
        | 20-40% | Faible | Peu de ressemblance |
        | 0-20% | Aucune | Codes distincts |
        
        ## 🏗️ Architecture
        
        ```
        Client Streamlit
             │
             ▼
        Spark Master ──┬── Worker 1
             │         └── Worker 2
             │
             ▼
          HDFS
        ```
        
        ## 🔗 Liens Utiles
        
        - [Spark Master UI](http://localhost:8080) - Monitoring du cluster
        - [HDFS NameNode UI](http://localhost:9870) - État du système de fichiers
        
        ## 📚 Références
        
        - **Winnowing Algorithm**: Schleimer, Wilkerson, Aiken (2003)
        - **Apache Spark**: https://spark.apache.org/
        - **HDFS**: https://hadoop.apache.org/
        """)


# ============================================
# POINT D'ENTRÉE
# ============================================
if __name__ == "__main__":
    main()
