"""
============================================
Extracteur AST (Abstract Syntax Tree)
============================================
Module pour extraire la structure syntaxique des fichiers sources.
Supporte Python, C++, et Java via tree-sitter.

Utilisation:
    extractor = ASTExtractor()
    tokens = extractor.extract_tokens(code, 'python')
============================================
"""

import hashlib
from typing import List, Optional


class ASTExtractor:
    """
    Classe pour extraire les tokens AST depuis du code source.
    
    Utilise tree-sitter pour parser différents langages et extraire
    les nœuds syntaxiques importants (fonctions, classes, variables, etc.)
    """
    
    def __init__(self):
        """
        Initialise l'extracteur avec les parsers pour chaque langage.
        
        Note: Dans une implémentation complète avec tree-sitter,
        il faudrait compiler les grammaires. Ici, nous utilisons
        une approche simplifiée pour la démonstration.
        """
        self.supported_languages = ['python', 'cpp', 'java']
        
    def extract_tokens(self, source_code: str, language: str) -> List[str]:
        """
        Extrait les tokens significatifs depuis le code source.
        
        Args:
            source_code (str): Code source à analyser
            language (str): Langage du code ('python', 'cpp', 'java')
            
        Returns:
            List[str]: Liste de tokens normalisés
        """
        if language not in self.supported_languages:
            raise ValueError(f"Langage non supporté: {language}")
        
        # Normalisation du code
        normalized_code = self._normalize_code(source_code)
        
        # Extraction selon le langage
        if language == 'python':
            return self._extract_python_tokens(normalized_code)
        elif language == 'cpp':
            return self._extract_cpp_tokens(normalized_code)
        elif language == 'java':
            return self._extract_java_tokens(normalized_code)
        
        return []
    
    def _normalize_code(self, code: str) -> str:
        """
        Normalise le code source (suppression des commentaires, espaces, etc.)
        
        Args:
            code (str): Code source brut
            
        Returns:
            str: Code normalisé
        """
        # Suppression des lignes vides
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        # TODO: Amélioration possible
        # - Supprimer les commentaires
        # - Normaliser les noms de variables
        # - Supprimer les chaînes littérales
        
        return '\n'.join(lines)
    
    def _extract_python_tokens(self, code: str) -> List[str]:
        """
        Extrait les tokens d'un code Python.
        
        Stratégie simplifiée:
        - Extraction des mots-clés et identifiants
        - Ignorer les littéraux (nombres, chaînes)
        
        Args:
            code (str): Code Python normalisé
            
        Returns:
            List[str]: Tokens Python
        """
        try:
            import ast
            import tokenize
            from io import BytesIO
            
            tokens = []
            
            # Tokenization Python native
            code_bytes = code.encode('utf-8')
            readline = BytesIO(code_bytes).readline
            
            for tok in tokenize.tokenize(readline):
                # Garder les mots-clés et identifiants
                if tok.type == tokenize.NAME:
                    tokens.append(tok.string)
                # Garder les opérateurs importants
                elif tok.type == tokenize.OP and tok.string in ['+', '-', '*', '/', '=', '==', '!=', '<', '>']:
                    tokens.append(tok.string)
            
            return tokens
            
        except Exception as e:
            # Fallback: découpage simple par mots
            return self._simple_tokenize(code)
    
    def _extract_cpp_tokens(self, code: str) -> List[str]:
        """
        Extrait les tokens d'un code C++.
        
        Note: Implémentation améliorée pour capturer la structure du code.
        
        Args:
            code (str): Code C++ normalisé
            
        Returns:
            List[str]: Tokens C++
        """
        import re
        
        # Mots-clés C++ courants à préserver
        cpp_keywords = {
            'int', 'float', 'double', 'char', 'void', 'bool', 'long', 'short',
            'class', 'struct', 'enum', 'union', 'typedef',
            'public', 'private', 'protected', 'virtual', 'static', 'const',
            'return', 'if', 'else', 'switch', 'case', 'default', 'break',
            'for', 'while', 'do', 'continue', 'goto',
            'namespace', 'using', 'include', 'define', 'template', 'typename',
            'new', 'delete', 'this', 'true', 'false', 'nullptr',
            'try', 'catch', 'throw', 'operator', 'friend', 'inline'
        }
        
        # Types STL courants
        stl_types = {'vector', 'string', 'map', 'set', 'list', 'queue', 'stack', 'pair'}
        
        # Opérateurs à capturer
        operators = {'+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=', 
                    '&&', '||', '!', '&', '|', '^', '<<', '>>', '++', '--'}
        
        tokens = []
        
        # Supprimer les commentaires
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)  # Commentaires //
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)   # Commentaires /* */
        
        # Supprimer les directives préprocesseur (sauf include)
        code = re.sub(r'#(?!include)\w+.*?$', '', code, flags=re.MULTILINE)
        
        # Supprimer les strings littérales pour ne pas polluer les tokens
        code = re.sub(r'"[^"]*"', '', code)
        
        # Extraire tous les mots et symboles
        pattern = r'\w+|[+\-*/%=<>!&|^]+'
        words = re.findall(pattern, code)
        
        for word in words:
            # Ignorer les nombres purs
            if word.isdigit():
                continue
            
            # Garder les mots-clés
            if word in cpp_keywords:
                tokens.append(word)
            # Garder les types STL
            elif word in stl_types:
                tokens.append(word)
            # Garder les opérateurs
            elif word in operators:
                tokens.append(word)
            # Pour les identifiants, ne garder que les fonctions standards connues
            elif word in {'cout', 'cin', 'endl', 'swap', 'push_back', 'pop_back', 
                         'size', 'empty', 'clear', 'begin', 'end', 'sort', 'find',
                         'insert', 'erase', 'printf', 'scanf', 'malloc', 'free'}:
                tokens.append(word)
            # Ignorer les identifiants personnalisés (noms de variables/fonctions)
        
        return tokens
    
    def _extract_java_tokens(self, code: str) -> List[str]:
        """
        Extrait les tokens d'un code Java.
        
        Note: Implémentation améliorée pour capturer la structure du code.
        
        Args:
            code (str): Code Java normalisé
            
        Returns:
            List[str]: Tokens Java
        """
        import re
        
        # Mots-clés Java courants à préserver
        java_keywords = {
            'public', 'private', 'protected', 'static', 'final', 'abstract', 'synchronized',
            'class', 'interface', 'enum', 'extends', 'implements', 'package', 'import',
            'void', 'int', 'long', 'float', 'double', 'boolean', 'char', 'byte', 'short',
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break',
            'continue', 'return', 'new', 'this', 'super', 'null', 'true', 'false',
            'try', 'catch', 'finally', 'throw', 'throws', 'assert',
            'native', 'strictfp', 'transient', 'volatile', 'instanceof'
        }
        
        # Types courants Java
        java_types = {'String', 'Integer', 'Long', 'Float', 'Double', 'Boolean', 
                     'Character', 'Object', 'ArrayList', 'HashMap', 'List', 'Map', 
                     'Set', 'Collection', 'Iterator'}
        
        # Opérateurs à capturer
        operators = {'+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
                    '&&', '||', '!', '&', '|', '^', '<<', '>>', '++', '--'}
        
        tokens = []
        
        # Supprimer les commentaires
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)  # Commentaires //
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)   # Commentaires /* */
        
        # Supprimer les strings littérales
        code = re.sub(r'"[^"]*"', '', code)
        
        # Supprimer les annotations (@Override, etc.)
        code = re.sub(r'@\w+', '', code)
        
        # Extraire tous les mots et symboles
        pattern = r'\w+|[+\-*/%=<>!&|^]+'
        words = re.findall(pattern, code)
        
        for word in words:
            # Ignorer les nombres purs
            if word.isdigit():
                continue
            
            # Garder les mots-clés
            if word in java_keywords:
                tokens.append(word)
            # Garder les types Java courants
            elif word in java_types:
                tokens.append(word)
            # Garder les opérateurs
            elif word in operators:
                tokens.append(word)
            # Pour les identifiants, ne garder que les méthodes standards connues
            elif word in {'print', 'println', 'length', 'size', 'add', 'remove', 
                         'get', 'set', 'contains', 'isEmpty', 'clear', 'sort',
                         'equals', 'toString', 'hashCode', 'compareTo', 'main'}:
                tokens.append(word)
            # Ignorer les identifiants personnalisés (noms de variables/fonctions/classes)
        
        return tokens
    
    def _simple_tokenize(self, code: str) -> List[str]:
        """
        Tokenisation simple par découpage sur les espaces et symboles.
        
        Args:
            code (str): Code source
            
        Returns:
            List[str]: Tokens
        """
        import re
        
        # Découpage sur les délimiteurs courants
        tokens = re.findall(r'\w+|[+\-*/=<>!&|]', code)
        
        return tokens
    
    def compute_ast_hash(self, tokens: List[str]) -> str:
        """
        Calcule un hash MD5 de la liste de tokens.
        Utile pour comparaison rapide.
        
        Args:
            tokens (List[str]): Liste de tokens
            
        Returns:
            str: Hash MD5 hexadécimal
        """
        token_string = ' '.join(tokens)
        return hashlib.md5(token_string.encode()).hexdigest()


# ============================================
# FONCTION UTILITAIRE POUR TESTS
# ============================================
def test_extractor():
    """
    Test simple de l'extracteur.
    """
    extractor = ASTExtractor()
    
    # Test Python
    python_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
    tokens = extractor.extract_tokens(python_code, 'python')
    print(f"Tokens Python: {tokens[:10]}")
    
    # Test C++
    cpp_code = """
int main() {
    int x = 10;
    return 0;
}
"""
    tokens = extractor.extract_tokens(cpp_code, 'cpp')
    print(f"Tokens C++: {tokens[:10]}")


if __name__ == "__main__":
    test_extractor()
