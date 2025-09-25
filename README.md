# Analizador Histórico de Términos

## Descripción del Proyecto

El **Analizador Histórico de Términos** es un sistema desarrollado para investigadores sociolingüísticos que permite analizar las palabras más utilizadas en documentos web históricos durante períodos específicos. El sistema utiliza la API de Internet Archive para acceder a páginas web archivadas y realizar análisis de frecuencia de términos.

## Características Principales

### 🔍 Funcionalidades Implementadas - Primera Iteración

- **Búsqueda temporal**: Define período histórico específico (fecha desde/hasta)
- **Filtrado por idioma**: Procesa únicamente documentos en inglés
- **Control de volumen**: Limita número de documentos analizados (configurable, mínimo 600)
- **Procesamiento web**: Extrae y procesa contenido de páginas web históricas
- **Análisis de frecuencias**: Cuenta ocurrencias de términos sin lematización
- **Filtrado de ruido**: Elimina stop words manteniendo términos relevantes

### 🏗️ Arquitectura del Sistema

```
HistoricalTermAnalyzer (Orquestador principal)
├── InternetArchiveClient (Acceso a API)
├── TextProcessor (Procesamiento NLP)
├── Document (Modelo de datos)
├── SessionMemory (Memoria temporal)
├── Exporter (Exportación resultados)
└── Visualizer (Gráficos)
```

## Instalación y Configuración

### Requisitos del Sistema

- Python 3.8 o superior
- Conexión a Internet estable
- Bibliotecas requeridas:

```bash
pip install requests
```

### Bibliotecas Estándar Utilizadas

El proyecto utiliza principalmente bibliotecas estándar de Python:
- `requests` - Para peticiones HTTP
- `time` - Para rate limiting
- `re` - Para procesamiento de texto
- `json` - Para manejo de datos JSON
- `datetime` - Para manejo de fechas
- `typing` - Para type hints
- `logging` - Para logging del sistema
- `collections` - Para Counter y estructuras de datos
- `csv` - Para exportación a CSV
- `unittest` - Para testing

## Uso del Sistema

### Uso Básico

```python
from historical_term_analyzer import HistoricalTermAnalyzer

# Inicializar analizador
analyzer = HistoricalTermAnalyzer(rate_limit_delay=4.0)

# Análizar período histórico
results = analyzer.analyze_period(
    start_year=1995,
    end_year=2005,
    max_documents=600,
    language='eng'
)

# Mostrar resultados
analyzer.display_results(results, top_n=25)

# Exportar resultados
analyzer.export_results(results)
```

### Configuración Avanzada

```python
# Con términos de búsqueda específicos
results = analyzer.analyze_period(
    start_year=1998,
    end_year=2002,
    max_documents=800,
    language='eng',
    search_terms=['internet', 'computer', 'technology']
)

# Con rate limiting personalizado (recomendado: 4-6 segundos)
analyzer = HistoricalTermAnalyzer(rate_limit_delay=5.0)
```

## Especificaciones Técnicas

### Clase InternetArchiveClient

Interfaz robusta para interactuar con Internet Archive:

#### Funciones Principales

- `search_items()`: Busca documentos web históricos con filtros
- `download_text()`: Descarga contenido textual de documentos específicos
- `validate_english_content()`: Valida que el contenido esté en inglés

#### Filtros Implementados

- **Temporal**: `date:[1995-01-01 TO 2005-12-31]`
- **Tipo de contenido**: `mediatype:web`
- **Idioma**: `language:eng` o validación post-descarga
- **Colección**: `collection:web` (Wayback Machine)

#### Rate Limiting

- Límite respetado: 6-15 requests por minuto
- Delay configurable entre requests (por defecto: 4 segundos)
- Reintentos automáticos en caso de errores temporales

### Clase TextProcessor

Procesador de texto para análisis de frecuencias:

- Extracción de términos relevantes (3+ caracteres)
- Filtrado de 200+ stop words en inglés
- Cálculo de frecuencias sin lematización
- Obtención de términos más frecuentes

### Validaciones y Controles de Calidad

#### Validación de Idioma Inglés

El sistema implementa un algoritmo de detección de idioma que:

- Analiza patrones de palabras comunes en inglés
- Verifica ratio de caracteres no latinos
- Requiere mínimo 15% de palabras en inglés reconocidas
- Máximo 5% de caracteres no latinos

#### Filtros de Calidad

- Contenido mínimo: 100 caracteres
- Palabras mínimas: 10 palabras válidas
- Identificadores válidos: mínimo 5 caracteres
- Validación temporal: documentos dentro del rango especificado

## Limitaciones y Consideraciones

### Limitaciones Técnicas

- **Rate Limiting**: Máximo 15 requests por minuto
- **Tiempo de procesamiento**: ~90 minutos para 600 documentos
- **Idioma**: Solo procesamiento de contenido en inglés
- **Tipo de contenido**: Solo páginas web archivadas (mediatype:web)

### Consideraciones de Uso

- El sistema respeta las políticas de uso de Internet Archive
- Se recomienda usar durante horas de menor tráfico
- Los resultados pueden variar según disponibilidad de contenido archivado
- La calidad del análisis depende de la calidad del contenido original

## Resultados y Exportación

### Formatos de Salida

#### CSV (términos principales)
```csv
Término,Frecuencia
computer,1250
internet,890
technology,756
```

#### JSON (datos completos)
```json
{
  "summary": {
    "total_documents": 600,
    "documents_with_content": 580,
    "total_unique_terms": 15420,
    "elapsed_time_minutes": 85.2
  },
  "top_terms": [...],
  "frequencies": {...},
  "analysis_metadata": {...}
}
```

### Métricas de Calidad

El sistema proporciona métricas detalladas:

- **Tasa de éxito de descargas**: % de documentos procesados exitosamente
- **Distribución temporal**: Documentos por año
- **Validación de idioma**: % de documentos validados como inglés
- **Tiempo de procesamiento**: Duración total del análisis

## Casos de Uso

### Investigación Sociolingüística

- Análisis de evolución terminológica en períodos específicos
- Estudio de emergencia de nuevos términos tecnológicos
- Comparación de frecuencias entre diferentes décadas

### Investigación Digital Humanities

- Análisis de cambios en el discurso web histórico
- Estudio de tendencias temáticas en documentos archivados
- Investigación de patrones de uso de lenguaje en la web temprana

### Análisis de Tendencias Tecnológicas

- Identificación de términos emergentes en tecnología
- Análisis retrospectivo de adopción de conceptos
- Estudio de evolución del vocabulario técnico

## Testing y Validación

### Suite de Pruebas

El sistema incluye una suite completa de pruebas unitarias:

```bash
python test_historical_analyzer.py
```

#### Categorías de Pruebas

- **Pruebas unitarias**: Cada componente individual
- **Pruebas de integración**: Flujo completo del sistema
- **Pruebas de validación**: Filtros y límites del sistema
- **Pruebas de casos límite**: Manejo de errores y situaciones extremas

### Ejecución de Pruebas

```bash
# Ejecutar todas las pruebas
python -m unittest test_historical_analyzer.py -v

# Ejecutar pruebas específicas
python -m unittest test_historical_analyzer.TestInternetArchiveClient -v
```

## Métricas de Rendimiento

### Benchmarks Típicos

- **Búsqueda**: ~2-3 segundos por página de resultados
- **Descarga**: ~4-6 segundos por documento (incluyendo rate limiting)
- **Procesamiento**: ~0.1-0.5 segundos por documento
- **Análisis completo**: 60-90 minutos para 600 documentos

### Optimizaciones Implementadas

- Búsqueda paginada para manejar grandes volúmenes
- Cache de resultados durante la sesión
- Procesamiento eficiente de texto con regex optimizadas
- Manejo inteligente de errores y reintentos

## Estructura del Código

### Archivos Principales

```
/
├── historical_term_analyzer.py    # Sistema principal
├── test_historical_analyzer.py    # Suite de pruebas
├── README.md                      # Esta documentación
└── examples/                      # Ejemplos de uso
    ├── basic_analysis.py          # Análisis básico
    ├── advanced_filtering.py      # Filtrado avanzado
    └── batch_processing.py        # Procesamiento por lotes
```

### Clases Principales

- `HistoricalTermAnalyzer`: Orquestador principal
- `InternetArchiveClient`: Cliente API
- `TextProcessor`: Procesador NLP
- `Document`: Modelo de datos
- `SessionMemory`: Gestión de memoria
- `Exporter`: Exportación de resultados
- `Visualizer`: Visualización de datos

## Licencia y Contribuciones

### Licencia

Este proyecto está desarrollado con fines educativos y de investigación. Respeta las políticas de uso de Internet Archive.

### Contribuciones

Para contribuir al proyecto:

1. Fork del repositorio
2. Crear branch para features: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. Push al branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## Contacto y Soporte

### Documentación Adicional

- [Internet Archive API Documentation](https://archive.org/developers/index-apis.html)
- [Wayback Machine API Reference](https://archive.org/help/wayback_api.php)

### Solución de Problemas Comunes

#### Error de Rate Limiting (429)
```
Solución: Incrementar rate_limit_delay a 5-6 segundos
analyzer = HistoricalTermAnalyzer(rate_limit_delay=6.0)
```

#### Sin resultados encontrados
```
Solución: Ampliar rango de años o reducir especificidad de filtros
```

#### Contenido no en inglés
```
Solución: El sistema filtra automáticamente, pero puedes ajustar 
los umbrales en validate_english_content()
```

---

**Desarrollado para**: Investigadores sociolingüísticos y académicos  
**Versión**: 1.0  
**Fecha**: Septiembre 2025  
**Autor**: Sistema de IA Especializado