"""
Implémentation d'un tri à bulles
Auteur: Étudiant 3
"""

def bubble_sort(arr):
    """Trie un tableau avec l'algorithme de tri à bulles"""
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

def main():
    """Fonction principale"""
    data = [64, 34, 25, 12, 22, 11, 90]
    print("Tableau original:", data)
    sorted_data = bubble_sort(data.copy())
    print("Tableau trié:", sorted_data)

if __name__ == "__main__":
    main()
