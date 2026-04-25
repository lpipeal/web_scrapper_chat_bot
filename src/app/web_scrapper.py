
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

async def start_scraping_process_clean(urls: list):
    output_dir = "celsia_knowledge_base_clean"
    os.makedirs(output_dir, exist_ok=True)

    print(f"🚀 Iniciando consolidación de {len(urls)} fuentes...")

    browser_config = BrowserConfig(headless=True, enable_stealth=True)

    # Usamos BYPASS para forzar la limpieza real y no traer basura del caché
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="body",
        wait_for_images=False,
        # Eliminamos selectores redundantes aquí, ya que BeautifulSoup hará el trabajo pesado
        excluded_tags=['nav', 'footer', 'aside', 'header', 'form', 'noscript', 'svg', 'script', 'style']
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=run_config)

        for res in results:
            clean_name = re.sub(r'https?://', '', res.url)
            clean_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name).strip('_')
            file_path = os.path.join(output_dir, f"{clean_name}.txt")

            if not res.success:
                continue

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"FUENTE ORIGINAL: {res.url}\n")
                f.write("-" * 50 + "\n\n")

                # Caso redes sociales
                if any(s in res.url for s in ['facebook', 'instagram', 'twitter', 'linkedin', 'youtube']):
                    f.write("LINK OFICIAL DE RED SOCIAL: Celsia tiene presencia aquí.\n")
                    continue

                # --- PROCESAMIENTO CON BEAUTIFULSOUP ---
                soup = BeautifulSoup(res.html, "html.parser")

                # 1. Eliminar ruido global y elementos de interfaz de carruseles
                # Quitamos selectores de paginación y navegación de sliders
                ui_selectors = "header, footer, nav, aside, noscript, svg, script, style, .swiper-button-next, .swiper-button-prev, .swiper-pagination, .owl-nav, .owl-dots"
                for tag in soup.select(ui_selectors):
                    tag.decompose()

                # 2. Extraer contenido principal (Prioridad <main>)
                main_content = soup.select_one("main")
                if not main_content:
                    main_content = soup.select_one("article") or soup.select_one(".content") or soup

                # 3. Limpiar elementos internos irrelevantes (botones, inputs, etc.)
                for tag in main_content.select("form, button, input, iframe, .pagination, .page-numbers"):
                    tag.decompose()

                # 4. Extraer texto y aplicar filtros de calidad
                raw_text = main_content.get_text(separator="\n", strip=True)
                lines = raw_text.split('\n')
                
                final_lines = []
                last_line = ""
                
                # Lista de frases de navegación que no aportan valor a la base vectorial
                noise_phrases = ["ver más", "conoce más", "inicia sesión", "paga tu factura", "hablemos", "clic aquí", "subir", "centro de relevo"]

                for line in lines:
                    clean_line = line.strip()
                    
                    # A. Filtro: Omitir números de paginación de carrusel (ej: "1 / 9")
                    if re.match(r'^\d+\s*/\s*\d+$', clean_line):
                        continue
                    
                    # B. Filtro: Omitir frases de ruido UI
                    if clean_line.lower() in noise_phrases:
                        continue
                    
                    # C. Filtro: Evitar duplicados consecutivos (clones de sliders) y líneas vacías
                    if clean_line != last_line and len(clean_line) > 1:
                        final_lines.append(clean_line)
                        last_line = clean_line

                # 5. Unir y normalizar saltos de línea
                text = '\n\n'.join(final_lines)
                f.write(text)

            print(f"✅ Guardado y Limpio: {clean_name}.txt")

    print(f"\n✨ Proceso terminado. Los archivos en '{output_dir}' están listos para tu base vectorial.")


async def start_scraping_process_markdown(urls: list[str]) -> list[dict]:
        
    # Esquema universal para componentes de International 
    config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED,
                excluded_tags=['nav', 'footer', 'aside', 'header', 'form',],
                excluded_selector=['.adsbygoogle', '.popup-ad', '#subscribe-modal', '.btn', '.button', '.nav', '.footer', '.header'],
                # wait_for=".main",
                js_code="window.scrollTo(0, document.body.scrollHeight);", # Forzamos carga de componentes lazy
                # css_selector="#content",
                remove_overlay_elements=True,
                exclude_external_images=True,
                exclude_social_media_links=True,
                exclude_social_media_domains=[
                    'facebook.com',
                    'twitter.com',
                    'x.com',
                    'linkedin.com',
                    'instagram.com',
                    'pinterest.com',
                    'tiktok.com',
                    'snapchat.com',
                    'reddit.com',
                ],
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0),
                    options={
                        "ignore_links": True
                    }
                    
                ),
            )    
    
    
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        # max_session_permit=10,
        # monitor=CrawlerMonitor(
        #     display_mode=DisplayMode.DETAILED
        # )
    )
    
    async with AsyncWebCrawler() as crawler:
        # Ejemplo con la serie CV
        results = await crawler.arun_many(
            urls=urls,
            config=config,
            dispatcher=dispatcher,
        )

    return await process_result(results)
    

async def process_result(results) -> list[dict]:
    # Creamos la carpeta de destino si no existe
    output_dir = "celsia_knowledge_base_markdown"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for res in results:
            # 1. Generar un nombre de archivo seguro basado en la URL
            # Ejemplo: https://celsia.com/es/pymes -> es_pymes.txt
            clean_name = re.sub(r'https?://', '', res.url)
            clean_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name).strip('_')
            file_path = os.path.join(output_dir, f"{clean_name}.txt")

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
                
                print(f"✅ Guardado: {clean_name}.txt")
