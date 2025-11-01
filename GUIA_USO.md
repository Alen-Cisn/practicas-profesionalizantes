# Guía de Uso - Historical Term Analyzer v2.1

## Inicio Rápido

### 1. Ejecutar la Aplicación

```bash
cd /home/alen/projects/practicas-profesionalizantes

# Ejecución estándar
streamlit run streamlit_app.py

# Con optimizaciones de rendimiento (recomendado)
ENABLE_PERFORMANCE_OPTS=true ENABLE_PERF_MONITORING=true streamlit run streamlit_app.py
```

#### Nuevas Variables de Entorno 🚀

- **`ENABLE_PERFORMANCE_OPTS=true`**: Activa optimizaciones de rendimiento
  - Cache multinivel (HTML parseado, términos extraídos)
  - Worker pools dinámicos (paralelización)
  - Connection pooling (reutilización de conexiones HTTP)
  - **Beneficio**: 40-60% más rápido en análisis de 300+ páginas
  
- **`ENABLE_PERF_MONITORING=true`**: Activa monitoreo de rendimiento
  - Dashboard de métricas en la barra lateral
  - Tiempo de ejecución por fase
  - Tasa de aciertos de cache
  - Uso de memoria en tiempo real
  - **Beneficio**: Visibilidad completa del rendimiento del análisis

### 2. Configurar el Análisis

En la barra lateral izquierda:

#### Período de Análisis

- **Año inicio**: Selecciona el año de inicio (ej: 2000)
- **Año fin**: Selecciona el año final (ej: 2005)

#### Parámetros

- **Máximo de páginas web**: 50-1000 (recomendado: 300-500)
- **Dominios**: Selecciona los sitios web a analizar
  - Predefinidos: CNN, BBC, NY Times, etc.
  - Personalizado: Agrega tu propio dominio

#### Configuración Avanzada

- **Delay entre requests**: 0.5-5.0 segundos (recomendado: 1.0)
- **Procesamiento paralelo**: Mantener activado para mejor rendimiento

### 3. Ejecutar Análisis

1. Haz clic en "▶️ Ejecutar Análisis"
2. El botón desaparecerá y verás:
   - 🔄 Barra de progreso en tiempo real
   - 📊 Porcentaje actual (0-100%)
   - 📝 Mensaje de estado detallado
   - 📋 Log de eventos en la columna derecha

**Progreso típico:**

- 0-10%: Búsqueda en Internet Archive
- 10-75%: Descarga de contenido (actualización continua)
- 75-90%: Análisis de términos
- 90-100%: Generación de resultados

### 4. Visualizar Resultados

#### Pestaña 1: Resultados Agregados

- Top términos de todos los años combinados
- Gráfico de barras horizontal interactivo
- Tabla con términos y frecuencias
- Slider para ajustar cantidad de términos mostrados

#### Pestaña 2: Resultados por Año ⭐ NUEVO

- Tabs individuales para cada año
- Métricas por año:
  - Documentos analizados
  - Términos únicos
  - Término más frecuente
- Gráficos comparativos entre años
- Visualización de tendencias temporales

#### Pestaña 3: Distribución

- Histograma de frecuencias
- Estadísticas descriptivas
- Términos por rango de frecuencia

#### Pestaña 4: Datos Detallados

- Lista de páginas web analizadas
- Distribución por año
- Metadatos del análisis

#### Pestaña 5: Exportar

- **CSV**: Top términos y frecuencias
- **JSON**: Datos completos del análisis

### 5. Historial de Análisis ⭐ NUEVO

#### Ver Análisis Previos

- Automáticamente se guardan hasta 10 análisis
- Selector dropdown en la parte superior de resultados
- Formato: "YYYY-MM-DD HH:MM - YYYY-YYYY (XXX docs)"

#### Navegar entre Análisis

1. Abre el selector "Seleccionar análisis"
2. Elige un análisis previo
3. Los resultados se actualizan automáticamente

#### Limpiar Historial

- Botón "🗑️ Limpiar Historial"
- Elimina todos los análisis guardados
- Libera memoria RAM

## Características Principales

### ✨ Nuevas en v2.1 (Performance & Testing)

1. **Optimizaciones de Rendimiento (40-60% más rápido)**
   - Cache multinivel con LRU eviction (>40% hit rate)
   - Worker pools dinámicos (2-8 workers según CPU)
   - Connection pooling para API requests
   - Requiere: `ENABLE_PERFORMANCE_OPTS=true`

2. **Monitoreo de Rendimiento**
   - Dashboard en barra lateral con métricas en tiempo real
   - Tiempo de ejecución por fase (search, download, parse, analyze)
   - Tasa de aciertos de cache
   - Uso de memoria actual y pico
   - Requiere: `ENABLE_PERF_MONITORING=true`

3. **Gestión de Memoria (<500MB)**
   - Garbage collection automático después de cada análisis
   - Historial limitado a 10 análisis (LRU eviction)
   - Advertencia visual cuando memoria > 450MB
   - Lazy-loading de visualizaciones (carga bajo demanda)

4. **Manejo de Errores API**
   - Detección de errores consecutivos (threshold: 10)
   - Pausa automática con notificación al usuario
   - Opción de reintentar después de errores

5. **Framework de Testing E2E**
   - 16 tests automatizados con Playwright
   - Cobertura: workflow, visualización, export, responsive
   - CI/CD integration con GitHub Actions
   - Ver: `docs/TESTING.md` para más detalles

### ✨ Características v2.0

1. **Progreso en Tiempo Real**
   - Barra de progreso dinámica que refleja el avance real
   - Mensajes de estado descriptivos
   - Actualización cada 5 segundos o 10 páginas

2. **Análisis por Año**
   - Resultados separados para cada año
   - Comparaciones visuales entre períodos
   - Identificación de tendencias temporales

3. **Sistema de Historial**
   - Hasta 10 análisis en memoria (con LRU eviction)
   - Navegación rápida entre resultados
   - Almacena solo datos esenciales para optimizar memoria

4. **Mejor UX**
   - Botón de análisis se oculta durante ejecución
   - Prevención de análisis múltiples simultáneos
   - Feedback visual mejorado

### 🚀 Rendimiento

**Con optimizaciones activadas** (`ENABLE_PERFORMANCE_OPTS=true`):

- **Velocidad típica**:
  - 100 páginas: ~3-6 minutos
  - 300 páginas: ≤15 minutos (objetivo cumplido) ✅
  - 500 páginas: ~20-30 minutos

**Sin optimizaciones** (legacy):
  - 100 páginas: ~5-10 minutos
  - 300 páginas: ~20-25 minutos
  - 500 páginas: ~35-45 minutos

**Mejora**: 40-60% reducción en tiempo de ejecución

**Uso de memoria**: <500MB constante (verificado con 5+ análisis consecutivos) ✅

## Ejemplos de Uso

### Caso 1: Análisis Rápido

```
Período: 2000-2002
Páginas: 100
Dominios: cnn.com, bbc.co.uk
Tiempo estimado: ~8 minutos
```

### Caso 2: Análisis Detallado

```
Período: 2000-2005
Páginas: 500
Dominios: 5 principales sitios de noticias
Tiempo estimado: ~30 minutos
```

### Caso 3: Análisis Comparativo

```
1. Ejecutar análisis 2000-2002
2. Ejecutar análisis 2003-2005
3. Usar historial para comparar resultados
4. Analizar cambios en términos populares
```

## Interpretación de Resultados

### Términos Agregados

- Muestra palabras más usadas en todo el período
- Útil para temas generales y constantes
- Base de comparación para años individuales

### Términos por Año

- Permite identificar eventos específicos del año
- Muestra evolución del vocabulario
- Detecta tendencias emergentes

### Comparaciones entre Años

- Gráficos de barras agrupadas
- Frecuencia de términos top de un año en otros años
- Identifica términos que ganaron/perdieron relevancia

## Solución de Problemas

### No se encuentran páginas

- Ampliar rango de años
- Agregar más dominios
- Verificar conectividad a Internet Archive

### Análisis muy lento

- Reducir número de páginas
- Aumentar delay entre requests
- Verificar conexión a internet

### Error durante descarga

- Internet Archive puede estar limitando requests
- Esperar unos minutos y reintentar
- Reducir número de páginas simultáneas

### Resultados vacíos por año

- Algunos años pueden tener pocas páginas
- Verificar en "Distribución por año"
- Considerar ampliar rango temporal

## Tips para Mejores Resultados

1. **Dominios**: Mezclar sitios de noticias con blogs/foros
2. **Período**: 3-5 años da buenos resultados comparativos
3. **Páginas**: 300-500 es el sweet spot entre tiempo y calidad
4. **Delay**: 1.0 segundos previene rate limiting
5. **Historial**: Guardar análisis interesantes antes de limpiar

## Límites y Consideraciones

- **Memoria**: Historial limitado a 10 análisis
- **Tiempo**: Análisis grandes pueden tomar 30+ minutos
- **Rate Limiting**: Internet Archive puede limitar requests
- **Contenido**: Solo páginas en inglés son procesadas
- **Calidad**: Depende de disponibilidad en Archive

## Próximos Pasos

Después de un análisis exitoso:

1. ✅ Revisar términos agregados para panorama general
2. ✅ Explorar resultados por año para detalles temporales
3. ✅ Exportar datos para análisis adicional
4. ✅ Ejecutar nuevos análisis con diferentes parámetros
5. ✅ Comparar resultados usando el historial

---

**¿Necesitas ayuda?** Revisa el log de análisis (columna derecha) para mensajes de error detallados.
