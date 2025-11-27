"""
Exemple de fichier Python 2
Programme calculant la factorielle (version légèrement modifiée)
"""

def calculate_factorial(num):
    """Calcule la factorielle d'un nombre"""
    if num == 0 or num == 1:
        return 1
    else:
        result = num * calculate_factorial(num - 1)
        return result

def run():
    n = 5
    factorial_result = calculate_factorial(n)
    print(f"Factorielle de {n} = {factorial_result}")

if __name__ == "__main__":
    run()
