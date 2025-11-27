"""
============================================
Utilitaires HDFS
============================================
Module pour interagir avec HDFS depuis Python.
Fournit des fonctions pour uploader, télécharger,
lister et gérer les fichiers dans HDFS.

Utilisation:
    from utils.hdfs_utils import HDFSClient
    
    client = HDFSClient("hdfs://spark-master:9000")
    client.upload_file("local.txt", "/app/input/local.txt")
============================================
"""

import os
import subprocess
from typing import List, Optional


class HDFSClient:
    """
    Client pour interagir avec HDFS via les commandes hadoop fs.
    """
    
    def __init__(self, hdfs_url: str = "hdfs://spark-master:9000"):
        """
        Initialise le client HDFS.
        
        Args:
            hdfs_url (str): URL du NameNode HDFS
        """
        self.hdfs_url = hdfs_url
        self.hadoop_bin = os.environ.get('HADOOP_HOME', '/opt/hadoop') + '/bin/hdfs'
        
    def _run_command(self, command: List[str]) -> tuple:
        """
        Exécute une commande HDFS.
        
        Args:
            command (List[str]): Commande à exécuter
            
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def list_files(self, hdfs_path: str) -> List[str]:
        """
        Liste les fichiers dans un répertoire HDFS.
        
        Args:
            hdfs_path (str): Chemin HDFS
            
        Returns:
            List[str]: Liste des fichiers
        """
        full_path = f"{self.hdfs_url}{hdfs_path}"
        command = [self.hadoop_bin, 'dfs', '-ls', full_path]
        
        returncode, stdout, stderr = self._run_command(command)
        
        if returncode != 0:
            print(f"Erreur lors du listing: {stderr}")
            return []
        
        # Parser la sortie
        files = []
        for line in stdout.split('\n'):
            if line.startswith('-') or line.startswith('d'):
                parts = line.split()
                if len(parts) >= 8:
                    files.append(parts[-1])
        
        return files
    
    def upload_file(self, local_path: str, hdfs_path: str) -> bool:
        """
        Upload un fichier vers HDFS.
        
        Args:
            local_path (str): Chemin local du fichier
            hdfs_path (str): Chemin de destination dans HDFS
            
        Returns:
            bool: True si succès, False sinon
        """
        full_hdfs_path = f"{self.hdfs_url}{hdfs_path}"
        command = [self.hadoop_bin, 'dfs', '-put', '-f', local_path, full_hdfs_path]
        
        returncode, stdout, stderr = self._run_command(command)
        
        if returncode != 0:
            print(f"Erreur lors de l'upload: {stderr}")
            return False
        
        print(f"✅ Fichier uploadé: {local_path} -> {hdfs_path}")
        return True
    
    def download_file(self, hdfs_path: str, local_path: str) -> bool:
        """
        Télécharge un fichier depuis HDFS.
        
        Args:
            hdfs_path (str): Chemin HDFS du fichier
            local_path (str): Chemin local de destination
            
        Returns:
            bool: True si succès, False sinon
        """
        full_hdfs_path = f"{self.hdfs_url}{hdfs_path}"
        command = [self.hadoop_bin, 'dfs', '-get', '-f', full_hdfs_path, local_path]
        
        returncode, stdout, stderr = self._run_command(command)
        
        if returncode != 0:
            print(f"Erreur lors du téléchargement: {stderr}")
            return False
        
        print(f"✅ Fichier téléchargé: {hdfs_path} -> {local_path}")
        return True
    
    def create_directory(self, hdfs_path: str) -> bool:
        """
        Crée un répertoire dans HDFS.
        
        Args:
            hdfs_path (str): Chemin du répertoire à créer
            
        Returns:
            bool: True si succès, False sinon
        """
        full_path = f"{self.hdfs_url}{hdfs_path}"
        command = [self.hadoop_bin, 'dfs', '-mkdir', '-p', full_path]
        
        returncode, stdout, stderr = self._run_command(command)
        
        if returncode != 0:
            print(f"Erreur lors de la création du répertoire: {stderr}")
            return False
        
        print(f"✅ Répertoire créé: {hdfs_path}")
        return True
    
    def delete(self, hdfs_path: str, recursive: bool = False) -> bool:
        """
        Supprime un fichier ou répertoire dans HDFS.
        
        Args:
            hdfs_path (str): Chemin à supprimer
            recursive (bool): Suppression récursive si répertoire
            
        Returns:
            bool: True si succès, False sinon
        """
        full_path = f"{self.hdfs_url}{hdfs_path}"
        command = [self.hadoop_bin, 'dfs', '-rm']
        
        if recursive:
            command.append('-r')
        
        command.append(full_path)
        
        returncode, stdout, stderr = self._run_command(command)
        
        if returncode != 0:
            print(f"Erreur lors de la suppression: {stderr}")
            return False
        
        print(f"✅ Supprimé: {hdfs_path}")
        return True
    
    def exists(self, hdfs_path: str) -> bool:
        """
        Vérifie si un chemin existe dans HDFS.
        
        Args:
            hdfs_path (str): Chemin à vérifier
            
        Returns:
            bool: True si existe, False sinon
        """
        full_path = f"{self.hdfs_url}{hdfs_path}"
        command = [self.hadoop_bin, 'dfs', '-test', '-e', full_path]
        
        returncode, _, _ = self._run_command(command)
        
        return returncode == 0
    
    def get_file_size(self, hdfs_path: str) -> Optional[int]:
        """
        Obtient la taille d'un fichier dans HDFS.
        
        Args:
            hdfs_path (str): Chemin du fichier
            
        Returns:
            Optional[int]: Taille en octets, None si erreur
        """
        full_path = f"{self.hdfs_url}{hdfs_path}"
        command = [self.hadoop_bin, 'dfs', '-du', '-s', full_path]
        
        returncode, stdout, stderr = self._run_command(command)
        
        if returncode != 0:
            return None
        
        # Parser la sortie
        parts = stdout.split()
        if len(parts) >= 1:
            try:
                return int(parts[0])
            except ValueError:
                return None
        
        return None


def upload_directory(local_dir: str, hdfs_dir: str, 
                    hdfs_url: str = "hdfs://spark-master:9000"):
    """
    Upload récursif d'un répertoire vers HDFS.
    
    Args:
        local_dir (str): Répertoire local
        hdfs_dir (str): Répertoire HDFS de destination
        hdfs_url (str): URL du NameNode
    """
    client = HDFSClient(hdfs_url)
    
    # Créer le répertoire de destination
    client.create_directory(hdfs_dir)
    
    # Parcourir récursivement le répertoire local
    for root, dirs, files in os.walk(local_dir):
        # Calculer le chemin relatif
        rel_path = os.path.relpath(root, local_dir)
        hdfs_subdir = os.path.join(hdfs_dir, rel_path).replace('\\', '/')
        
        # Créer le sous-répertoire dans HDFS
        if rel_path != '.':
            client.create_directory(hdfs_subdir)
        
        # Uploader chaque fichier
        for file in files:
            local_file = os.path.join(root, file)
            hdfs_file = os.path.join(hdfs_subdir, file).replace('\\', '/')
            client.upload_file(local_file, hdfs_file)
