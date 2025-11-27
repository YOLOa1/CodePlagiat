"""
Programme de calcul de la suite de Fibonacci
Auteur: Étudiant 1
"""

def fibonacci(n):
    """Calcule le n-ième nombre de Fibonacci"""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def main():
    """Fonction principale"""
    print("Suite de Fibonacci:")
    for i in range(10):
        result = fibonacci(i)
        print(f"F({i}) = {result}")

if __name__ == "__main__":
    main()
