#!/usr/bin/env python3
"""
Analizador Histórico de Términos
Permite analizar las palabras más usadas en documentos web históricos durante períodos específicos
utilizando Internet Archive API.

Autor: Sistema de IA
Fecha: 2025-09-25
"""

import requests
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlencode
import logging
from collections import Counter
import csv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Document:
    """
    Modelo de datos para representar un documento web histórico
    """
    def __init__(self, identifier: str, title: str, date: datetime, year: int):
        self.identifier = identifier
        self.title = title
        self.date = date
        self.year = year
        self.text_content = ""
        self.metadata = {}
        
    def get_metadata(self) -> Dict:
        """Retornar metadatos estructurados"""
        return {
            'identifier': self.identifier,
            'title': self.title,
            'date': self.date.isoformat() if self.date else None,
            'year': self.year,
            'content_length': len(self.text_content),
            **self.metadata
        }
        
    def get_text(self) -> str:
        """Retornar contenido textual limpio"""
        return self.text_content
        
    def set_content(self, content: str):
        """Establecer contenido textual"""
        self.text_content = content


class InternetArchiveClient:
    """
    Cliente para interactuar con Internet Archive API
    Maneja búsqueda, descarga y procesamiento de documentos web históricos
    """
    
    # URLs base de Internet Archive
    SEARCH_API = "https://archive.org/advancedsearch.php"
    CDX_API = "http://web.archive.org/cdx/search/cdx"
    DOWNLOAD_BASE = "https://archive.org/download/"
    METADATA_API = "https://archive.org/metadata/"
    
    def __init__(self, rate_limit_delay: float = 4.0):
        """
        Inicializar cliente con configuración de rate limiting
        
        Args:
            rate_limit_delay: Tiempo de espera entre requests en segundos
        """
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HistoricalTermAnalyzer/1.0 (Educational Research Project)'
        })
        
        # Estadísticas
        self.total_requests = 0
        self.failed_requests = 0
        
    def search_items(self, query_params: Dict, max_results: int = 600) -> List[Document]:
        """
        Buscar documentos web históricos con filtros
        
        Args:
            query_params: Dict con start_year, end_year, language, terms
            max_results: Límite máximo de documentos
            
        Returns:
            Lista de objetos Document con metadatos
        """
        logger.info(f"Iniciando búsqueda con parámetros: {query_params}")
        
        documents = []
        rows_per_page = 50
        total_pages = (max_results + rows_per_page - 1) // rows_per_page
        
        for page in range(total_pages):
            try:
                page_documents = self._search_page(query_params, page, rows_per_page)
                documents.extend(page_documents)
                
                logger.info(f"Página {page + 1}/{total_pages}: {len(page_documents)} documentos obtenidos")
                
                if len(documents) >= max_results:
                    documents = documents[:max_results]
                    break
                    
                # Rate limiting entre páginas
                self._handle_rate_limiting()
                
            except Exception as e:
                logger.error(f"Error en página {page + 1}: {e}")
                self.failed_requests += 1
                continue
                
        logger.info(f"Búsqueda completada: {len(documents)} documentos encontrados")
        return documents
        
    def _search_page(self, query_params: Dict, page: int, rows: int) -> List[Document]:
        """Buscar una página específica de resultados"""
        
        # Construir query de búsqueda
        query_parts = []
        
        # Filtros obligatorios
        query_parts.append("mediatype:web")
        query_parts.append("collection:web")
        
        # Filtro temporal
        start_year = query_params.get('start_year', 1995)
        end_year = query_params.get('end_year', 2005)
        query_parts.append(f"date:[{start_year}-01-01 TO {end_year}-12-31]")
        
        # Filtro de idioma (si se especifica)
        if query_params.get('language') == 'eng':
            query_parts.append("language:eng")
            
        # Términos de búsqueda (opcional)
        terms = query_params.get('terms')
        if terms:
            if isinstance(terms, list):
                terms_query = " OR ".join(f'"{term}"' for term in terms)
                query_parts.append(f"({terms_query})")
            else:
                query_parts.append(f'"{terms}"')
        
        query_string = " AND ".join(query_parts)
        
        # Parámetros de la API
        params = {
            'q': query_string,
            'fl': 'identifier,title,date,year,addeddate,language',
            'sort': 'date desc',
            'rows': rows,
            'page': page + 1,
            'output': 'json',
            'save': 'yes'
        }
        
        logger.debug(f"Query: {query_string}")
        
        response = self._make_request(self.SEARCH_API, params)
        if not response:
            return []
            
        # Procesar resultados
        documents = []
        data = response.json()
        
        if 'response' in data and 'docs' in data['response']:
            for doc in data['response']['docs']:
                try:
                    document = self._create_document_from_search_result(doc)
                    if document and self._validate_document(document, query_params):
                        documents.append(document)
                except Exception as e:
                    logger.warning(f"Error procesando documento {doc.get('identifier', 'unknown')}: {e}")
                    continue
                    
        return documents
        
    def _create_document_from_search_result(self, doc_data: Dict) -> Optional[Document]:
        """Crear objeto Document desde resultado de búsqueda"""
        try:
            identifier = doc_data.get('identifier')
            if not identifier:
                return None
                
            title = doc_data.get('title', 'Sin título')
            if isinstance(title, list):
                title = title[0]
                
            # Procesar fecha
            date_str = doc_data.get('date')
            date_obj = None
            year = None
            
            if date_str:
                try:
                    if isinstance(date_str, list):
                        date_str = date_str[0]
                    date_obj = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
                    year = date_obj.year
                except:
                    year = doc_data.get('year')
                    if year:
                        year = int(str(year)[:4])
                        
            document = Document(identifier, title, date_obj, year)
            document.metadata = {
                'addeddate': doc_data.get('addeddate'),
                'language': doc_data.get('language'),
                'source_api': 'search'
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Error creando documento: {e}")
            return None
            
    def _validate_document(self, document: Document, query_params: Dict) -> bool:
        """Validar que el documento cumple con los criterios"""
        
        # Validar año
        start_year = query_params.get('start_year', 1995)
        end_year = query_params.get('end_year', 2005)
        
        if document.year:
            if document.year < start_year or document.year > end_year:
                return False
                
        # Validar identificador válido
        if not document.identifier or len(document.identifier) < 5:
            return False
            
        return True
        
    def download_text(self, identifier: str) -> str:
        """
        Descargar contenido textual de un documento específico
        
        Args:
            identifier: Identificador único del documento
            
        Returns:
            Contenido textual del documento
        """
        logger.debug(f"Descargando contenido para: {identifier}")
        
        # Intentar diferentes formatos de archivo
        text_formats = [
            f"{identifier}.txt",
            f"{identifier}_djvu.txt", 
            f"{identifier}_text.pdf",
            f"{identifier}.html"
        ]
        
        for filename in text_formats:
            try:
                content = self._download_file_content(identifier, filename)
                if content and len(content.strip()) > 100:  # Contenido mínimo
                    # Validar idioma inglés
                    if self.validate_english_content(content):
                        return self._clean_text_content(content)
                        
            except Exception as e:
                logger.debug(f"Error descargando {filename}: {e}")
                continue
                
        # Si no se encontró contenido, intentar via metadata API
        try:
            return self._get_text_via_metadata_api(identifier)
        except Exception as e:
            logger.warning(f"No se pudo descargar contenido para {identifier}: {e}")
            return ""
            
    def _download_file_content(self, identifier: str, filename: str) -> str:
        """Descargar contenido de un archivo específico"""
        url = f"{self.DOWNLOAD_BASE}{identifier}/{filename}"
        
        response = self._make_request(url, timeout=30)
        if response and response.status_code == 200:
            # Detectar encoding
            content = response.content
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('latin-1')
                except UnicodeDecodeError:
                    text = content.decode('utf-8', errors='ignore')
                    
            return text
            
        return ""
        
    def _get_text_via_metadata_api(self, identifier: str) -> str:
        """Obtener texto a través de la API de metadatos"""
        url = f"{self.METADATA_API}{identifier}"
        
        response = self._make_request(url)
        if not response:
            return ""
            
        try:
            data = response.json()
            # Extraer descripción o contenido relevante
            metadata = data.get('metadata', {})
            description = metadata.get('description', '')
            
            if isinstance(description, list):
                description = ' '.join(description)
                
            return str(description)
            
        except Exception as e:
            logger.debug(f"Error procesando metadata API: {e}")
            return ""
            
    def validate_english_content(self, text: str) -> bool:
        """
        Validar que el contenido esté en inglés usando patrones básicos
        
        Args:
            text: Texto a validar
            
        Returns:
            True si el contenido parece estar en inglés
        """
        if len(text.strip()) < 50:
            return False
            
        # Tomar muestra del texto para análisis
        sample = text[:1000].lower()
        
        # Palabras comunes en inglés
        english_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
            'who', 'when', 'where', 'why', 'how', 'is', 'are', 'was', 'were', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'a', 'an'
        }
        
        # Contar palabras en inglés
        words = re.findall(r'\b[a-zA-Z]+\b', sample)
        if len(words) < 10:
            return False
            
        english_count = sum(1 for word in words if word.lower() in english_words)
        english_ratio = english_count / len(words)
        
        # Verificar caracteres no latinos (indicativo de otros idiomas)
        non_latin_chars = re.findall(r'[^\x00-\x7F]', sample)
        non_latin_ratio = len(non_latin_chars) / len(sample) if len(sample) > 0 else 1.0
        
        # Criterios más permisivos para contenido técnico
        # - Ratio de palabras inglesas más bajo (0.1 en lugar de 0.15)
        # - Ratio de caracteres no latinos más alto (0.1 en lugar de 0.05)
        return english_ratio > 0.1 and non_latin_ratio < 0.1
        
    def _clean_text_content(self, content: str) -> str:
        """Limpiar contenido textual de HTML y metadatos"""
        
        # Eliminar HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Eliminar metadatos comunes
        content = re.sub(r'Internet Archive.*?Book Digitized.*?Google', '', content, flags=re.DOTALL)
        content = re.sub(r'Digitized by.*?Internet Archive', '', content)
        
        # Limpiar espacios y líneas vacías
        content = re.sub(r'\n\s*\n', '\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Eliminar líneas muy cortas (probablemente metadata)
        lines = content.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 20]
        
        return '\n'.join(cleaned_lines)
        
    def _make_request(self, url: str, params: Dict = None, timeout: int = 30) -> Optional[requests.Response]:
        """Realizar request HTTP con manejo de errores y rate limiting"""
        
        self.total_requests += 1
        
        try:
            if params:
                if '?' in url:
                    url += '&' + urlencode(params)
                else:
                    url += '?' + urlencode(params)
                    
            response = self.session.get(url, timeout=timeout)
            
            # Manejar códigos de error específicos
            if response.status_code == 429:  # Too Many Requests
                logger.warning("Rate limit exceeded, esperando...")
                time.sleep(self.rate_limit_delay * 2)
                return self._make_request(url, timeout=timeout)
                
            elif response.status_code == 503:  # Service Unavailable
                logger.warning("Servicio no disponible, reintentando...")
                time.sleep(self.rate_limit_delay)
                return self.session.get(url, timeout=timeout)
                
            elif response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} para {url}")
                return None
                
            return response
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout para {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Error de conexión para {url}")
            time.sleep(self.rate_limit_delay)
            return None
        except Exception as e:
            logger.error(f"Error en request: {e}")
            return None
            
    def _handle_rate_limiting(self):
        """Implementar delays entre requests"""
        time.sleep(self.rate_limit_delay)
        
    def get_stats(self) -> Dict:
        """Obtener estadísticas del cliente"""
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.total_requests - self.failed_requests) / max(self.total_requests, 1) * 100
        }


class TextProcessor:
    """
    Procesador de texto para análisis de frecuencias
    """
    
    # Stop words en inglés - lista básica para preservar términos relevantes
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 
        'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was',
        'will', 'with', 'this', 'but', 'they', 'have', 'had', 'what',
        'said', 'each', 'which', 'do', 'how', 'their', 'if', 'up', 'out', 'many',
        'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like',
        'into', 'him', 'time', 'two', 'more', 'very', 'when', 'come', 'may',
        'only', 'think', 'now', 'you', 'his', 'your', 'here', 'me', 'should', 
        'could', 'been', 'than', 'who', 'just', 'where', 'most', 'us', 'much', 
        'go', 'being', 'over', 'such', 'our', 'made', 'can', 'get', 'am', 'way', 
        'too', 'any', 'day', 'same', 'right', 'under', 'while', 'might',
        'old', 'year', 'off', 'since', 'against', 'back', 'take', 'part', 'used', 
        'use', 'during', 'without', 'again', 'around', 'however', 'why', 'turn', 
        'put', 'end', 'does', 'another', 'well', 'must', 'even', 'give',
        'means', 'different', 'move', 'did', 'no', 'my', 'know', 'than',
        'first', 'down', 'side', 'now', 'find', 'own', 'should', 'found',
        'still', 'between', 'keep', 'never', 'let', 'saw', 'far', 'left', 'late', 
        'run', 'don', 'press', 'close', 'night', 'real', 'few', 'took', 'once', 
        'hear', 'cut', 'sure', 'watch', 'seem', 'together', 'next', 'got', 'walk',
        'always', 'those', 'both', 'often', 'until', 'care', 'second', 'enough',
        'ready', 'above', 'ever', 'though', 'feel', 'talk', 'soon', 'got',
        'direct', 'leave', 'told', 'knew', 'pass', 'top', 'heard', 'best', 'hour',
        'better', 'hundred', 'five', 'remember', 'step', 'early', 'hold', 'reach',
        'fast', 'listen', 'six', 'less', 'ten', 'simple', 'several', 'toward',
        'lay', 'pattern', 'slow', 'serve', 'appear', 'pull', 'cold', 'notice',
        'fine', 'certain', 'fly', 'fall', 'lead', 'cry', 'dark', 'note', 'wait',
        'plan', 'rest', 'able', 'done', 'stood', 'front', 'week', 'gave',
        'oh', 'develop', 'warm', 'free', 'minute', 'special', 'behind', 'clear',
        'produce', 'nothing', 'stay', 'full', 'force', 'decide', 'deep',
        'busy', 'record', 'common', 'possible', 'dry', 'ago', 'ran', 'check',
        'hot', 'miss', 'brought', 'heat', 'yes', 'fill', 'among'
    }
    
    def __init__(self):
        """Inicializar procesador de texto"""
        self.word_pattern = re.compile(r'\b[a-zA-Z]{3,}\b')  # Solo palabras de 3+ letras
        
    def extract_terms(self, text: str) -> List[str]:
        """
        Extraer términos relevantes del texto
        
        Args:
            text: Texto a procesar
            
        Returns:
            Lista de términos limpios
        """
        if not text:
            return []
            
        # Convertir a minúsculas
        text = text.lower()
        
        # Extraer palabras (2+ caracteres para incluir términos como "to", "in")
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        
        # Filtrar stop words y limpiar términos
        terms = []
        for word in words:
            if word not in self.STOP_WORDS and len(word) >= 2:
                # Limpiar caracteres especiales adicionales
                clean_word = re.sub(r'[^\w]', '', word)
                if len(clean_word) >= 2:
                    terms.append(clean_word)
                    
        return terms
        
    def calculate_frequencies(self, documents_or_text) -> Dict[str, int]:
        """
        Calcular frecuencias de términos en documentos o texto
        
        Args:
            documents_or_text: Lista de documentos o texto directo
            
        Returns:
            Diccionario con frecuencias de términos
        """
        all_terms = []
        
        # Manejar tanto documentos como texto directo
        if isinstance(documents_or_text, str):
            # Caso: texto directo
            terms = self.extract_terms(documents_or_text)
            all_terms.extend(terms)
        elif isinstance(documents_or_text, list):
            # Caso: lista de documentos
            logger.info(f"Calculando frecuencias para {len(documents_or_text)} documentos")
            processed_docs = 0
            
            for doc in documents_or_text:
                if hasattr(doc, 'text_content') and doc.text_content:
                    terms = self.extract_terms(doc.text_content)
                    all_terms.extend(terms)
                    processed_docs += 1
                    
            logger.info(f"Procesados {processed_docs} documentos con contenido")
        
        logger.info(f"Total de términos extraídos: {len(all_terms)}")
        
        # Calcular frecuencias
        frequencies = Counter(all_terms)
        
        return dict(frequencies)
        
    def get_top_terms(self, frequencies: Dict[str, int], top_n: int = 50) -> List[tuple]:
        """
        Obtener los términos más frecuentes
        
        Args:
            frequencies: Diccionario de frecuencias
            top_n: Número de términos principales a retornar
            
        Returns:
            Lista de tuplas (término, frecuencia) ordenada por frecuencia
        """
        return Counter(frequencies).most_common(top_n)


class SessionMemory:
    """
    Memoria temporal para la sesión de análisis
    """
    
    def __init__(self):
        """Inicializar memoria de sesión"""
        self.documents = []
        self.frequencies = {}
        self.top_terms = []
        self.session_stats = {}
        self.start_time = datetime.now()
        
    def add_documents(self, documents: List[Document]):
        """Agregar documentos a la memoria"""
        self.documents.extend(documents)
        
    def set_frequencies(self, frequencies: Dict[str, int]):
        """Establecer frecuencias calculadas"""
        self.frequencies = frequencies
        
    def set_top_terms(self, top_terms: List[tuple]):
        """Establecer términos principales"""
        self.top_terms = top_terms
        
    def update_stats(self, stats: Dict):
        """Actualizar estadísticas de la sesión"""
        self.session_stats.update(stats)
        
    def get_summary(self) -> Dict:
        """Obtener resumen de la sesión"""
        elapsed_time = datetime.now() - self.start_time
        
        return {
            'total_documents': len(self.documents),
            'documents_with_content': len([d for d in self.documents if d.text_content]),
            'total_unique_terms': len(self.frequencies),
            'top_terms_count': len(self.top_terms),
            'elapsed_time_minutes': elapsed_time.total_seconds() / 60,
            'session_stats': self.session_stats
        }


class Exporter:
    """
    Exportador de resultados a diferentes formatos
    """
    
    @staticmethod
    def export_to_csv(top_terms: List[tuple], filename: str):
        """Exportar términos principales a CSV"""
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Término', 'Frecuencia'])
            
            for term, freq in top_terms:
                writer.writerow([term, freq])
                
        logger.info(f"Resultados exportados a: {filename}")
        
    @staticmethod
    def export_to_json(data: Dict, filename: str):
        """Exportar datos completos a JSON"""
        
        # Serializar documentos
        if 'documents' in data:
            serialized_docs = []
            for doc in data['documents']:
                doc_data = doc.get_metadata()
                doc_data['content_preview'] = doc.get_text()[:500] + '...' if len(doc.get_text()) > 500 else doc.get_text()
                serialized_docs.append(doc_data)
            data['documents'] = serialized_docs
            
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False, default=str)
            
        logger.info(f"Datos completos exportados a: {filename}")


class Visualizer:
    """
    Generador de visualizaciones básicas
    """
    
    @staticmethod
    def print_top_terms(top_terms: List[tuple], top_n: int = 20):
        """Imprimir términos principales en consola"""
        
        print(f"\n{'='*50}")
        print(f"TOP {top_n} TÉRMINOS MÁS FRECUENTES")
        print(f"{'='*50}")
        
        for i, (term, freq) in enumerate(top_terms[:top_n], 1):
            print(f"{i:2d}. {term:<20} {freq:>6} ocurrencias")
            
    @staticmethod
    def print_summary(summary: Dict):
        """Imprimir resumen de la sesión"""
        
        print(f"\n{'='*50}")
        print(f"RESUMEN DE LA SESIÓN")
        print(f"{'='*50}")
        
        print(f"Documentos totales: {summary['total_documents']}")
        print(f"Documentos con contenido: {summary['documents_with_content']}")
        print(f"Términos únicos encontrados: {summary['total_unique_terms']}")
        print(f"Tiempo transcurrido: {summary['elapsed_time_minutes']:.1f} minutos")
        
        if 'session_stats' in summary:
            stats = summary['session_stats']
            if 'success_rate' in stats:
                print(f"Tasa de éxito de requests: {stats['success_rate']:.1f}%")


class HistoricalTermAnalyzer:
    """
    Orquestador principal del sistema de análisis histórico de términos
    """
    
    def __init__(self, rate_limit_delay: float = 4.0):
        """
        Inicializar analizador histórico
        
        Args:
            rate_limit_delay: Delay entre requests a Internet Archive
        """
        self.client = InternetArchiveClient(rate_limit_delay)
        self.processor = TextProcessor()
        self.memory = SessionMemory()
        self.exporter = Exporter()
        self.visualizer = Visualizer()
        
    def analyze_period(self, 
                      start_year: int, 
                      end_year: int, 
                      max_documents: int = 600,
                      language: str = 'eng',
                      search_terms: Optional[List[str]] = None) -> Dict:
        """
        Analizar términos en un período histórico específico
        
        Args:
            start_year: Año de inicio del período
            end_year: Año de fin del período
            max_documents: Número máximo de documentos a analizar
            language: Idioma de los documentos ('eng' para inglés)
            search_terms: Términos específicos a buscar (opcional)
            
        Returns:
            Diccionario con resultados del análisis
        """
        
        logger.info(f"Iniciando análisis histórico: {start_year}-{end_year}")
        logger.info(f"Parámetros: max_docs={max_documents}, idioma={language}")
        
        # Parámetros de búsqueda
        query_params = {
            'start_year': start_year,
            'end_year': end_year,
            'language': language,
            'terms': search_terms
        }
        
        try:
            # Fase 1: Búsqueda de documentos
            logger.info("Fase 1: Búsqueda de documentos...")
            documents = self.client.search_items(query_params, max_documents)
            
            if not documents:
                logger.error("No se encontraron documentos")
                return {'error': 'No se encontraron documentos'}
                
            self.memory.add_documents(documents)
            
            # Fase 2: Descarga de contenido
            logger.info("Fase 2: Descarga de contenido textual...")
            self._download_document_content(documents)
            
            # Fase 3: Análisis de frecuencias
            logger.info("Fase 3: Análisis de frecuencias...")
            frequencies = self.processor.calculate_frequencies(documents)
            self.memory.set_frequencies(frequencies)
            
            # Fase 4: Obtener términos principales
            top_terms = self.processor.get_top_terms(frequencies, top_n=100)
            self.memory.set_top_terms(top_terms)
            
            # Actualizar estadísticas
            client_stats = self.client.get_stats()
            self.memory.update_stats(client_stats)
            
            # Generar resultados
            results = self._generate_results()
            
            logger.info("Análisis completado exitosamente")
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis: {e}")
            return {'error': str(e)}
            
    def _download_document_content(self, documents: List[Document]):
        """Descargar contenido textual para todos los documentos"""
        
        successful_downloads = 0
        total_docs = len(documents)
        
        for i, doc in enumerate(documents, 1):
            try:
                logger.info(f"Descargando {i}/{total_docs}: {doc.identifier}")
                
                content = self.client.download_text(doc.identifier)
                if content:
                    doc.set_content(content)
                    successful_downloads += 1
                    logger.debug(f"Contenido descargado: {len(content)} caracteres")
                else:
                    logger.warning(f"No se pudo obtener contenido para {doc.identifier}")
                    
                # Rate limiting
                if i % 10 == 0:
                    logger.info(f"Progreso: {i}/{total_docs} documentos procesados")
                    
            except Exception as e:
                logger.error(f"Error descargando {doc.identifier}: {e}")
                continue
                
        logger.info(f"Descarga completada: {successful_downloads}/{total_docs} exitosos")
        
    def _generate_results(self) -> Dict:
        """Generar diccionario de resultados completos"""
        
        summary = self.memory.get_summary()
        
        return {
            'summary': summary,
            'documents': self.memory.documents,
            'frequencies': self.memory.frequencies,
            'top_terms': self.memory.top_terms,
            'analysis_metadata': {
                'analyzer_version': '1.0',
                'analysis_date': datetime.now().isoformat(),
                'total_terms_analyzed': len(self.memory.frequencies),
                'documents_processed': summary['documents_with_content']
            }
        }
        
    def export_results(self, results: Dict, output_dir: str = '.'):
        """
        Exportar resultados a archivos
        
        Args:
            results: Resultados del análisis
            output_dir: Directorio de salida
        """
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Exportar términos principales a CSV
        csv_filename = f"{output_dir}/top_terms_{timestamp}.csv"
        self.exporter.export_to_csv(results['top_terms'], csv_filename)
        
        # Exportar datos completos a JSON
        json_filename = f"{output_dir}/analysis_results_{timestamp}.json"
        self.exporter.export_to_json(results, json_filename)
        
    def display_results(self, results: Dict, top_n: int = 20):
        """
        Mostrar resultados en consola
        
        Args:
            results: Resultados del análisis
            top_n: Número de términos principales a mostrar
        """
        
        self.visualizer.print_summary(results['summary'])
        self.visualizer.print_top_terms(results['top_terms'], top_n)


def main():
    """Función principal para demostración del sistema"""
    
    # Configurar análisis de ejemplo
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=4.0)
    
    # Análisis del período 1995-2005
    results = analyzer.analyze_period(
        start_year=1995,
        end_year=2005,
        max_documents=50,  # Reducido para demo
        language='eng'
    )
    
    if 'error' not in results:
        # Mostrar resultados
        analyzer.display_results(results, top_n=25)
        
        # Exportar resultados
        analyzer.export_results(results)
        
        print(f"\n{'='*50}")
        print("ANÁLISIS COMPLETADO")
        print("Los resultados han sido exportados a archivos CSV y JSON")
        print(f"{'='*50}")
        
    else:
        print(f"Error en el análisis: {results['error']}")


if __name__ == "__main__":
    main()