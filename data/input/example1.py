"""
Exemple de fichier Python 1
Programme calculant la factorielle d'un nombre
"""

def factorial(n):
    """Calcule la factorielle de n"""
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

def main():
    number = 5
    result = factorial(number)
    print(f"La factorielle de {number} est {result}")

if __name__ == "__main__":
    main()
