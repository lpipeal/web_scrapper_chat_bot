
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator, MemoryAdaptiveDispatcher, PruningContentFilter


async def web_scraping_init(url: str):
    urls = await get_seed_urls_with_social_networks(url)
    await start_scraping_process_clean(urls)
    await start_scraping_process_markdown(urls)


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




# # --- LÓGICA DE PROCESAMIENTO MASIVO ---
async def start_scraping_process_simple(urls: list):
    """
    Procesa la lista de URLs descargando el contenido de cada una.
    """
    print(f"🚀 Iniciando scraping de {len(urls)} URLs...")
    
    # Configuración de rastreo para las páginas finales
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, # Ahorra ancho de banda si ya la vimos
        word_count_threshold=10,        # Evita páginas vacías
    )

    async with AsyncWebCrawler() as crawler:
        # Crawl4AI maneja la concurrencia internamente si le pasamos una lista
        results = await crawler.arun_many(urls=urls, config=run_config)
        
        # Aquí procesas los resultados (guardar en BD, JSON, etc.)
        for res in results:
            if res.success:
                # Aquí iría tu lógica de guardado: DB.save(res.markdown)
                print(f"✅ Procesado: {res.url} | Tamaño: {len(res.markdown)} chars")


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

async def start_scraping_process_clean(urls: list):
    output_dir = "celsia_knowledge_base_clean"
    os.makedirs(output_dir, exist_ok=True)

    # --- PASO 1: FILTRADO DINÁMICO POR DNS ---
    print(f"🔍 Validando {len(urls)} fuentes en la red...")
    
    # Filtramos: Solo dominios que existen + descartar palabras de login/acceso
    filtered_urls = [
        url for url in urls 
        if domain_exists(url) and not any(k in url.lower() for k in ['login', 'password', 'acceso'])
    ]

    print(f"🚀 Iniciando proceso con {len(filtered_urls)} fuentes válidas.")
    if len(urls) != len(filtered_urls):
        print(f"🧹 Se ignoraron {len(urls) - len(filtered_urls)} enlaces (caídos o irrelevantes).")

    browser_config = BrowserConfig(headless=True, enable_stealth=True)

    # --- PASO 2: CONFIGURACIÓN CON TIMEOUT ---
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=20000, # 20 segundos máximo por página
        wait_for="body",
        wait_for_images=False,
        excluded_tags=['nav', 'footer', 'aside', 'header', 'form', 'noscript', 'svg', 'script', 'style']
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Ejecutamos solo sobre las URLs que pasaron el filtro de DNS
        results = await crawler.arun_many(urls=filtered_urls, config=run_config)

        for res in results:
            if not res.success:
                # Aquí ya solo entrarían errores raros, no de DNS
                print(f"⚠️ Error inesperado en: {res.url}")
                continue

            # Nombre de archivo seguro
            clean_name = re.sub(r'https?://', '', res.url)
            clean_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name).strip('_')
            file_path = os.path.join(output_dir, f"{clean_name}.txt")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"FUENTE ORIGINAL: {res.url}\n")
                f.write("-" * 50 + "\n\n")

                # Caso Redes Sociales
                if any(s in res.url for s in ['facebook', 'instagram', 'twitter', 'linkedin', 'youtube']):
                    f.write("LINK OFICIAL DE RED SOCIAL: Consultar para campañas vigentes.")
                    continue

                # --- PASO 3: LIMPIEZA PROFUNDA CON BEAUTIFULSOUP ---
                soup = BeautifulSoup(res.html, "html.parser")

                # Borrar elementos de interfaz y menús móviles rebeldes
                ui_selectors = [
                    ".swiper-button-next", ".swiper-button-prev", ".swiper-pagination", 
                    ".owl-nav", ".owl-dots", ".content-menu-mobile", "#header-mobile-wrapper"
                ]
                for selector in ui_selectors:
                    for tag in soup.select(selector):
                        tag.decompose()

                # Contenido principal
                main_content = soup.select_one("main") or soup.select_one("article") or soup.select_one(".content") or soup

                # Quitar botones, inputs y paginadores internos
                for tag in main_content.select("form, button, input, iframe, .pagination"):
                    tag.decompose()

                # Limpiar texto y remover duplicados de carruseles
                raw_text = main_content.get_text(separator="\n", strip=True)
                lines = raw_text.split('\n')
                
                final_lines = []
                last_line = ""
                noise_phrases = ["ver más", "conoce más", "inicia sesión", "paga tu factura", "hablemos", "clic aquí", "subir"]

                for line in lines:
                    clean_line = line.strip()
                    
                    # Saltar indicadores "1 / 9" y frases de navegación
                    if re.match(r'^\d+\s*/\s*\d+$', clean_line) or clean_line.lower() in noise_phrases:
                        continue
                    
                    # Evitar duplicados seguidos (clones de sliders)
                    if clean_line != last_line and len(clean_line) > 1:
                        final_lines.append(clean_line)
                        last_line = clean_line

                f.write('\n\n'.join(final_lines))

            print(f"✅ Procesado: {clean_name}.txt")

    print(f"\n✨ ¡Listo! Revisa la carpeta: '{output_dir}'")


async def start_scraping_process_markdown(urls: list[str]) -> list[dict]:
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
    return await process_result_markdown(results)


async def process_result_markdown(results) -> list[dict]:
    output_dir = "celsia_knowledge_base_markdown"
    os.makedirs(output_dir, exist_ok=True)
    
    for res in results:
                # 1. Generar un nombre de archivo seguro basado en la URL
                # Ejemplo: https://celsia.com/es/pymes -> es_pymes.txt
                clean_name = re.sub(r'https?://', '', res.url)
                clean_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name).strip('_')
                file_path = os.path.join(output_dir, f"{clean_name}.md")

                if res.success:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"FUENTE ORIGINAL: {res.url}\n")
                        f.write("-" * 50 + "\n\n")
                        
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