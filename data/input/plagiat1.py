"""
Calculateur de factorielle - Version originale
"""

def factorielle(n):
    if n == 0 or n == 1:
        return 1
    return n * factorielle(n - 1)

def calculer_somme(liste):
    total = 0
    for element in liste:
        total += element
    return total

def main():
    print("Factorielle de 5:", factorielle(5))
    nombres = [1, 2, 3, 4, 5]
    print("Somme:", calculer_somme(nombres))

if __name__ == "__main__":
    main()
