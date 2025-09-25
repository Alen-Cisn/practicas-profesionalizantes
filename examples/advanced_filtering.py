#!/usr/bin/env python3
"""
Ejemplo Avanzado - Filtrado y Configuración Especializada
Demuestra capacidades avanzadas de filtrado y análisis específico
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from historical_term_analyzer import HistoricalTermAnalyzer, TextProcessor


def technology_terms_analysis():
    """
    Análisis enfocado en términos relacionados con tecnología
    """
    
    print("="*60)
    print("ANÁLISIS ESPECIALIZADO - TÉRMINOS TECNOLÓGICOS")
    print("="*60)
    print()
    
    # Términos de búsqueda específicos para tecnología
    tech_terms = [
        'computer', 'internet', 'software', 'technology', 'digital',
        'website', 'email', 'programming', 'database', 'network',
        'server', 'browser', 'web', 'online', 'cyber'
    ]
    
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=4.5)
    
    print("🔍 Búsqueda especializada en términos tecnológicos:")
    print(f"Términos objetivo: {', '.join(tech_terms[:5])}...")
    print("Período: 1995-2005 (Era del Internet temprano)")
    print()
    
    results = analyzer.analyze_period(
        start_year=1995,
        end_year=2005,
        max_documents=100,
        language='eng',
        search_terms=tech_terms
    )
    
    if 'error' not in results:
        print("✅ Análisis tecnológico completado!")
        
        # Filtrar resultados para mostrar solo términos tecnológicos relevantes
        tech_frequencies = {}
        for term, freq in results['frequencies'].items():
            if (term in tech_terms or 
                any(tech_word in term.lower() for tech_word in ['comput', 'tech', 'digit', 'web', 'cyber', 'net', 'soft'])):
                tech_frequencies[term] = freq
        
        # Mostrar términos tecnológicos más frecuentes
        tech_top = sorted(tech_frequencies.items(), key=lambda x: x[1], reverse=True)[:15]
        
        print("\n🖥️ TOP 15 TÉRMINOS TECNOLÓGICOS:")
        print("-" * 40)
        for i, (term, freq) in enumerate(tech_top, 1):
            print(f"{i:2d}. {term:<15} {freq:>6} ocurrencias")
        
        # Exportar resultados especializados
        specialized_results = {
            'tech_summary': {
                'total_tech_terms': len(tech_frequencies),
                'period': '1995-2005',
                'focus': 'technology_terms'
            },
            'tech_frequencies': tech_frequencies,
            'tech_top_terms': tech_top,
            'original_summary': results['summary']
        }
        
        analyzer.exporter.export_to_json(specialized_results, 'tech_analysis_results.json')
        print("\n📁 Resultados especializados exportados a: tech_analysis_results.json")
        
    else:
        print(f"❌ Error: {results['error']}")


def comparative_periods_analysis():
    """
    Análisis comparativo entre diferentes períodos
    """
    
    print("\n" + "="*60)
    print("ANÁLISIS COMPARATIVO - DIFERENTES PERÍODOS")
    print("="*60)
    print()
    
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=5.0)
    
    # Definir períodos para comparar
    periods = [
        {'name': 'Pre-Internet', 'start': 1995, 'end': 1997},
        {'name': 'Dot-com Boom', 'start': 1998, 'end': 2001},
        {'name': 'Post-Bubble', 'start': 2002, 'end': 2005}
    ]
    
    comparative_results = {}
    
    for period in periods:
        print(f"📊 Analizando período: {period['name']} ({period['start']}-{period['end']})")
        
        results = analyzer.analyze_period(
            start_year=period['start'],
            end_year=period['end'],
            max_documents=30,  # Reducido por ser comparativo
            language='eng'
        )
        
        if 'error' not in results:
            comparative_results[period['name']] = {
                'period': f"{period['start']}-{period['end']}",
                'total_documents': results['summary']['total_documents'],
                'top_terms': results['top_terms'][:10],  # Solo top 10 por período
                'unique_terms': results['summary']['total_unique_terms']
            }
            print(f"✅ Completado - {results['summary']['total_documents']} documentos")
        else:
            print(f"❌ Error en período {period['name']}")
    
    # Mostrar resultados comparativos
    if comparative_results:
        print("\n📈 RESUMEN COMPARATIVO:")
        print("=" * 50)
        
        for period_name, data in comparative_results.items():
            print(f"\n{period_name} ({data['period']}):")
            print(f"  Documentos: {data['total_documents']}")
            print(f"  Términos únicos: {data['unique_terms']}")
            print("  Top 5 términos:")
            for i, (term, freq) in enumerate(data['top_terms'][:5], 1):
                print(f"    {i}. {term} ({freq})")
        
        # Exportar comparativa
        analyzer.exporter.export_to_json(comparative_results, 'comparative_analysis.json')
        print(f"\n📁 Análisis comparativo exportado a: comparative_analysis.json")


def custom_text_processing():
    """
    Ejemplo de procesamiento de texto personalizado
    """
    
    print("\n" + "="*60)
    print("PROCESAMIENTO DE TEXTO PERSONALIZADO")
    print("="*60)
    print()
    
    # Crear procesador personalizado
    processor = TextProcessor()
    
    # Texto de ejemplo para demostrar capacidades
    sample_texts = [
        """
        The World Wide Web was invented by Tim Berners-Lee in 1989. 
        This revolutionary technology transformed how we access information online.
        Websites, browsers, and HTML became fundamental components of the internet.
        """,
        """
        Computer programming languages like Java, C++, and Python gained popularity.
        Software development methodologies evolved to support web-based applications.
        Database management systems became crucial for storing digital information.
        """,
        """
        E-commerce platforms revolutionized online shopping and digital transactions.
        Cybersecurity became increasingly important as more businesses went digital.
        Network protocols and server technologies advanced rapidly during this period.
        """
    ]
    
    print("🔍 Analizando textos de ejemplo...")
    
    all_terms = []
    for i, text in enumerate(sample_texts, 1):
        terms = processor.extract_terms(text)
        all_terms.extend(terms)
        print(f"Texto {i}: {len(terms)} términos extraídos")
    
    # Calcular frecuencias
    from collections import Counter
    frequencies = Counter(all_terms)
    
    print(f"\nTotal de términos procesados: {len(all_terms)}")
    print(f"Términos únicos encontrados: {len(frequencies)}")
    
    # Mostrar términos más frecuentes
    top_terms = frequencies.most_common(10)
    print("\n🏆 TOP 10 TÉRMINOS EN TEXTOS DE EJEMPLO:")
    print("-" * 35)
    for i, (term, freq) in enumerate(top_terms, 1):
        print(f"{i:2d}. {term:<15} {freq} ocurrencias")
    
    # Análizar características del procesamiento
    print("\n📋 CARACTERÍSTICAS DEL PROCESAMIENTO:")
    print(f"- Stop words filtradas: {len(processor.STOP_WORDS)}")
    print(f"- Longitud mínima de palabras: 3 caracteres")
    print(f"- Conversión a minúsculas: ✅")
    print(f"- Filtrado de caracteres especiales: ✅")


def main():
    """Función principal para ejecutar ejemplos avanzados"""
    
    print("🚀 EJEMPLOS AVANZADOS - ANALIZADOR HISTÓRICO")
    print("Este script demuestra capacidades avanzadas del sistema")
    print()
    
    try:
        # Ejecutar análisis tecnológico
        technology_terms_analysis()
        
        # Ejecutar análisis comparativo
        comparative_periods_analysis()
        
        # Demostrar procesamiento personalizado
        custom_text_processing()
        
        print("\n" + "="*60)
        print("✅ TODOS LOS EJEMPLOS AVANZADOS COMPLETADOS")
        print("Revise los archivos generados para ver los resultados detallados")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        print("Detalles del error:")
        traceback.print_exc()


if __name__ == "__main__":
    main()