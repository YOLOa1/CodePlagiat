"""
Exemple de fichier Python 3
Programme de tri à bulles
"""

def bubble_sort(arr):
    """Implémentation du tri à bulles"""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def main():
    data = [64, 34, 25, 12, 22, 11, 90]
    print(f"Tableau original: {data}")
    
    sorted_data = bubble_sort(data)
    print(f"Tableau trié: {sorted_data}")

if __name__ == "__main__":
    main()
