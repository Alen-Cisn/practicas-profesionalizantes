#!/usr/bin/env python3
"""
Script de prueba rápida para verificar conectividad con CDX API
"""

import requests
import json

def test_cdx_simple():
    """Test simple del CDX API"""
    
    # Búsqueda muy simple - solo 5 resultados de CNN en 2005
    url = "http://web.archive.org/cdx/search/cdx"
    params = {
        'url': 'cnn.com/*',
        'from': '20050101',
        'to': '20051231',
        'output': 'json',
        'limit': 5,
        'fl': 'timestamp,original,mimetype'
    }
    
    print("🔍 Probando conexión con Internet Archive CDX API...")
    print(f"URL: {url}")
    print(f"Parámetros: {params}")
    print("\n" + "="*60)
    
    try:
        response = requests.get(url, params=params, timeout=60)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Resultados recibidos: {len(data)} entradas")
                
                if len(data) > 0:
                    print("\n📄 Primeras 3 entradas:")
                    for i, entry in enumerate(data[:3], 1):
                        print(f"\n{i}. {entry}")
                    
                    print("\n✅ ¡CDX API está funcionando correctamente!")
                    return True
                else:
                    print("\n⚠️ No se encontraron resultados (puede ser normal)")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parseando JSON: {e}")
                print(f"Respuesta: {response.text[:200]}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - El servidor tardó demasiado en responder")
        print("Posibles causas:")
        print("  - Internet Archive está sobrecargado")
        print("  - Tu conexión es lenta")
        print("  - Firewall bloqueando la conexión")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
        print("Posibles causas:")
        print("  - No hay conexión a Internet")
        print("  - Internet Archive está caído")
        print("  - Proxy o firewall bloqueando")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_alternative_search():
    """Probar búsqueda alternativa más específica"""
    
    print("\n\n🔍 Probando búsqueda alternativa (por año específico)...")
    print("="*60)
    
    url = "http://web.archive.org/cdx/search/cdx"
    params = {
        'url': 'bbc.co.uk/news/*',
        'from': '20050601',
        'to': '20050630',
        'output': 'json',
        'limit': 3,
        'fl': 'timestamp,original'
    }
    
    print(f"Buscando: bbc.co.uk/news en Junio 2005 (solo 3 resultados)")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Encontrados: {len(data)} resultados")
            
            if len(data) > 0:
                print("\n📄 URLs encontradas:")
                for entry in data[:3]:
                    if len(entry) >= 2:
                        print(f"  - {entry[1]}")
                return True
            else:
                print("⚠️ Sin resultados")
                return False
        else:
            print(f"❌ Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test de Conectividad con Internet Archive CDX API")
    print("="*60)
    
    # Test 1: Búsqueda simple
    test1 = test_cdx_simple()
    
    # Test 2: Búsqueda alternativa
    test2 = test_alternative_search()
    
    print("\n\n" + "="*60)
    print("📊 RESUMEN:")
    print(f"  Test 1 (Búsqueda simple): {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Test 2 (Búsqueda alternativa): {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 or test2:
        print("\n✅ La conexión con CDX API funciona.")
        print("💡 Si el análisis principal falla, puede ser por:")
        print("   - Timeouts debido a búsquedas muy amplias")
        print("   - Rate limiting del servidor")
        print("   - Dominios con pocas páginas archivadas")
    else:
        print("\n❌ Hay problemas de conectividad con CDX API")
        print("💡 Recomendaciones:")
        print("   - Verificar conexión a Internet")
        print("   - Intentar más tarde (servidor puede estar sobrecargado)")
        print("   - Usar un VPN si está bloqueado")
    
    print("="*60)
