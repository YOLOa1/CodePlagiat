"""
Calcul de Fibonacci - Version 2
Auteur: Étudiant 2
"""

def calculate_fibonacci(num):
    """Retourne le nombre de Fibonacci"""
    if num <= 1:
        return num
    else:
        return calculate_fibonacci(num-1) + calculate_fibonacci(num-2)

def run():
    """Programme principal"""
    print("Nombres de Fibonacci:")
    for index in range(10):
        value = calculate_fibonacci(index)
        print(f"Fibonacci({index}) = {value}")

if __name__ == "__main__":
    run()
