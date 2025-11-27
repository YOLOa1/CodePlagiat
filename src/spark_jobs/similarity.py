"""
============================================
Calculateur de Similarité
============================================
Module pour calculer la similarité entre deux ensembles d'empreintes.
Implémente plusieurs métriques de similarité.

Métriques disponibles:
    - Jaccard Similarity (principal)
    - Containment
    - Cosine Similarity

Utilisation:
    calculator = SimilarityCalculator(threshold=0.7)
    score = calculator.jaccard_similarity(fp1, fp2)
    is_plagiarism = calculator.is_plagiarism(score)
============================================
"""

from typing import Set, Tuple
import math


class SimilarityCalculator:
    """
    Classe pour calculer différentes métriques de similarité entre ensembles d'empreintes.
    """
    
    def __init__(self, threshold: float = 0.7):
        """
        Initialise le calculateur de similarité.
        
        Args:
            threshold (float): Seuil de détection de plagiat (0.0 à 1.0)
                              Au-dessus de ce seuil, on considère qu'il y a plagiat
                              
        Recommandations:
            - 0.9-1.0 : Copie quasi-identique
            - 0.7-0.9 : Forte similarité (probable plagiat)
            - 0.5-0.7 : Similarité modérée (à investiguer)
            - 0.0-0.5 : Faible similarité
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold doit être entre 0.0 et 1.0")
        
        self.threshold = threshold
        
        print(f"🔧 SimilarityCalculator initialisé (seuil={threshold:.2%})")
    
    def jaccard_similarity(self, set1: Set[int], set2: Set[int]) -> float:
        """
        Calcule la similarité de Jaccard entre deux ensembles.
        
        Formule:
            J(A, B) = |A ∩ B| / |A ∪ B|
            
        Où:
            - |A ∩ B| = nombre d'éléments communs
            - |A ∪ B| = nombre d'éléments dans l'union
        
        Propriétés:
            - Valeur entre 0.0 (aucune similarité) et 1.0 (identique)
            - Symétrique: J(A,B) = J(B,A)
            - Robuste aux différences de taille
        
        Args:
            set1 (Set[int]): Premier ensemble d'empreintes
            set2 (Set[int]): Deuxième ensemble d'empreintes
            
        Returns:
            float: Score de similarité Jaccard (0.0 à 1.0)
        """
        # Cas particuliers
        if not set1 and not set2:
            return 1.0  # Deux ensembles vides sont identiques
        
        if not set1 or not set2:
            return 0.0  # Un ensemble vide -> aucune similarité
        
        # Calcul de l'intersection et de l'union
        intersection = set1 & set2
        union = set1 | set2
        
        # Similarité de Jaccard
        similarity = len(intersection) / len(union)
        
        return similarity
    
    def containment(self, set1: Set[int], set2: Set[int]) -> Tuple[float, float]:
        """
        Calcule le coefficient de containment (inclusion).
        
        Mesure à quel point un ensemble est contenu dans l'autre.
        Utile pour détecter si un document est une version partielle d'un autre.
        
        Formule:
            C(A → B) = |A ∩ B| / |A|
            C(B → A) = |A ∩ B| / |B|
        
        Args:
            set1 (Set[int]): Premier ensemble
            set2 (Set[int]): Deuxième ensemble
            
        Returns:
            Tuple[float, float]: (containment de set1 dans set2, containment de set2 dans set1)
        """
        if not set1 or not set2:
            return (0.0, 0.0)
        
        intersection = set1 & set2
        
        # Containment dans les deux directions
        c1_to_2 = len(intersection) / len(set1)
        c2_to_1 = len(intersection) / len(set2)
        
        return (c1_to_2, c2_to_1)
    
    def cosine_similarity(self, set1: Set[int], set2: Set[int]) -> float:
        """
        Calcule la similarité cosinus entre deux ensembles.
        
        Note: Pour des ensembles binaires (présence/absence), 
        la similarité cosinus est similaire à Jaccard mais avec
        une pondération différente.
        
        Formule:
            cos(A, B) = |A ∩ B| / sqrt(|A| * |B|)
        
        Args:
            set1 (Set[int]): Premier ensemble
            set2 (Set[int]): Deuxième ensemble
            
        Returns:
            float: Score de similarité cosinus (0.0 à 1.0)
        """
        if not set1 or not set2:
            return 0.0
        
        intersection = set1 & set2
        
        # Similarité cosinus
        similarity = len(intersection) / math.sqrt(len(set1) * len(set2))
        
        return similarity
    
    def dice_coefficient(self, set1: Set[int], set2: Set[int]) -> float:
        """
        Calcule le coefficient de Dice (Sørensen–Dice).
        
        Formule:
            Dice(A, B) = 2 * |A ∩ B| / (|A| + |B|)
        
        Propriétés:
            - Plus sensible aux éléments communs que Jaccard
            - Valeur entre 0.0 et 1.0
        
        Args:
            set1 (Set[int]): Premier ensemble
            set2 (Set[int]): Deuxième ensemble
            
        Returns:
            float: Coefficient de Dice (0.0 à 1.0)
        """
        if not set1 or not set2:
            return 0.0
        
        intersection = set1 & set2
        
        # Coefficient de Dice
        coefficient = (2 * len(intersection)) / (len(set1) + len(set2))
        
        return coefficient
    
    def is_plagiarism(self, similarity_score: float) -> bool:
        """
        Détermine s'il y a plagiat selon le seuil défini.
        
        Args:
            similarity_score (float): Score de similarité
            
        Returns:
            bool: True si plagiat détecté, False sinon
        """
        return similarity_score >= self.threshold
    
    def categorize_similarity(self, similarity_score: float) -> str:
        """
        Catégorise le niveau de similarité.
        
        Args:
            similarity_score (float): Score de similarité (0.0 à 1.0)
            
        Returns:
            str: Catégorie ('IDENTIQUE', 'TRÈS ÉLEVÉE', 'ÉLEVÉE', 'MODÉRÉE', 'FAIBLE', 'AUCUNE')
        """
        if similarity_score >= 0.95:
            return "IDENTIQUE"
        elif similarity_score >= 0.80:
            return "TRÈS ÉLEVÉE"
        elif similarity_score >= 0.60:
            return "ÉLEVÉE"
        elif similarity_score >= 0.40:
            return "MODÉRÉE"
        elif similarity_score >= 0.20:
            return "FAIBLE"
        else:
            return "AUCUNE"
    
    def detailed_comparison(self, set1: Set[int], set2: Set[int], 
                          label1: str = "Doc1", label2: str = "Doc2") -> dict:
        """
        Effectue une comparaison détaillée avec toutes les métriques.
        
        Args:
            set1 (Set[int]): Premier ensemble d'empreintes
            set2 (Set[int]): Deuxième ensemble d'empreintes
            label1 (str): Label du premier document
            label2 (str): Label du deuxième document
            
        Returns:
            dict: Dictionnaire avec toutes les métriques
        """
        # Calcul de toutes les métriques
        jaccard = self.jaccard_similarity(set1, set2)
        containment = self.containment(set1, set2)
        cosine = self.cosine_similarity(set1, set2)
        dice = self.dice_coefficient(set1, set2)
        
        # Statistiques
        intersection = set1 & set2
        union = set1 | set2
        
        result = {
            # Identifiants
            "doc1": label1,
            "doc2": label2,
            
            # Métriques de similarité
            "jaccard_similarity": jaccard,
            "cosine_similarity": cosine,
            "dice_coefficient": dice,
            "containment_1_to_2": containment[0],
            "containment_2_to_1": containment[1],
            
            # Catégorisation
            "category": self.categorize_similarity(jaccard),
            "is_plagiarism": self.is_plagiarism(jaccard),
            
            # Statistiques
            "set1_size": len(set1),
            "set2_size": len(set2),
            "intersection_size": len(intersection),
            "union_size": len(union),
            "unique_to_set1": len(set1 - set2),
            "unique_to_set2": len(set2 - set1),
        }
        
        return result
    
    def batch_compare(self, fingerprints_dict: dict) -> list:
        """
        Compare tous les documents par paires.
        
        Args:
            fingerprints_dict (dict): Dictionnaire {filename: Set[int]}
            
        Returns:
            list: Liste de résultats de comparaison triés par similarité
        """
        results = []
        filenames = list(fingerprints_dict.keys())
        
        # Comparaison par paires
        for i in range(len(filenames)):
            for j in range(i + 1, len(filenames)):
                file1 = filenames[i]
                file2 = filenames[j]
                
                comparison = self.detailed_comparison(
                    fingerprints_dict[file1],
                    fingerprints_dict[file2],
                    file1,
                    file2
                )
                
                results.append(comparison)
        
        # Trier par similarité décroissante
        results.sort(key=lambda x: x['jaccard_similarity'], reverse=True)
        
        return results


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def print_comparison_report(comparison: dict):
    """
    Affiche un rapport formaté de comparaison.
    
    Args:
        comparison (dict): Résultat de detailed_comparison()
    """
    print(f"\n{'='*70}")
    print(f"📊 RAPPORT DE COMPARAISON")
    print(f"{'='*70}")
    print(f"📄 Document 1: {comparison['doc1']}")
    print(f"📄 Document 2: {comparison['doc2']}")
    print(f"{'─'*70}")
    print(f"🎯 Similarité Jaccard:  {comparison['jaccard_similarity']:.2%}")
    print(f"📐 Similarité Cosinus:  {comparison['cosine_similarity']:.2%}")
    print(f"🎲 Coefficient Dice:    {comparison['dice_coefficient']:.2%}")
    print(f"{'─'*70}")
    print(f"📦 Taille Doc1:         {comparison['set1_size']} empreintes")
    print(f"📦 Taille Doc2:         {comparison['set2_size']} empreintes")
    print(f"🔗 Intersection:        {comparison['intersection_size']} empreintes")
    print(f"🔀 Union:               {comparison['union_size']} empreintes")
    print(f"{'─'*70}")
    print(f"📊 Catégorie:           {comparison['category']}")
    print(f"⚠️  Plagiat détecté:     {'OUI' if comparison['is_plagiarism'] else 'NON'}")
    print(f"{'='*70}\n")


def test_similarity():
    """
    Test simple du calculateur de similarité.
    """
    # Ensembles d'exemple
    set1 = {1, 2, 3, 4, 5}
    set2 = {3, 4, 5, 6, 7}
    set3 = {1, 2, 3, 4, 5}  # Identique à set1
    
    calculator = SimilarityCalculator(threshold=0.6)
    
    print("\n🧪 Tests de Similarité\n")
    
    # Test 1: Similarité partielle
    score1 = calculator.jaccard_similarity(set1, set2)
    print(f"Set1 vs Set2: {score1:.2%} - {calculator.categorize_similarity(score1)}")
    
    # Test 2: Similarité identique
    score2 = calculator.jaccard_similarity(set1, set3)
    print(f"Set1 vs Set3: {score2:.2%} - {calculator.categorize_similarity(score2)}")
    
    # Test 3: Comparaison détaillée
    comparison = calculator.detailed_comparison(set1, set2, "Doc1", "Doc2")
    print_comparison_report(comparison)


if __name__ == "__main__":
    test_similarity()
