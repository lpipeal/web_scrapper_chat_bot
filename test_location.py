def check_location_content_in_source(data_dir: str = "data/celsia_knowledge_base_clean"):
    """Busca archivos que contengan información de ubicación"""
    from pathlib import Path
    
    location_terms = ['sede', 'oficina', 'dirección', 'Cali', 'Valle del Cauca', 
                      'Colombia', 'cobertura', 'atención', 'teléfono', 'contacto']
    
    results = []
    for file in Path(data_dir).glob("*.txt"):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        matches = [term for term in location_terms if term.lower() in content]
        if matches:
            results.append({
                'file': file.name,
                'terms_found': matches,
                'snippet': [line.strip() for line in content.split('\n') 
                           if any(t in line.lower() for t in matches)][:3]
            })
    
    print(f"\n📍 Archivos con contenido de ubicación: {len(results)}/{len(list(Path(data_dir).glob('*.txt')))}")
    for r in results[:5]:  # Mostrar primeros 5
        print(f"\n📄 {r['file']}")
        print(f"   🔑 Términos: {r['terms_found']}")
        print(f"   ✂️  Snippets:")
        for s in r['snippet']:
            print(f"      • {s[:150]}...")
    
    return results

# Ejecutar:
# check_location_content_in_source()