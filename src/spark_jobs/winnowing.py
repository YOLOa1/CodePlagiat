"""
============================================
Algorithme de Winnowing
============================================
Implémentation de l'algorithme Winnowing pour générer des empreintes
digitales (fingerprints) robustes pour la détection de plagiat.

Référence:
    "Winnowing: Local Algorithms for Document Fingerprinting"
    Schleimer, Wilkerson, Aiken (2003)
    https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf

Principe:
    1. Génération de k-grams depuis les tokens
    2. Hashing de chaque k-gram
    3. Application de la fenêtre glissante (window)
    4. Sélection du hash minimum dans chaque fenêtre

Utilisation:
    hasher = WinnowingHasher(k=5, window_size=4)
    fingerprints = hasher.generate_fingerprints(tokens)
============================================
"""

import hashlib
from typing import List, Set, Tuple


class WinnowingHasher:
    """
    Implémentation de l'algorithme Winnowing pour générer des empreintes digitales.
    
    Attributes:
        k (int): Taille des k-grams (nombre de tokens consécutifs)
        window_size (int): Taille de la fenêtre glissante pour sélection
    """
    
    def __init__(self, k: int = 5, window_size: int = 4):
        """
        Initialise le générateur Winnowing.
        
        Args:
            k (int): Taille des k-grams (défaut: 5)
                    Plus k est grand, plus la détection est stricte
            window_size (int): Taille de la fenêtre (défaut: 4)
                              Plus la fenêtre est grande, moins il y a d'empreintes
                              
        Recommandations:
            - k=5, window=4 : bon équilibre (détecte des copies de ~4-5 lignes)
            - k=3, window=2 : très sensible (détecte de petites similitudes)
            - k=10, window=7 : peu sensible (détecte uniquement de grosses copies)
        """
        if k < 1:
            raise ValueError("k doit être >= 1")
        if window_size < 1:
            raise ValueError("window_size doit être >= 1")
        if window_size > k:
            raise ValueError("window_size ne peut pas être > k")
            
        self.k = k
        self.window_size = window_size
        
        print(f"🔧 WinnowingHasher initialisé (k={k}, window={window_size})")
    
    def generate_fingerprints(self, tokens: List[str]) -> List[int]:
        """
        Génère les empreintes digitales depuis une liste de tokens.
        
        Pipeline:
            tokens -> k-grams -> hashes -> winnowing -> fingerprints
        
        Args:
            tokens (List[str]): Liste de tokens du code source
            
        Returns:
            List[int]: Liste des empreintes digitales sélectionnées
        """
        if not tokens or len(tokens) < self.k:
            return []
        
        # Étape 1: Générer les k-grams
        kgrams = self._generate_kgrams(tokens)
        
        # Étape 2: Hasher chaque k-gram
        hashes = [self._hash_kgram(kg) for kg in kgrams]
        
        # Étape 3: Appliquer l'algorithme Winnowing
        fingerprints = self._winnow(hashes)
        
        return fingerprints
    
    def _generate_kgrams(self, tokens: List[str]) -> List[Tuple[str, ...]]:
        """
        Génère tous les k-grams depuis une liste de tokens.
        
        Un k-gram est une séquence de k tokens consécutifs.
        
        Exemple:
            tokens = ['a', 'b', 'c', 'd'], k=3
            k-grams = [('a','b','c'), ('b','c','d')]
        
        Args:
            tokens (List[str]): Liste de tokens
            
        Returns:
            List[Tuple[str, ...]]: Liste de k-grams
        """
        kgrams = []
        
        for i in range(len(tokens) - self.k + 1):
            kgram = tuple(tokens[i:i + self.k])
            kgrams.append(kgram)
        
        return kgrams
    
    def _hash_kgram(self, kgram: Tuple[str, ...]) -> int:
        """
        Calcule un hash numérique pour un k-gram.
        
        Utilise MD5 pour robustesse, puis convertit en entier.
        
        Args:
            kgram (Tuple[str, ...]): Un k-gram (tuple de tokens)
            
        Returns:
            int: Valeur de hash (entier positif)
        """
        # Concaténer les tokens du k-gram
        kgram_string = ' '.join(kgram)
        
        # Hash MD5
        hash_hex = hashlib.md5(kgram_string.encode('utf-8')).hexdigest()
        
        # Convertir en entier (utiliser les 8 premiers caractères)
        hash_int = int(hash_hex[:8], 16)
        
        return hash_int
    
    def _winnow(self, hashes: List[int]) -> List[int]:
        """
        Applique l'algorithme Winnowing pour sélectionner les empreintes.
        
        Algorithme:
            1. Créer une fenêtre glissante de taille window_size
            2. Pour chaque position de fenêtre:
               - Trouver le hash minimum dans la fenêtre
               - Si c'est un nouveau minimum (position différente), l'ajouter
        
        Cette technique garantit:
            - Robustesse aux petites modifications
            - Densité d'empreintes contrôlée
            - Détection des copies même avec renommage de variables
        
        Args:
            hashes (List[int]): Liste de tous les hashes
            
        Returns:
            List[int]: Liste des hashes sélectionnés (fingerprints)
        """
        if len(hashes) < self.window_size:
            # Si pas assez de hashes, retourner tous
            return hashes
        
        fingerprints = []
        min_positions = set()  # Positions déjà sélectionnées
        
        # Parcourir avec une fenêtre glissante
        for i in range(len(hashes) - self.window_size + 1):
            # Extraire la fenêtre
            window = hashes[i:i + self.window_size]
            
            # Trouver le minimum et sa position
            min_hash = min(window)
            min_pos = i + window.index(min_hash)
            
            # Si c'est une nouvelle position, ajouter l'empreinte
            if min_pos not in min_positions:
                fingerprints.append(min_hash)
                min_positions.add(min_pos)
        
        return fingerprints
    
    def compute_fingerprint_set(self, tokens: List[str]) -> Set[int]:
        """
        Génère un ensemble (set) d'empreintes pour comparaison rapide.
        
        Args:
            tokens (List[str]): Liste de tokens
            
        Returns:
            Set[int]: Ensemble d'empreintes uniques
        """
        fingerprints = self.generate_fingerprints(tokens)
        return set(fingerprints)
    
    def fingerprint_density(self, tokens: List[str]) -> float:
        """
        Calcule la densité d'empreintes (ratio empreintes/tokens).
        
        Utile pour diagnostiquer la configuration (k, window).
        
        Args:
            tokens (List[str]): Liste de tokens
            
        Returns:
            float: Densité (0.0 à 1.0)
        """
        if not tokens:
            return 0.0
        
        fingerprints = self.generate_fingerprints(tokens)
        
        if not fingerprints:
            return 0.0
        
        density = len(fingerprints) / len(tokens)
        return density


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def compare_configurations(tokens: List[str]):
    """
    Compare différentes configurations de Winnowing.
    Utile pour tuning des paramètres.
    
    Args:
        tokens (List[str]): Tokens de test
    """
    configs = [
        (3, 2),   # Très sensible
        (5, 4),   # Équilibré (défaut)
        (7, 5),   # Moyennement sensible
        (10, 7),  # Peu sensible
    ]
    
    print(f"\n{'='*60}")
    print(f"Comparaison des Configurations Winnowing")
    print(f"{'='*60}")
    print(f"Nombre de tokens: {len(tokens)}\n")
    
    for k, window in configs:
        hasher = WinnowingHasher(k=k, window_size=window)
        fingerprints = hasher.generate_fingerprints(tokens)
        density = hasher.fingerprint_density(tokens)
        
        print(f"k={k:2d}, window={window:2d} -> "
              f"{len(fingerprints):4d} empreintes "
              f"(densité: {density:.2%})")
    
    print(f"{'='*60}\n")


def test_winnowing():
    """
    Test simple de l'algorithme Winnowing.
    """
    # Tokens d'exemple
    tokens = ['def', 'hello', 'print', 'hello', 'world', 'return', 'True']
    
    print(f"\n🧪 Test Winnowing")
    print(f"Tokens: {tokens}")
    
    hasher = WinnowingHasher(k=3, window_size=2)
    fingerprints = hasher.generate_fingerprints(tokens)
    
    print(f"Empreintes générées: {len(fingerprints)}")
    print(f"Exemples: {fingerprints[:5]}")
    
    # Test de comparaison
    compare_configurations(tokens * 10)  # Répéter pour plus de tokens


if __name__ == "__main__":
    test_winnowing()
