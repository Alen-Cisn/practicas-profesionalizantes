"""
Test cases para el Analizador Histórico de Términos
Valida filtros, límites y funcionalidad básica del sistema
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para importar el módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from historical_term_analyzer import (
    Document, 
    InternetArchiveClient, 
    TextProcessor, 
    SessionMemory,
    HistoricalTermAnalyzer
)


class TestDocument(unittest.TestCase):
    """Test cases para la clase Document"""
    
    def setUp(self):
        self.test_date = datetime(2000, 6, 15)
        self.document = Document("test-id-123", "Test Document", self.test_date, 2000)
        
    def test_document_creation(self):
        """Probar creación básica de documento"""
        self.assertEqual(self.document.identifier, "test-id-123")
        self.assertEqual(self.document.title, "Test Document")
        self.assertEqual(self.document.year, 2000)
        self.assertEqual(self.document.date, self.test_date)
        
    def test_get_metadata(self):
        """Probar extracción de metadatos"""
        metadata = self.document.get_metadata()
        
        self.assertIn('identifier', metadata)
        self.assertIn('title', metadata)
        self.assertIn('year', metadata)
        self.assertIn('date', metadata)
        self.assertIn('content_length', metadata)
        
    def test_set_content(self):
        """Probar establecimiento de contenido"""
        test_content = "This is test content for the document."
        self.document.set_content(test_content)
        
        self.assertEqual(self.document.get_text(), test_content)
        self.assertEqual(len(self.document.text_content), len(test_content))


class TestTextProcessor(unittest.TestCase):
    """Test cases para la clase TextProcessor"""
    
    def setUp(self):
        self.processor = TextProcessor()
        
    def test_extract_terms_basic(self):
        """Probar extracción básica de términos"""
        text = "The quick brown fox jumps over the lazy dog."
        terms = self.processor.extract_terms(text)
        
        # Verificar que se excluyen stop words
        self.assertNotIn('the', terms)
        self.assertNotIn('over', terms)
        
        # Verificar que se incluyen palabras relevantes
        self.assertIn('quick', terms)
        self.assertIn('brown', terms)
        self.assertIn('jumps', terms)
        
    def test_extract_terms_empty(self):
        """Probar con texto vacío"""
        terms = self.processor.extract_terms("")
        self.assertEqual(terms, [])
        
    def test_extract_terms_case_insensitive(self):
        """Probar que la extracción sea case-insensitive"""
        text = "COMPUTER computer Computer"
        terms = self.processor.extract_terms(text)
        
        # Todos deberían convertirse a minúsculas
        expected_terms = ['computer', 'computer', 'computer']
        self.assertEqual(terms, expected_terms)
        
    def test_calculate_frequencies(self):
        """Probar cálculo de frecuencias"""
        # Crear documentos de prueba
        doc1 = Document("test1", "Test 1", datetime.now(), 2000)
        doc1.set_content("computer science technology")
        
        doc2 = Document("test2", "Test 2", datetime.now(), 2001)
        doc2.set_content("computer programming technology software")
        
        documents = [doc1, doc2]
        frequencies = self.processor.calculate_frequencies(documents)
        
        # Verificar frecuencias
        self.assertEqual(frequencies['computer'], 2)
        self.assertEqual(frequencies['technology'], 2)
        self.assertEqual(frequencies['science'], 1)
        self.assertEqual(frequencies['programming'], 1)
        
    def test_get_top_terms(self):
        """Probar obtención de términos principales"""
        frequencies = {
            'computer': 10,
            'technology': 8,
            'science': 6,
            'programming': 4,
            'software': 2
        }
        
        top_terms = self.processor.get_top_terms(frequencies, top_n=3)
        
        # Verificar orden y número correcto
        self.assertEqual(len(top_terms), 3)
        self.assertEqual(top_terms[0], ('computer', 10))
        self.assertEqual(top_terms[1], ('technology', 8))
        self.assertEqual(top_terms[2], ('science', 6))


class TestInternetArchiveClient(unittest.TestCase):
    """Test cases para la clase InternetArchiveClient"""
    
    def setUp(self):
        self.client = InternetArchiveClient(rate_limit_delay=0.1)  # Delay corto para tests
        
    def test_client_initialization(self):
        """Probar inicialización del cliente"""
        self.assertEqual(self.client.rate_limit_delay, 0.1)
        self.assertEqual(self.client.total_requests, 0)
        self.assertEqual(self.client.failed_requests, 0)
        
    def test_validate_english_content(self):
        """Probar validación de contenido en inglés"""
        
        # Texto en inglés
        english_text = """
        The Internet Archive is a digital library with the stated mission of 
        providing universal access to all knowledge. It provides permanent storage 
        for millions of free books, movies, music, television programs and more.
        """
        self.assertTrue(self.client.validate_english_content(english_text))
        
        # Texto muy corto
        short_text = "Hi there"
        self.assertFalse(self.client.validate_english_content(short_text))
        
        # Texto con muchos caracteres no latinos
        non_latin_text = "这是中文文本，不应该被识别为英文"
        self.assertFalse(self.client.validate_english_content(non_latin_text))
        
    def test_clean_text_content(self):
        """Probar limpieza de contenido textual"""
        dirty_content = """
        <html><body><h1>Title</h1>
        <p>This is a paragraph with content.</p>
        <div>Internet Archive Book Digitized by Google</div>
        
        
        <p>More content here.</p>
        </body></html>
        """
        
        clean_content = self.client._clean_text_content(dirty_content)
        
        # Verificar que se eliminaron tags HTML
        self.assertNotIn('<html>', clean_content)
        self.assertNotIn('<p>', clean_content)
        
        # Verificar que se eliminaron metadatos
        self.assertNotIn('Digitized by', clean_content)
        
        # Verificar que se mantiene contenido válido
        self.assertIn('paragraph with content', clean_content)
        
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Probar request exitoso"""
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'test': 'data'}
        mock_get.return_value = mock_response
        
        response = self.client._make_request('http://test.com')
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.total_requests, 1)
        
    @patch('requests.Session.get')
    def test_make_request_404(self, mock_get):
        """Probar request con error 404"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        response = self.client._make_request('http://test.com')
        
        self.assertIsNone(response)
        self.assertEqual(self.client.total_requests, 1)
        
    def test_document_validation(self):
        """Probar validación de documentos"""
        query_params = {
            'start_year': 1995,
            'end_year': 2005
        }
        
        # Documento válido
        valid_doc = Document("valid-test-123", "Valid Document", datetime(2000, 1, 1), 2000)
        self.assertTrue(self.client._validate_document(valid_doc, query_params))
        
        # Documento fuera de rango de años
        invalid_doc = Document("invalid-test-123", "Invalid Document", datetime(2010, 1, 1), 2010)
        self.assertFalse(self.client._validate_document(invalid_doc, query_params))
        
        # Documento con identificador inválido
        invalid_id_doc = Document("abc", "Short ID", datetime(2000, 1, 1), 2000)
        self.assertFalse(self.client._validate_document(invalid_id_doc, query_params))


class TestSessionMemory(unittest.TestCase):
    """Test cases para la clase SessionMemory"""
    
    def setUp(self):
        self.memory = SessionMemory()
        
    def test_initialization(self):
        """Probar inicialización de memoria de sesión"""
        self.assertEqual(len(self.memory.documents), 0)
        self.assertEqual(len(self.memory.frequencies), 0)
        self.assertEqual(len(self.memory.top_terms), 0)
        self.assertIsInstance(self.memory.start_time, datetime)
        
    def test_add_documents(self):
        """Probar agregado de documentos"""
        doc1 = Document("test1", "Test 1", datetime.now(), 2000)
        doc2 = Document("test2", "Test 2", datetime.now(), 2001)
        
        self.memory.add_documents([doc1, doc2])
        
        self.assertEqual(len(self.memory.documents), 2)
        self.assertEqual(self.memory.documents[0].identifier, "test1")
        self.assertEqual(self.memory.documents[1].identifier, "test2")
        
    def test_set_frequencies(self):
        """Probar establecimiento de frecuencias"""
        frequencies = {'computer': 10, 'science': 5}
        self.memory.set_frequencies(frequencies)
        
        self.assertEqual(self.memory.frequencies, frequencies)
        
    def test_get_summary(self):
        """Probar generación de resumen"""
        # Agregar datos de prueba
        doc = Document("test", "Test", datetime.now(), 2000)
        doc.set_content("test content")
        self.memory.add_documents([doc])
        
        self.memory.set_frequencies({'test': 1, 'content': 1})
        self.memory.set_top_terms([('test', 1), ('content', 1)])
        
        summary = self.memory.get_summary()
        
        self.assertEqual(summary['total_documents'], 1)
        self.assertEqual(summary['documents_with_content'], 1)
        self.assertEqual(summary['total_unique_terms'], 2)
        self.assertEqual(summary['top_terms_count'], 2)
        self.assertIn('elapsed_time_minutes', summary)


class TestIntegration(unittest.TestCase):
    """Test de integración para el sistema completo"""
    
    def setUp(self):
        self.analyzer = HistoricalTermAnalyzer(rate_limit_delay=0.1)
        
    @patch('historical_term_analyzer.InternetArchiveClient.search_items')
    @patch('historical_term_analyzer.InternetArchiveClient.download_text')
    def test_full_analysis_workflow(self, mock_download, mock_search):
        """Probar el flujo completo de análisis"""
        
        # Mock de documentos encontrados
        doc1 = Document("test1", "Computer Science", datetime(1999, 1, 1), 1999)
        doc2 = Document("test2", "Technology Today", datetime(2001, 1, 1), 2001)
        mock_search.return_value = [doc1, doc2]
        
        # Mock de contenido descargado
        mock_download.side_effect = [
            "Computer science is the study of algorithmic processes and computational systems.",
            "Technology has advanced rapidly in recent years with new innovations."
        ]
        
        # Ejecutar análisis
        results = self.analyzer.analyze_period(
            start_year=1995,
            end_year=2005,
            max_documents=10,
            language='eng'
        )
        
        # Verificar resultados
        self.assertNotIn('error', results)
        self.assertIn('summary', results)
        self.assertIn('top_terms', results)
        self.assertIn('frequencies', results)
        
        # Verificar que se procesaron documentos
        self.assertEqual(results['summary']['total_documents'], 2)
        
        # Verificar que se calcularon frecuencias
        self.assertGreater(len(results['frequencies']), 0)
        
        # Verificar términos principales
        self.assertGreater(len(results['top_terms']), 0)


class TestValidationAndLimits(unittest.TestCase):
    """Tests específicos para validaciones y límites del sistema"""
    
    def setUp(self):
        self.client = InternetArchiveClient()
        
    def test_rate_limiting_parameters(self):
        """Probar parámetros de rate limiting"""
        # Valor por defecto
        default_client = InternetArchiveClient()
        self.assertEqual(default_client.rate_limit_delay, 4.0)
        
        # Valor personalizado
        custom_client = InternetArchiveClient(rate_limit_delay=2.0)
        self.assertEqual(custom_client.rate_limit_delay, 2.0)
        
    def test_document_limits_validation(self):
        """Probar validación de límites de documentos"""
        query_params = {'start_year': 1995, 'end_year': 2005}
        
        # Simular búsqueda con límites
        with patch.object(self.client, '_search_page') as mock_search_page:
            mock_search_page.return_value = [
                Document(f"test-{i}", f"Test {i}", datetime(2000, 1, 1), 2000)
                for i in range(10)
            ]
            
            # Buscar con límite de 25 documentos
            results = self.client.search_items(query_params, max_results=25)
            
            # Verificar que respeta el límite
            self.assertLessEqual(len(results), 25)
            
    def test_english_validation_edge_cases(self):
        """Probar validación de inglés con casos límite"""
        
        # Texto mixto (inglés con algunas palabras en otros idiomas)
        mixed_text = """
        This is mostly English text with some français words mixed in.
        The document discusses computer science and technology topics.
        There are occasional deutsche Wörter but the main language is English.
        """
        self.assertTrue(self.client.validate_english_content(mixed_text))
        
        # Texto técnico con términos especializados
        technical_text = """
        The algorithm implements a binary search tree with O(log n) complexity.
        Database normalization follows the principles of ACID transactions.
        Machine learning models utilize gradient descent optimization techniques.
        """
        self.assertTrue(self.client.validate_english_content(technical_text))
        
        # Texto con muchos números y símbolos
        numeric_text = """
        Data: 123, 456, 789
        Results: $50.25, €30.15, £25.99
        Percentage: 75.5% improvement over baseline
        """
        # Este debería fallar por falta de palabras en inglés suficientes
        self.assertFalse(self.client.validate_english_content(numeric_text))


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)