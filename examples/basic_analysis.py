#!/usr/bin/env python3
"""
Ejemplo Básico - Analizador Histórico de Términos
Demonstra el uso básico del sistema para analizar documentos web históricos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from historical_term_analyzer import HistoricalTermAnalyzer


def basic_analysis_example():
    """
    Ejemplo de análisis básico del período 1995-2005
    """
    
    print("="*60)
    print("EJEMPLO BÁSICO - ANÁLISIS HISTÓRICO DE TÉRMINOS")
    print("="*60)
    print()
    
    # Inicializar analizador con configuración básica
    print("Inicializando analizador...")
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=4.0)
    
    # Configurar parámetros de análisis
    print("Configurando parámetros de análisis:")
    print("- Período: 1995-2005")
    print("- Máximo documentos: 50 (demo)")
    print("- Idioma: Inglés")
    print()
    
    # Ejecutar análisis
    print("Iniciando análisis... (esto puede tomar varios minutos)")
    print()
    
    results = analyzer.analyze_period(
        start_year=1995,
        end_year=2005,
        max_documents=50,  # Reducido para demostración
        language='eng'
    )
    
    # Verificar resultados
    if 'error' in results:
        print(f"❌ Error en el análisis: {results['error']}")
        return
    
    # Mostrar resultados
    print("✅ Análisis completado exitosamente!")
    print()
    
    # Mostrar resumen
    analyzer.display_results(results, top_n=20)
    
    # Exportar resultados
    print("\n📁 Exportando resultados...")
    analyzer.export_results(results, output_dir='.')
    
    print("\n" + "="*60)
    print("ANÁLISIS COMPLETADO")
    print("Los archivos de resultados han sido generados en el directorio actual")
    print("- CSV: Contiene los términos más frecuentes")
    print("- JSON: Contiene todos los datos del análisis")
    print("="*60)


def mini_analysis_example():
    """
    Ejemplo de análisis rápido con muy pocos documentos para pruebas
    """
    
    print("="*60)
    print("EJEMPLO MINI - ANÁLISIS RÁPIDO (5 DOCUMENTOS)")
    print("="*60)
    print()
    
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=2.0)
    
    print("Ejecutando análisis mini para pruebas rápidas...")
    
    results = analyzer.analyze_period(
        start_year=2000,
        end_year=2002,
        max_documents=5,  # Solo 5 documentos para prueba rápida
        language='eng'
    )
    
    if 'error' not in results:
        print("✅ Mini análisis completado!")
        
        # Mostrar solo resumen
        summary = results['summary']
        print(f"\nDocumentos procesados: {summary['total_documents']}")
        print(f"Documentos con contenido: {summary['documents_with_content']}")
        print(f"Términos únicos: {summary['total_unique_terms']}")
        print(f"Tiempo: {summary['elapsed_time_minutes']:.1f} minutos")
        
        # Mostrar top 10 términos
        if results['top_terms']:
            print("\nTop 10 términos más frecuentes:")
            for i, (term, freq) in enumerate(results['top_terms'][:10], 1):
                print(f"{i:2d}. {term:<15} {freq:>3} ocurrencias")
    else:
        print(f"❌ Error: {results['error']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejemplos del Analizador Histórico')
    parser.add_argument('--tipo', choices=['basico', 'mini'], default='mini',
                       help='Tipo de análisis a ejecutar')
    
    args = parser.parse_args()
    
    try:
        if args.tipo == 'basico':
            basic_analysis_example()
        else:
            mini_analysis_example()
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("Verifique su conexión a internet y vuelva a intentar")