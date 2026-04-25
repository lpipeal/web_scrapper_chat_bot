import asyncio

from src.app.web_scrapper import web_scraping_init

async def main():
    await web_scraping_init("https://www.celsia.com/es/mapa-del-sitio/")


if __name__ == "__main__":
    asyncio.run(main())
