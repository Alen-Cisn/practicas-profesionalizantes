# Prompt Detallado para Implementar Búsqueda con Internet Archive API

## Contexto del Proyecto

Estás desarrollando un **Analizador Histórico de Términos** que permite a investigadores sociolingüísticos analizar las palabras más usadas en documentos web históricos durante períodos específicos. El sistema utiliza Internet Archive API para acceder a páginas web archivadas y realizar análisis de frecuencia de términos.

## Objetivos Funcionales - Primera Iteración

1. **Búsqueda temporal**: Permitir definir período histórico (fecha desde/hasta)
2. **Filtrado por idioma**: Procesar únicamente documentos en inglés
3. **Control de volumen**: Limitar número de documentos analizados (configurable, mínimo 600)
4. **Procesamiento web**: Extraer y procesar contenido de páginas web históricas
5. **Análisis de frecuencias**: Contar ocurrencias de términos sin lematización
6. **Filtrado de ruido**: Eliminar stop words manteniendo términos relevantes

## Arquitectura del Sistema

```
HistoricalTermAnalyzer (Orquestador principal)
├── InternetArchiveClient (Acceso a API)
├── TextProcessor (Procesamiento NLP)
├── Document (Modelo de datos)
├── SessionMemory (Memoria temporal)
├── Exporter (Exportación resultados)
└── Visualizer (Gráficos)
```

## Tarea Principal: Implementar InternetArchiveClient

### Paso 1: Análisis de Requisitos
**Objetivo**: Comprender completamente la API de Internet Archive y sus limitaciones

**Acciones requeridas**:
1. Investigar documentación oficial de Internet Archive API
2. Identificar endpoints específicos para búsqueda web histórica
3. Determinar parámetros de filtrado temporal y por idioma
4. Entender límites de rate limiting (6-15 requests/minuto)
5. Analizar estructura de respuestas y metadatos disponibles

**Resultado esperado**: Documento con especificaciones técnicas de la API

### Paso 2: Diseño de la Clase InternetArchiveClient
**Objetivo**: Crear interfaz robusta para interactuar con Internet Archive

**Funciones principales a implementar**:

```python
class InternetArchiveClient:
    def __init__(self, rate_limit_delay=4.0):
        """
        Inicializar cliente con configuración de rate limiting
        """
        pass
    
    def search_items(self, query_params: Dict, max_results: int = 600) -> List[Document]:
        """
        Buscar documentos web históricos con filtros
        
        Parámetros:
        - query_params: Dict con start_year, end_year, language, terms
        - max_results: Límite máximo de documentos (configurable)
        
        Filtros obligatorios:
        - mediatype:web (solo páginas web)
        - language:eng (solo inglés) 
        - date:[start_year TO end_year]
        
        Retorna: Lista de objetos Document con metadatos
        """
        pass
    
    def download_text(self, identifier: str) -> str:
        """
        Descargar contenido textual de un documento específico
        
        Manejo de:
        - Diferentes formatos (.txt, _djvu.txt, .html)
        - Rate limiting entre descargas
        - Validación de contenido en inglés
        - Limpieza básica de HTML/metadatos
        """
        pass
    
    def validate_english_content(self, text: str) -> bool:
        """
        Validar que el contenido esté en inglés
        Usar detección básica de idioma o patrones
        """
        pass
```

### Paso 3: Implementación de Filtros y Validaciones
**Objetivo**: Asegurar calidad y relevancia de los datos obtenidos

**Filtros de búsqueda requeridos**:
1. **Temporal**: `date:[1995-01-01 TO 2005-12-31]`
2. **Tipo de contenido**: `mediatype:web`
3. **Idioma**: `language:eng` o validación post-descarga
4. **Colección**: `collection:web` (Wayback Machine)
5. **Límite de resultados**: Implementar paginación para manejar grandes volúmenes

**Validaciones necesarias**:
- Verificar que las fechas estén en rango válido
- Confirmar disponibilidad de contenido textual
- Validar que el idioma sea inglés (detección automática)
- Manejar errores de API (timeouts, límites excedidos)

### Paso 4: Manejo de Rate Limiting y Errores
**Objetivo**: Implementar acceso responsable y robusto a la API

**Estrategias requeridas**:
```python
def _handle_rate_limiting(self):
    """Implementar delays entre requests"""
    time.sleep(self.rate_limit_delay)

def _retry_on_failure(self, func, max_retries=3):
    """Reintentar en caso de errores temporales"""
    pass

def _handle_api_errors(self, response):
    """Manejar códigos de error HTTP específicos"""
    # 429: Too Many Requests
    # 503: Service Unavailable
    # 404: Not Found
    pass
```

### Paso 5: Integración con Modelo Document
**Objetivo**: Estructurar datos obtenidos en formato consistente

**Clase Document requerida**:
```python
class Document:
    def __init__(self, identifier: str, title: str, date: datetime, year: int):
        self.identifier = identifier
        self.title = title  
        self.date = date
        self.year = year
        self.text_content = ""
        
    def get_metadata(self) -> Dict:
        """Retornar metadatos estructurados"""
        pass
        
    def get_text(self) -> str:
        """Retornar contenido textual limpio"""
        pass
```

### Paso 6: Implementación de Muestreo Representativo
**Objetivo**: Obtener muestra manejable pero representativa

**Estrategias de muestreo**:
1. **Muestreo estratificado por años**: Dividir período en subrangos
2. **Límite por dominio**: Evitar sobrerrepresentación de sitios específicos
3. **Distribución temporal uniforme**: Balancear documentos por año
4. **Filtrado por popularidad**: Priorizar documentos con más snapshots

## Criterios de Éxito

### Funcionalidad Mínima Viable
- [ ] Búsqueda exitosa con filtros temporales
- [ ] Descarga de al menos 600 documentos en inglés
- [ ] Validación automática de idioma
- [ ] Manejo de rate limiting sin errores 429
- [ ] Tiempo de ejecución < 90 minutos

### Métricas de Calidad
- [ ] 95%+ de documentos descargados en inglés
- [ ] <5% de errores en descargas
- [ ] Distribución temporal equilibrada
- [ ] Metadatos completos para todos los documentos

## Consideraciones Técnicas

### Bibliotecas Recomendadas
```python
import requests          # HTTP requests
import time             # Rate limiting
import re               # Procesamiento texto
import json             # Manejo JSON
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlencode
```

### Configuración Inicial
```python
# URLs base de Internet Archive
SEARCH_API = "https://archive.org/advancedsearch.php"
CDX_API = "http://web.archive.org/cdx/search/cdx"
DOWNLOAD_BASE = "https://archive.org/download/"

# Límites operacionales
MAX_REQUESTS_PER_MINUTE = 10
DEFAULT_MAX_RESULTS = 600
REQUEST_TIMEOUT = 30
```

## Entregables Esperados

1. **Código funcional** de la clase `InternetArchiveClient`
2. **Casos de prueba** para validar filtros y límites
3. **Documentación** de parámetros y uso
4. **Script de ejemplo** demostrando búsqueda 1995-2005
5. **Manejo de errores** robusto con logging

## Restricciones y Limitaciones

- Respetar límites de API (máximo 15 requests/minuto)
- Procesar únicamente contenido en inglés
- Limitar a páginas web archivadas (mediatype:web)
- Manejar volúmenes grandes con paginación
- Tiempo total de proceso < 90 minutos para 600 documentos

***

**Instrucción final para el IDE con IA**: Implementa la clase `InternetArchiveClient` siguiendo este prompt, investigando la documentación oficial de Internet Archive API, y creando un sistema robusto de búsqueda y descarga que cumpla con todos los objetivos funcionales especificados para la primera iteración del proyecto.

https://archive.org/developers/index-apis.html