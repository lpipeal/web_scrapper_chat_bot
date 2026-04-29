import asyncio

from src.app.web_scrapper import web_scraping_init
from src.preprocess import create_master_context, create_master_context_clean

async def main():
    await web_scraping_init("https://www.celsia.com/es/mapa-del-sitio/")
    await create_master_context(input_dir="celsia_knowledge_base_clean", output_file="master_context_text.txt")

if __name__ == "__main__":
    asyncio.run(main())
