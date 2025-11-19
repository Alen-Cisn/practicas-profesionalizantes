#!/usr/bin/env python3
"""
Analizador Histórico de Términos
Permite analizar las palabras más usadas en documentos web históricos durante períodos específicos
utilizando Internet Archive API.

Autor: Ian Alén Cisneros
Fecha: 2025-09-25
"""

import requests
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Set
from urllib.parse import urlencode
import logging
from collections import Counter, defaultdict
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from functools import lru_cache
import string

# HTML parsing optimization
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

# Simple content caching
import hashlib
import os

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
    Cliente para interactuar con Internet Archive API (Wayback Machine)
    Maneja búsqueda, descarga y procesamiento de páginas web históricas
    """
    
    # URLs base de Internet Archive - enfoque en Wayback Machine
    CDX_API = "http://web.archive.org/cdx/search/cdx"
    WAYBACK_BASE = "http://web.archive.org/web/"
    
    # Dominios populares para búsqueda de páginas web
    POPULAR_DOMAINS = [
        'cnn.com', 'bbc.co.uk', 'nytimes.com', 'washingtonpost.com', 
        'reuters.com', 'bloomberg.com', 'guardian.co.uk', 'time.com',
        'newsweek.com', 'usatoday.com', 'abcnews.go.com', 'cbsnews.com',
        'npr.org', 'pbs.org', 'economist.com', 'wsj.com', 'ft.com',
        'latimes.com', 'sfgate.com', 'chicagotribune.com'
    ]
    
    def __init__(self, rate_limit_delay: float = 1.0, enable_cache: bool = True):
        """
        Inicializar cliente con configuración de rate limiting
        
        Args:
            rate_limit_delay: Tiempo de espera entre requests en segundos
            enable_cache: Activar cache de contenido para evitar re-descargas
        """
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HistoricalTermAnalyzer/1.0 (Educational Research Project)'
        })
        
        # Sistema de cache simple
        self.enable_cache = enable_cache
        self.cache_dir = '.cache'
        if enable_cache:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # Estadísticas
        self.total_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        
    def search_items(self, query_params: Dict, max_results: int = 700) -> List[Document]:
        """
        Buscar páginas web históricas utilizando CDX API
        
        Args:
            query_params: Dict con start_year, end_year, domains, terms
            max_results: Límite máximo de páginas web
            
        Returns:
            Lista de objetos Document con metadatos de páginas web
        """
        logger.info(f"Iniciando búsqueda de páginas web con parámetros: {query_params}")
        
        documents = []
        domains = query_params.get('domains', self.POPULAR_DOMAINS[:5])
        
        # Buscar en cada dominio usando método robusto
        for domain in domains:
            try:
                # Intentar primero con búsqueda por años (más confiable)
                logger.info(f"Buscando páginas en {domain} usando método por años...")
                domain_documents = self._search_domain_by_years(domain, query_params, max_results // len(domains))
                
                documents.extend(domain_documents)
                
                logger.info(f"Dominio {domain}: {len(domain_documents)} páginas encontradas")
                
                if len(documents) >= max_results:
                    documents = documents[:max_results]
                    break
                    
                # Rate limiting entre dominios
                self._handle_rate_limiting()
                
            except Exception as e:
                logger.error(f"Error buscando en dominio {domain}: {e}")
                self.failed_requests += 1
                continue
                
        logger.info(f"Búsqueda completada: {len(documents)} páginas web encontradas")
        return documents
    def _search_domain_pages(self, domain: str, query_params: Dict, max_per_domain: int) -> List[Document]:
        """Buscar páginas web de un dominio específico usando CDX API"""
        logger.info(f"Buscando páginas en dominio: {domain}")
        
        start_year = query_params.get('start_year', 1995)
        end_year = query_params.get('end_year', 2005)
        
        # Parámetros para CDX API - optimizados para mejor respuesta
        params = {
            'url': f'{domain}',
            'from': f'{start_year}0101',
            'to': f'{end_year}1231',
            'output': 'json',
            # 'fl': 'timestamp,original,mimetype,statuscode,digest',
            # 'filter': 'statuscode:200',
            # 'filter': 'mimetype:text/html',
            'collapse': 'urlkey',  # Mejor que digest para evitar duplicados
            # 'limit': min(max_per_domain, 1000)  # Limitar requests grandes
        }
        
        # Usar timeout más largo para CDX API
        response = self._make_request(self.CDX_API, params, limit=min(max_per_domain, 1000), timeout=90)
        if not response:
            return []
            
        documents = []
        try:
            data = response.json()
            
            # Saltar la primera línea (headers) si existe
            if data and isinstance(data[0], list) and data[0][0] == 'timestamp':
                data = data[1:]
            
            logger.info(f"Recibidas {len(data)} entradas de CDX para {domain}")
                
            for entry in data:
                if len(entry) >= 5:  # Ahora son 5 campos en lugar de 6
                    timestamp, original_url, mimetype, statuscode, digest = entry[:5]
                    
                    # Filtrar solo contenido HTML
                    if mimetype and ('text/html' in mimetype or 'html' in mimetype):
                        document = self._create_document_from_cdx_entry(
                            timestamp, original_url, mimetype, digest
                        )
                        if document and self._validate_webpage(document, query_params):
                            documents.append(document)
                            
        except Exception as e:
            logger.error(f"Error procesando respuesta CDX para {domain}: {e}")
            
        return documents
    
    def _search_domain_by_years(self, domain: str, query_params: Dict, max_per_domain: int) -> List[Document]:
        """Búsqueda alternativa dividiendo por años individuales (más confiable)"""
        logger.info(f"Búsqueda por años para {domain}")
        
        start_year = query_params.get('start_year', 1995)
        end_year = query_params.get('end_year', 2005)
        
        all_documents = []
        years = list(range(start_year, end_year + 1))
        docs_per_year = max(5, max_per_domain // len(years))
        
        logger.info(f"Buscando en {len(years)} años, ~{docs_per_year} docs por año")
        
        for year in years:
            try:
                # Parámetros más simples y específicos
                params = {
                    'url': f'{domain}',
                    'from': f'{year}0101',
                    'to': f'{year}1231',
                    'output': 'json',
                    # 'fl': 'timestamp,original',  # Solo campos esenciales
                    # 'limit': docs_per_year,
                    # 'filter': 'statuscode:200'
                }
                
                logger.debug(f"Buscando {domain} en {year}...")
                response = self._make_request(self.CDX_API, params, limit=docs_per_year, timeout=90)

                if response:
                    try:
                        data = response.json()
                        
                        # Saltar header
                        if data and len(data) > 0 and isinstance(data[0], list):
                            if data[0][0] == 'timestamp':
                                data = data[1:]
                        
                        logger.info(f"  {year}: {len(data)} páginas encontradas")
                        
                        for entry in data:
                            logger.info(f"    Procesando entrada: {entry}")
                            if len(entry) >= 5:
                                _, timestamp, original_url, _, _ = entry[:5]

                                logger.info(f"    Campos: {timestamp}, {original_url}")

                                # Validar que sea una URL válida
                                if not original_url or len(original_url) < 10:
                                    continue
                                
                                # Crear documento
                                try:
                                    date_obj = datetime.strptime(timestamp[:14], '%Y%m%d%H%M%S')
                                    identifier = f"{domain}_{timestamp}_{len(all_documents)}"

                                    # Extraer título de URL
                                    url_parts = original_url.rstrip('/').split('/')
                                    title = url_parts[-1] if url_parts[-1] else url_parts[-2] if len(url_parts) > 1 else domain
                                    if '?' in title:
                                        title = title.split('?')[0]
                                    if len(title) > 100:
                                        title = title[:100]
                                    
                                    document = Document(identifier, title, date_obj, year)
                                    document.metadata = {
                                        'original_url': original_url,
                                        'wayback_url': f"{self.WAYBACK_BASE}{timestamp}/{original_url}",
                                        'mimetype': 'text/html',
                                        'source_api': 'cdx_by_year',
                                        'domain': domain
                                    }
                                    
                                    # Validar documento
                                    if self._validate_webpage(document, query_params):
                                        all_documents.append(document)
                                        
                                except ValueError as e:
                                    logger.debug(f"Error parseando timestamp {timestamp}: {e}")
                                    continue
                                except Exception as e:
                                    logger.debug(f"Error creando documento: {e}")
                                    continue
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parseando JSON para {year}: {e}")
                    except Exception as e:
                        logger.warning(f"Error procesando respuesta para {year}: {e}")
                else:
                    logger.warning(f"  {year}: Sin respuesta del servidor")
                
                # Rate limiting entre años - más corto
                time.sleep(self.rate_limit_delay * 0.3)
                
                # Si ya tenemos suficientes documentos, parar
                if len(all_documents) >= max_per_domain:
                    logger.info(f"Alcanzado límite de {max_per_domain} documentos para {domain}")
                    break
                    
            except Exception as e:
                logger.warning(f"Error buscando año {year} en {domain}: {e}")
                continue
        
        logger.info(f"✅ Búsqueda completada para {domain}: {len(all_documents)} documentos encontrados")
        return all_documents[:max_per_domain]
    
    def _create_document_from_cdx_entry(self, timestamp: str, original_url: str, 
                                       mimetype: str, digest: str) -> Optional[Document]:
        """Crear objeto Document desde entrada CDX"""
        try:
            # Parsear timestamp
            date_obj = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
            year = date_obj.year
            
            # Crear identificador único usando URL y timestamp
            identifier = f"{digest}_{timestamp}"
            
            # Extraer título de la URL
            title = original_url.split('/')[-1] or original_url.split('/')[-2]
            if '?' in title:
                title = title.split('?')[0]
                
            document = Document(identifier, title, date_obj, year)
            document.metadata = {
                'original_url': original_url,
                'wayback_url': f"{self.WAYBACK_BASE}{timestamp}/{original_url}",
                'mimetype': mimetype,
                'digest': digest,
                'source_api': 'cdx'
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Error creando documento desde CDX: {e}")
            return None
    def _validate_webpage(self, document: Document, query_params: Dict) -> bool:
        """Validar que la página web cumple con los criterios"""
        
        # Validar año
        start_year = query_params.get('start_year', 1995)
        end_year = query_params.get('end_year', 2005)
        
        if document.year:
            if document.year < start_year or document.year > end_year:
                return False
                
        # Validar que tenga URL original
        if not document.metadata.get('original_url'):
            return False
            
        # Filtrar URLs que probablemente no contengan texto útil
        url = document.metadata.get('original_url', '').lower()
        excluded_extensions = ['.jpg', '.png', '.gif', '.pdf', '.css', '.js', '.xml', '.rss']
        if any(url.endswith(ext) for ext in excluded_extensions):
            return False
            
        return True
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
        start_year = query_params.get('start_year', 2005)
        end_year = query_params.get('end_year', 2007)
        
        if document.year:
            if document.year < start_year or document.year > end_year:
                return False
                
        # Validar identificador válido
        if not document.identifier or len(document.identifier) < 5:
            return False
            
        return True
        
    def download_text(self, document: Document) -> str:
        """
        Descargar contenido HTML de una página web desde Wayback Machine con cache
        
        Args:
            document: Objeto Document con metadatos de la página
            
        Returns:
            Contenido textual extraído del HTML
        """
        wayback_url = document.metadata.get('wayback_url')
        if not wayback_url:
            logger.warning(f"No hay URL de Wayback para {document.identifier}")
            return ""
        
        # Verificar cache primero
        if self.enable_cache:
            cached_content = self._get_cached_content(wayback_url)
            if cached_content:
                self.cache_hits += 1
                logger.debug(f"Cache hit para {document.identifier}")
                return cached_content
            
        logger.debug(f"Descargando página: {wayback_url}")
        
        try:
            response = self._make_request(wayback_url, timeout=90)
            if response and response.status_code == 200:
                # Extraer texto del HTML
                html_content = response.text
                text_content = self._extract_text_from_html(html_content)
                
                # Validar que el contenido esté en inglés
                if text_content and self.validate_english_content(text_content):
                    cleaned_content = self._clean_text_content(text_content)
                    
                    # Guardar en cache
                    if self.enable_cache and cleaned_content:
                        self._cache_content(wayback_url, cleaned_content)
                    
                    return cleaned_content
                    
        except Exception as e:
            logger.warning(f"Error descargando {wayback_url}: {e}")
            
        return ""
    
    def _get_cache_key(self, url: str) -> str:
        """Generar clave de cache para una URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cached_content(self, url: str) -> Optional[str]:
        """Obtener contenido del cache si existe"""
        if not self.enable_cache:
            return None
            
        cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(url)}.txt")
        try:
            if os.path.exists(cache_file):
                # Verificar que el archivo no sea muy viejo (7 días)
                if time.time() - os.path.getmtime(cache_file) < 7 * 24 * 3600:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return f.read()
        except Exception:
            pass
        return None
    
    def _cache_content(self, url: str, content: str):
        """Guardar contenido en cache"""
        if not self.enable_cache or not content:
            return
            
        cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(url)}.txt")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception:
            pass
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extraer texto legible del contenido HTML con optimización BeautifulSoup"""
        try:
            # Usar BeautifulSoup si está disponible (mucho más rápido)
            if BEAUTIFULSOUP_AVAILABLE:
                return self._extract_text_with_beautifulsoup(html_content)
            else:
                # Fallback a regex (método original)
                return self._extract_text_with_regex(html_content)
                
        except Exception as e:
            logger.error(f"Error extrayendo texto de HTML: {e}")
            return ""
    
    def _extract_text_with_beautifulsoup(self, html_content: str) -> str:
        """Extracción optimizada con BeautifulSoup (70-90% más rápido)"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remover scripts, estilos y comentarios de una vez
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Obtener texto limpio directamente
            text = soup.get_text(separator=' ', strip=True)
            
            # Limpiar espacios múltiples
            text = re.sub(r'\s+', ' ', text)
            
            return text
            
        except Exception as e:
            logger.warning(f"BeautifulSoup falló, usando regex: {e}")
            return self._extract_text_with_regex(html_content)
    
    def _extract_text_with_regex(self, html_content: str) -> str:
        """Método original con regex (para fallback)"""
        try:
            # Remover scripts y estilos
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remover comentarios HTML
            html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
            
            # Remover todas las etiquetas HTML pero mantener el texto
            text = re.sub(r'<[^>]+>', ' ', html_content)
            
            # Decodificar entidades HTML comunes
            html_entities = {
                '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
                '&#39;': "'", '&nbsp;': ' ', '&copy;': '©', '&reg;': '®'
            }
            for entity, char in html_entities.items():
                text = text.replace(entity, char)
            
            return text
            
        except Exception as e:
            logger.error(f"Error con extracción regex: {e}")
            return ""
            
    def _download_file_content(self, identifier: str, filename: str) -> str:
        """Descargar contenido de un archivo específico - DEPRECATED"""
        # Método mantenido para compatibilidad pero ya no se usa
        return ""
        
    def _get_text_via_metadata_api(self, identifier: str) -> str:
        """Obtener texto a través de la API de metadatos - DEPRECATED"""
        # Método mantenido para compatibilidad pero ya no se usa
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
            'should', 'may', 'might', 'must', 'can', 'a', 'an', 'br', 'com', 'www', 'rol'
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

    def _make_request(self, url: str, params: Dict = None, limit: int = 100, timeout: int = 90) -> Optional[requests.Response]:
        """Realizar request HTTP con manejo de errores y rate limiting"""
        
        self.total_requests += 1
        
        try:
            if params:
                if '?' in url:
                    url += '&' + urlencode(params)
                else:
                    url += '?' + urlencode(params)

            logger.debug(f"Realizando request a: {url}")

            response = self.session.get(url, timeout=timeout)
            
            # Manejar códigos de error específicos
            if response.status_code == 429:  # Too Many Requests
                logger.warning("Rate limit exceeded, esperando más tiempo...")
                time.sleep(self.rate_limit_delay * 3)
                return self._make_request(url, timeout=timeout)
                
            elif response.status_code == 503:  # Service Unavailable
                logger.warning("Servicio no disponible, esperando y reintentando...")
                time.sleep(self.rate_limit_delay * 2)
                # Un solo reintento para evitar bucles infinitos
                try:
                    response = self.session.get(url, timeout=timeout)
                    if response.status_code == 200:
                        return response
                except:
                    pass
                return None
                
            elif response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} para {url}")
                return None
                
            return response
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout para {url}")
            self.failed_requests += 1
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Error de conexión para {url}")
            self.failed_requests += 1
            time.sleep(self.rate_limit_delay)
            return None
        except Exception as e:
            logger.error(f"Error en request: {e}")
            self.failed_requests += 1
            return None
            
    def _handle_rate_limiting(self):
        """Implementar delays entre requests"""
        time.sleep(self.rate_limit_delay)
        
    def get_stats(self) -> Dict:
        """Obtener estadísticas del cliente incluyendo cache"""
        total_requests = max(self.total_requests, 1)
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.total_requests - self.failed_requests) / total_requests * 100,
            'cache_hits': self.cache_hits if self.enable_cache else 0,
            'cache_hit_rate': (self.cache_hits / total_requests * 100) if self.enable_cache and total_requests > 0 else 0
        }


class TextProcessor:
    """
    Procesador de texto optimizado para análisis de frecuencias
    Incluye caching, procesamiento paralelo y stop words ampliadas
    """
    
    # Stop words expandidas en inglés - lista más completa para mejor filtrado
    STOP_WORDS = {
        # Artículos, preposiciones y conjunciones básicas
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 
        'cnn', 'nyt', 'york', 'bbc', 'reuters', 'bloomberg', 'guardian', 'time',
        'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was',
        'will', 'with', 'this', 'but', 'they', 'have', 'had', 'what', 'said', 
        'each', 'which', 'do', 'how', 'their', 'if', 'up', 'out', 'many',
        'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like',
        'into', 'him', 'time', 'two', 'more', 'very', 'when', 'come', 'may',
        'only', 'think', 'now', 'you', 'his', 'your', 'here', 'me', 'should', 
        'could', 'been', 'than', 'who', 'just', 'where', 'most', 'us', 'much', 
        'go', 'being', 'over', 'such', 'our', 'made', 'can', 'get', 'am', 'way', 
        'too', 'any', 'day', 'same', 'right', 'under', 'while', 'might',
        'old', 'year', 'off', 'since', 'against', 'back', 'take', 'part', 'used', 
        'use', 'during', 'without', 'again', 'around', 'however', 'why', 'turn', 
        'put', 'end', 'does', 'another', 'well', 'must', 'even', 'give',
        'means', 'different', 'move', 'did', 'no', 'my', 'know', 'first', 
        'down', 'side', 'find', 'own', 'found', 'still', 'between', 'keep', 
        'never', 'let', 'saw', 'far', 'left', 'late', 'run', 'don', 'press', 
        'close', 'night', 'real', 'few', 'took', 'once', 'hear', 'cut', 'sure', 
        'watch', 'seem', 'together', 'next', 'got', 'walk', 'always', 'those', 
        'both', 'often', 'until', 'care', 'second', 'enough', 'ready', 'above', 
        'ever', 'though', 'feel', 'talk', 'soon', 'direct', 'leave', 'told', 
        'knew', 'pass', 'top', 'heard', 'best', 'hour', 'better', 'hundred', 
        'five', 'remember', 'step', 'early', 'hold', 'reach', 'fast', 'listen', 
        'six', 'less', 'ten', 'simple', 'several', 'toward', 'lay', 'pattern', 
        'slow', 'serve', 'appear', 'pull', 'cold', 'notice', 'fine', 'certain', 
        'fly', 'fall', 'lead', 'cry', 'dark', 'note', 'wait', 'plan', 'rest', 
        'able', 'done', 'stood', 'front', 'week', 'gave', 'develop', 'warm', 
        'free', 'minute', 'special', 'behind', 'clear', 'produce', 'nothing', 
        'stay', 'full', 'force', 'decide', 'deep', 'busy', 'record', 'common', 
        'possible', 'dry', 'ago', 'ran', 'check', 'hot', 'miss', 'brought', 
        'heat', 'yes', 'fill', 'among', 'new', 'all', 'not'
        
        # Palabras comunes adicionales de web y documentos
        'page', 'pages', 'site', 'website', 'web', 'home', 'click', 'link', 
        'links', 'search', 'about', 'contact', 'help', 'information', 'info', 
        'copyright', 'rights', 'reserved', 'terms', 'privacy', 'policy', 
        'service', 'services', 'content', 'text', 'article', 'news', 'date',
        'today', 'yesterday', 'tomorrow', 'monday', 'tuesday', 'wednesday', 
        'thursday', 'friday', 'saturday', 'sunday', 'january', 'february', 
        'march', 'april', 'june', 'july', 'august', 'september', 'october', 
        'november', 'december', 'email', 'mail', 'phone', 'address', 'name',
        'first', 'last', 'middle', 'title', 'description', 'view', 'views',
        'read', 'reading', 'write', 'written', 'author', 'posted', 'post',
        'comment', 'comments', 'reply', 'replies', 'submit', 'send', 'login',
        'register', 'sign', 'password', 'username', 'user', 'users', 'member',
        'members', 'join', 'follow', 'share', 'print', 'save', 'download',
        
        # Números y medidas comunes
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
        'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
        'seventeen', 'eighteen', 'nineteen', 'twenty', 'thirty', 'forty', 'fifty',
        'sixty', 'seventy', 'eighty', 'ninety', 'hundred', 'thousand', 'million',
        'billion', 'first', 'second', 'third', 'fourth', 'fifth', 'last',
        
        # Palabras técnicas comunes de HTML/Web
        'html', 'http', 'https', 'www', 'com', 'org', 'net', 'edu', 'gov',
        'jpg', 'gif', 'png', 'pdf', 'doc', 'docx', 'txt', 'css', 'javascript',
        'script', 'image', 'images', 'photo', 'photos', 'video', 'videos',
        'file', 'files', 'folder', 'folders', 'document', 'documents'
    }
    
    def __init__(self, use_parallel: bool = True, max_workers: int = None):
        """
        Inicializar procesador de texto optimizado
        
        Args:
            use_parallel: Usar procesamiento paralelo
            max_workers: Número máximo de workers (None = auto)
        """
        self.use_parallel = use_parallel
        self.max_workers = max_workers or min(4, mp.cpu_count())
        
        # Compilar expresiones regulares una sola vez
        self.word_pattern = re.compile(r'\b[a-zA-Z]{2,}\b')
        self.whitespace_pattern = re.compile(r'\s+')
        self.punctuation_pattern = re.compile(f'[{re.escape(string.punctuation)}]')
        
        # Cache para términos extraídos
        self._term_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    @lru_cache(maxsize=1000)
    def _clean_and_normalize_text(self, text: str) -> str:
        """Limpiar y normalizar texto usando cache"""
        if not text:
            return ""
            
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover puntuación y normalizar espacios
        text = self.punctuation_pattern.sub(' ', text)
        text = self.whitespace_pattern.sub(' ', text)
        
        return text.strip()
        
    def extract_terms(self, text: str) -> List[str]:
        """
        Extraer términos relevantes del texto con optimizaciones
        
        Args:
            text: Texto a procesar
            
        Returns:
            Lista de términos limpios
        """
        if not text:
            return []
            
        # Verificar cache
        text_hash = hash(text[:1000])  # Usar hash de los primeros 1000 caracteres
        if text_hash in self._term_cache:
            self._cache_hits += 1
            return self._term_cache[text_hash]
            
        self._cache_misses += 1
        
        # Limpiar y normalizar
        cleaned_text = self._clean_and_normalize_text(text)
        
        # Extraer palabras usando regex compilada
        words = self.word_pattern.findall(cleaned_text)
        
        # Filtrar stop words en una sola pasada
        terms = [word for word in words 
                if word not in self.STOP_WORDS and len(word) >= 2]
        
        # Guardar en cache (limitar tamaño del cache)
        if len(self._term_cache) < 500:
            self._term_cache[text_hash] = terms
            
        return terms
        
    def _process_document_batch(self, documents: List) -> Dict[str, int]:
        """Procesar un lote de documentos y retornar frecuencias"""
        batch_frequencies = defaultdict(int)
        
        for doc in documents:
            if hasattr(doc, 'text_content') and doc.text_content:
                terms = self.extract_terms(doc.text_content)
                for term in terms:
                    batch_frequencies[term] += 1
                    
        return dict(batch_frequencies)
        
    def calculate_frequencies(self, documents_or_text) -> Dict[str, int]:
        """
        Calcular frecuencias de términos con procesamiento paralelo optimizado
        
        Args:
            documents_or_text: Lista de documentos o texto directo
            
        Returns:
            Diccionario con frecuencias de términos
        """
        if isinstance(documents_or_text, str):
            # Caso: texto directo
            terms = self.extract_terms(documents_or_text)
            return dict(Counter(terms))
            
        elif isinstance(documents_or_text, list):
            # Caso: lista de documentos
            documents = documents_or_text
            logger.info(f"Calculando frecuencias para {len(documents)} documentos")
            
            # Filtrar documentos con contenido
            docs_with_content = [doc for doc in documents 
                               if hasattr(doc, 'text_content') and doc.text_content]
            
            logger.info(f"Procesando {len(docs_with_content)} documentos con contenido")
            
            if not docs_with_content:
                return {}
                
            # Procesamiento paralelo si está habilitado y hay suficientes documentos
            if self.use_parallel and len(docs_with_content) > 10:
                return self._calculate_frequencies_parallel(docs_with_content)
            else:
                return self._calculate_frequencies_sequential(docs_with_content)
        
        return {}
        
    def _calculate_frequencies_parallel(self, documents: List) -> Dict[str, int]:
        """Calcular frecuencias usando procesamiento paralelo"""
        logger.info(f"Usando procesamiento paralelo con {self.max_workers} workers")
        
        # Dividir documentos en lotes
        batch_size = max(1, len(documents) // self.max_workers)
        document_batches = [documents[i:i + batch_size] 
                           for i in range(0, len(documents), batch_size)]
        
        # Procesar lotes en paralelo
        combined_frequencies = defaultdict(int)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar lotes a procesar
            future_to_batch = {
                executor.submit(self._process_document_batch, batch): batch 
                for batch in document_batches
            }
            
            # Recopilar resultados
            for future in as_completed(future_to_batch):
                try:
                    batch_freq = future.result()
                    for term, freq in batch_freq.items():
                        combined_frequencies[term] += freq
                except Exception as e:
                    logger.error(f"Error procesando lote: {e}")
                    
        logger.info(f"Procesamiento paralelo completado. Términos únicos: {len(combined_frequencies)}")
        return dict(combined_frequencies)
        
    def _calculate_frequencies_sequential(self, documents: List) -> Dict[str, int]:
        """Calcular frecuencias secuencialmente"""
        logger.info("Usando procesamiento secuencial")
        
        all_terms = []
        for doc in documents:
            terms = self.extract_terms(doc.text_content)
            all_terms.extend(terms)
            
        logger.info(f"Total de términos extraídos: {len(all_terms)}")
        return dict(Counter(all_terms))
        
    def get_cache_stats(self) -> Dict:
        """Obtener estadísticas del cache"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self._term_cache)
        }
        
    def get_top_terms(self, frequencies: Dict[str, int], top_n: int = 50) -> List[tuple]:
        """
        Obtener los términos más frecuentes con filtrado adicional
        
        Args:
            frequencies: Diccionario de frecuencias
            top_n: Número de términos principales a retornar
            
        Returns:
            Lista de tuplas (término, frecuencia) ordenada por frecuencia
        """
        # Filtrar términos muy cortos o que parecen ruido
        filtered_freq = {
            term: freq for term, freq in frequencies.items()
            if len(term) >= 3 and not term.isdigit() and freq > 1
        }
        
        return Counter(filtered_freq).most_common(top_n)


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
    
    def __init__(self, rate_limit_delay: float = 1.0, progress_callback=None):
        """
        Inicializar analizador histórico
        
        Args:
            rate_limit_delay: Delay entre requests a Internet Archive
            progress_callback: Función callback para reportar progreso (opcional)
        """
        self.client = InternetArchiveClient(rate_limit_delay)
        self.processor = TextProcessor()
        self.memory = SessionMemory()
        self.exporter = Exporter()
        self.visualizer = Visualizer()
        self.progress_callback = progress_callback
        
    def analyze_period(self, 
                      start_year: int, 
                      end_year: int, 
                      max_documents: int = 600,
                      domains: Optional[List[str]] = None,
                      search_terms: Optional[List[str]] = None,
                      analyze_by_year: bool = False) -> Dict:
        """
        Analizar términos en páginas web de un período histórico específico
        
        Args:
            start_year: Año de inicio del período
            end_year: Año de fin del período
            max_documents: Número máximo de páginas web a analizar
            domains: Lista de dominios a buscar (opcional, usa lista por defecto)
            search_terms: Términos específicos a buscar (opcional)
            analyze_by_year: Si True, genera resultados separados por año
            
        Returns:
            Diccionario con resultados del análisis
        """
        
        logger.info(f"Iniciando análisis histórico de páginas web: {start_year}-{end_year}")
        logger.info(f"Parámetros: max_docs={max_documents}, dominios={domains or 'default'}")
        
        # Parámetros de búsqueda
        query_params = {
            'start_year': start_year,
            'end_year': end_year,
            'domains': domains,
            'terms': search_terms
        }
        
        try:
            # Paso 1: Búsqueda de documentos (10% del progreso)
            if self.progress_callback:
                self.progress_callback(5, "Buscando páginas web en Internet Archive...")
            
            documents = self.client.search_items(query_params, max_results=max_documents)
            
            if not documents:
                return {'error': 'No se encontraron páginas web para los criterios especificados'}
            
            if self.progress_callback:
                self.progress_callback(10, f"Encontradas {len(documents)} páginas web")
            
            self.memory.add_documents(documents)
            
            # Paso 2: Descarga de contenido (10% - 70% del progreso)
            if self.progress_callback:
                self.progress_callback(15, "Iniciando descarga de contenido...")
            
            self._download_document_content(documents)
            
            # Filtrar documentos con contenido
            docs_with_content = [d for d in documents if d.text_content]
            
            if not docs_with_content:
                return {'error': 'No se pudo extraer contenido de ninguna página web'}
            
            if self.progress_callback:
                self.progress_callback(75, f"{len(docs_with_content)} páginas con contenido válido")
            
            # Paso 3: Procesamiento de términos (70% - 90% del progreso)
            if self.progress_callback:
                self.progress_callback(80, "Procesando y contando términos...")
            
            # Análisis agregado
            frequencies = self.processor.calculate_frequencies(docs_with_content)
            top_terms = self.processor.get_top_terms(frequencies, top_n=50)
            
            self.memory.set_frequencies(frequencies)
            self.memory.set_top_terms(top_terms)
            
            # Análisis por año si se solicita
            results_by_year = {}
            if analyze_by_year:
                if self.progress_callback:
                    self.progress_callback(85, "Generando análisis por año...")
                results_by_year = self._analyze_by_year(docs_with_content)
            
            # Paso 4: Generar estadísticas (90% - 95% del progreso)
            if self.progress_callback:
                self.progress_callback(90, "Generando estadísticas...")
            
            client_stats = self.client.get_stats()
            processor_stats = self.processor.get_cache_stats() if hasattr(self.processor, 'get_cache_stats') else {}
            
            self.memory.update_stats({
                'client_stats': client_stats,
                'processor_stats': processor_stats
            })
            
            # Paso 5: Generar resultados finales (95% - 100%)
            if self.progress_callback:
                self.progress_callback(95, "Finalizando análisis...")
            
            results = self._generate_results()
            
            # Agregar resultados por año si se generaron
            if results_by_year:
                results['results_by_year'] = results_by_year
            
            if self.progress_callback:
                self.progress_callback(100, "¡Análisis completado!")
            
            logger.info("Análisis completado exitosamente")
            return results
            
        except Exception as e:
            error_msg = f"Error durante el análisis: {str(e)}"
            logger.error(error_msg)
            if self.progress_callback:
                self.progress_callback(0, f"Error: {str(e)}")
            return {'error': error_msg}
    
    def _analyze_by_year(self, documents: List[Document]) -> Dict:
        """
        Analizar términos separadamente para cada año
        
        Args:
            documents: Lista de documentos con contenido
            
        Returns:
            Diccionario con resultados por año {año: {frequencies, top_terms}}
        """
        results_by_year = {}
        
        # Agrupar documentos por año
        docs_by_year = defaultdict(list)
        for doc in documents:
            if doc.year:
                docs_by_year[doc.year].append(doc)
        
        # Analizar cada año
        for year in sorted(docs_by_year.keys()):
            year_docs = docs_by_year[year]
            
            # Calcular frecuencias para este año
            frequencies = self.processor.calculate_frequencies(year_docs)
            top_terms = self.processor.get_top_terms(frequencies, top_n=50)
            
            results_by_year[year] = {
                'frequencies': frequencies,
                'top_terms': top_terms,
                'document_count': len(year_docs)
            }
            
            logger.info(f"Año {year}: {len(year_docs)} documentos, {len(frequencies)} términos únicos")
        
        return results_by_year
            
    def _download_document_content(self, documents: List[Document]):
        """Descargar contenido textual para todas las páginas web con paralelización optimizada"""
        
        successful_downloads = 0
        total_docs = len(documents)
        
        logger.info(f"Iniciando descarga paralela de {total_docs} documentos...")
        
        # Usar paralelización para downloads de red
        max_workers = min(8, total_docs)  # Máximo 8 workers para evitar sobrecargar el servidor
        
        # Variables para tracking de progreso
        completed_docs = 0
        progress_step = max(1, total_docs // 60)  # Actualizar progreso cada ~1.6% (60 pasos entre 15% y 75%)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas de descarga
            future_to_doc = {
                executor.submit(self._download_single_document, doc): doc 
                for doc in documents
            }
            
            # Procesar resultados a medida que se completan
            for future in as_completed(future_to_doc):
                doc = future_to_doc[future]
                completed_docs += 1
                
                try:
                    success = future.result()
                    if success:
                        successful_downloads += 1
                        
                    # Reportar progreso (15% - 75% del rango total)
                    if self.progress_callback and completed_docs % progress_step == 0:
                        progress_percent = 15 + int((completed_docs / total_docs) * 60)
                        self.progress_callback(
                            progress_percent, 
                            f"Descargando: {completed_docs}/{total_docs} páginas"
                        )
                        
                except Exception as e:
                    logger.error(f"Error procesando resultado de descarga: {e}")
        
        # Reporte final de descarga
        if self.progress_callback:
            self.progress_callback(75, f"Descarga completada: {successful_downloads}/{total_docs} páginas exitosas")
                    
        logger.info(f"Descarga paralela completada: {successful_downloads}/{total_docs} exitosos")
    
    def _download_single_document(self, doc: Document) -> bool:
        """Descargar contenido de un solo documento (para uso en ThreadPoolExecutor)"""
        try:
            wayback_url = doc.metadata.get('wayback_url')
            if not wayback_url:
                return False
                
            content = self.client.download_text(doc)
            if content:
                doc.set_content(content)
                return True
            return False
            
        except Exception as e:
            logger.debug(f"Error en descarga individual de {doc.identifier}: {e}")
            return False
        
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
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=1.0)  # Usar rate limit optimizado
    
    # Análisis del período 2000-2005 enfocado en páginas web
    results = analyzer.analyze_period(
        start_year=2000,
        end_year=2005,
        max_documents=300,  # Reducido para demo
        domains=['cnn.com', 'bbc.co.uk', 'nytimes.com']  # Dominios específicos
    )
    
    if 'error' not in results:
        # Mostrar resultados
        analyzer.display_results(results, top_n=25)
        
        # Exportar resultados
        analyzer.export_results(results)
        
        # Mostrar estadísticas del cache si está disponible
        if hasattr(analyzer.processor, 'get_cache_stats'):
            cache_stats = analyzer.processor.get_cache_stats()
            print(f"\n📊 Estadísticas del Cache:")
            print(f"Hit rate: {cache_stats['hit_rate_percent']}%")
            print(f"Cache size: {cache_stats['cache_size']}")
        
        print(f"\n{'='*50}")
        print("ANÁLISIS COMPLETADO")
        print("Los resultados han sido exportados a archivos CSV y JSON")
        print("Para usar la interfaz web, ejecuta: streamlit run streamlit_app.py")
        print(f"{'='*50}")
        
    else:
        print(f"Error en el análisis: {results['error']}")


if __name__ == "__main__":
    main()