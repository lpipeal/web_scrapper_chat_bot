
import json

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator, MemoryAdaptiveDispatcher, PruningContentFilter

async def web_scraping_init(url: str, output_dir_clean: str, output_dir_markdown: str):
    urls = await get_seed_urls_with_social_networks(url)
    await start_scraping_process_clean(urls, output_dir_clean)
    await start_scraping_process_markdown(urls, output_dir_markdown)

async def get_seed_urls(url: str):
    # 1. Configuración del Navegador: SIMULAR SER HUMANO
    browser_config = BrowserConfig(
        headless=False, # Ponlo en True una vez funcione
        enable_stealth=True, 
        browser_type="chromium",
        # Estos argumentos son vitales para sitios con Incapsula
        extra_args=[
            "--disable-web-security",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
        ]
    )

    # 2. Configuración de Ejecución
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        # Forzamos una espera de 5 segundos para que Incapsula nos deje pasar
        # y el mapa del sitio se renderice completamente.
        wait_for="js:() => document.querySelectorAll('a').length > 50",
        delay_before_return_html=5.0, 
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Le pedimos a Crawl4AI que use su propio motor de descubrimiento de links
        scan_full_page=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("🔗 Accediendo a Celsia... espera un momento.")
        result = await crawler.arun(
            url=url,
            config=run_config
        )

        if result.success:
            # MÉTODO DE RESPALDO: Si el JS no devuelve nada, usamos los links detectados por el crawler
            all_links = []
            if result.links and "internal" in result.links:
                all_links = [l["href"] for l in result.links["internal"]]
            
            # Si aún así está vacío, intentamos extraer del Markdown que Crawl4AI generó
            if not all_links:
                import re
                # Extraer URLs usando regex del contenido markdown
                all_links = re.findall(r'\[.*?\]\((https?://www\.celsia\.com/[^\s\)]+)\)', result.markdown)

            # Limpieza y consolidación
            final_urls = set()
            for url in all_links:
                # Filtrar solo páginas reales, ignorando basura y archivos
                if "celsia.com/" in url:
                    clean_url = url.split('?')[0].split('#')[0].rstrip('/')
                    if not any(ext in clean_url.lower() for ext in ['.pdf', '.jpg', '.png', '.zip', '.gif', 'wp-json']):
                        final_urls.add(clean_url)
                    print(f"✅ URL válida encontrada: {clean_url}")

                else:
                    print(f"⚠️ URL ignorada (no es interna): {url}")
                    # Si es una URL relativa, convertirla a absoluta
                    # if url.startswith('/'):
                        # final_urls.add(f"https://www.celsia.com{url}")

            print(f"🎯 ¡Éxito! Se encontraron {len(final_urls)} URLs.")
            # print(f"Ejemplo de URL encontrada: {(final_urls), list(final_urls)[0] if final_urls else 'Ninguna'}")
            return list(final_urls)
        
        print(f"❌ Falló el acceso: {result.error_message}")
        return []


async def get_seed_urls_with_social_networks(url: str ):
     # 1. Configuración del Navegador: SIMULAR SER HUMANO
    browser_config = BrowserConfig(
        headless=False, # Ponlo en True una vez funcione
        enable_stealth=True, 
        browser_type="chromium",
        # Estos argumentos son vitales para sitios con Incapsula
        extra_args=[
            "--disable-web-security",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
        ]
    )

    # 2. Configuración de Ejecución
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        # Forzamos una espera de 5 segundos para que Incapsula nos deje pasar
        # y el mapa del sitio se renderice completamente.
        wait_for="js:() => document.querySelectorAll('a').length > 50",
        delay_before_return_html=5.0, 
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Le pedimos a Crawl4AI que use su propio motor de descubrimiento de links
        scan_full_page=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )

        if result.success:
            # Obtenemos TODOS los links detectados (internos y externos)
            raw_links = []
            if result.links:
                # Combinamos internos y externos para no perder las redes sociales
                raw_links = [l["href"] for l in result.links.get('internal', [])] + \
                            [l["href"] for l in result.links.get('external', [])]

            final_urls = set()
            social_domains = ['facebook.com', 'instagram.com', 'x.com', 'twitter.com', 'linkedin.com', 'youtube.com']
            
            for url in raw_links:
                if not url: continue
                
                # Caso 1: Es una red social oficial
                if any(domain in url.lower() for domain in social_domains):
                    # Solo guardamos si parece ser el perfil de Celsia
                    if "celsia" in url.lower():
                        final_urls.add(url.strip())
                
                # Caso 2: Es una página interna de Celsia
                elif "celsia.com" in url:
                    clean_url = url.split('?')[0].split('#')[0].rstrip('/')
                    if not any(ext in clean_url.lower() for ext in ['.pdf', '.jpg', '.png', '.zip']):
                        final_urls.add(clean_url)

            print(f"🎯 Total consolidado: {len(final_urls)} URLs (incluyendo Redes Sociales).")
            return list(final_urls)



import os
import re
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import os
import re
import socket
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import os
import re
import json
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# 1. Silenciamos los logs de la librería para que no ensucien la consola
logging.getLogger("crawl4ai").setLevel(logging.CRITICAL)

def domain_exists(url):
    """
    Verifica si el dominio de la URL realmente existe en internet 
    antes de intentar abrir el navegador.
    """
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return False
        # Intenta resolver el nombre de dominio (timeout de 2 seg)
        socket.gethostbyname(hostname)
        return True
    except (socket.gaierror, socket.timeout):
        return False


async def start_scraping_process_clean(urls: list, output_dir: str):
    """
    Scraper genérico que limpia ruido visual y guarda contenido + metadata.
    """
    os.makedirs(output_dir, exist_ok=True)
    metadata_map = {}

    print(f"🚀 Iniciando scraping de {len(urls)} URLs...")
    
    browser_config = BrowserConfig(headless=True, enable_stealth=True)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        excluded_tags=['nav', 'footer', 'header', 'aside', 'form', 'script', 'style', 'svg']
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=run_config)

        for res in results:
            if not res.success:
                print(f"⚠️ Error en: {res.url}")
                continue

            # 1. Generar nombre de archivo seguro y único
            # Quitamos protocolo y caracteres ilegales
            clean_url_name = re.sub(r'https?://', '', res.url)
            clean_url_name = re.sub(r'[\\/*?:"<>|]', '_', clean_url_name).strip('_')
            filename = f"{clean_url_name}.txt"
            file_path = os.path.join(output_dir, filename)

            # 2. Limpieza de contenido con BeautifulSoup
            soup = BeautifulSoup(res.html, "html.parser")
            
            # Intentamos encontrar el cuerpo principal (genérico)
            main_content = (
                soup.select_one("main") or 
                soup.select_one("article") or 
                soup.select_one("#content") or 
                soup.select_one(".main-content") or 
                soup
            )

            # Eliminar elementos de UI comunes que ensucian el texto
            for tag in main_content.select("button, input, iframe, .pagination, .social-share, [role='button']"):
                tag.decompose()

            # Extraer y limpiar líneas
            raw_text = main_content.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 2]
            
            # Filtro de ruido genérico (frases de navegación comunes)
            noise_phrases = {"ver más", "leer más", "clic aquí", "iniciar sesión", "cookies", "derechos reservados"}
            final_lines = [l for l in lines if l.lower() not in noise_phrases]

            # 3. Guardar el archivo de texto (Solo contenido)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write('\n\n'.join(final_lines))

            # 4. Registrar en el mapa de metadata
            metadata_map[filename] = {
                "url": res.url,
                "domain": clean_url_name.split('_')[0],
                "char_count": len('\n\n'.join(final_lines))
            }
            print(f"✅ Guardado: {filename}")

    # 5. Guardar el archivo maestro de metadata
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        # EL CAMBIO ESTÁ AQUÍ: de ensure_all_ascii a ensure_ascii
        json.dump(metadata_map, f, indent=4, ensure_ascii=False) 

    print(f"\n✨ Proceso terminado. Metadata generada en {output_dir}")


async def start_scraping_process_markdown(urls: list[str], output_dir: str) -> list[dict]:
    # --- PASO 1: VALIDACIÓN DNS Y FILTRADO ---
    print(f"🔍 Validando {len(urls)} dominios en la red...")
    ignore_keywords = ['login', 'kiosco', 'bienvenida', 'password', 'acceso']
    
    filtered_urls = [
        url for url in urls 
        if domain_exists(url) and not any(key in url.lower() for key in ignore_keywords)
    ]
    
    print(f"🚀 Procesando {len(filtered_urls)} URLs válidas (Se descartaron {len(urls) - len(filtered_urls)}).")

    # --- PASO 2: CONFIGURACIÓN CRAWLER ---
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, # BYPASS para asegurar que la limpieza se aplique a HTML fresco
        excluded_tags=['nav', 'footer', 'aside', 'header', 'form', 'noscript', 'svg', 'script', 'style'],
        excluded_selector=['.adsbygoogle', '.popup-ad', '#subscribe-modal', '.btn', '.button'],
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        remove_overlay_elements=True,
        exclude_external_images=True,
        exclude_social_media_links=True,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0),
            options={"ignore_links": True}
        ),
    )    


    dispatcher = MemoryAdaptiveDispatcher(
    memory_threshold_percent=90.0,  # Sube el límite al 90% (antes 70%)
    check_interval=2.0,           # Revisa cada 2 segundos en lugar de 1
    max_session_permit=5          # LIMITA a 5 pestañas máximo abiertas a la vez
)

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=filtered_urls,
            config=config,
            dispatcher=dispatcher,
            # --- Añade esto ---
            concurrency_count=5,           # No más de 5 procesos paralelos
            stream=False                   # Si son muchísimas URLs (ej. > 500), considera poner True
        )
    return await process_result_markdown(results, output_dir=output_dir)


async def process_result_markdown(results, output_dir: str) -> list[dict]:
    os.makedirs(output_dir, exist_ok=True)
    
    for res in results:
                # 1. Generar un nombre de archivo seguro basado en la URL
                # Ejemplo: https://celsia.com/es/pymes -> es_pymes.txt
                clean_name = re.sub(r'https?://', '', res.url)
                clean_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name).strip('_')
                file_path = os.path.join(output_dir, f"{clean_name}.md")

                if res.success:
                    with open(file_path, "w", encoding="utf-8") as f:
                        # f.write(f"FUENTE ORIGINAL: {res.url}\n")
                        # f.write("-" * 50 + "\n\n")
                        
                        # Si es red social, guardamos una nota informativa
                        if any(social in res.url for social in ['facebook', 'instagram', 'twitter', 'linkedin', 'youtube']):
                            f.write(f"LINK OFICIAL DE RED SOCIAL: Celsia tiene presencia aquí. ")
                            f.write("Consultar manualmente para actualizaciones de campañas en tiempo real.")
                        else:
                            # Si es web, guardamos el Markdown (ideal para RAG/LLM)
                            # f.write(res.markdown)
                            if hasattr(res, 'fit_markdown') and res.fit_markdown:
                                # f.write(res.fit_markdown)
                                f.write(res.markdown.fit_markdown) # Intentamos usar el resumen inteligente
                                
                            else:
                                f.write(res.markdown) # Respaldo por si falla
                    
                    print(f"✅ Guardado: {clean_name}.md")