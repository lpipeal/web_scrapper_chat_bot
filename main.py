import asyncio

from src.app.web_scrapper import web_scraping_init
from src.preprocess import create_master_context, create_master_context_clean

async def main():
    await web_scraping_init("https://www.celsia.com/es/mapa-del-sitio/")
    # await create_master_context_clean("celsia_knowledge_base_markdown", "master_context_clean.txt")
    # await create_master_context_clean("celsia_knowledge_base_clean", "master_context_clean.txt")
    await create_master_context(input_dir="celsia_knowledge_base_clean")
    # await create_master_context(input_dir="celsia_knowledge_base_markdown")


if __name__ == "__main__":
    asyncio.run(main())
