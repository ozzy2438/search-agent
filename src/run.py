import os
from app import app
from config import Config
from hypercorn.config import Config as HyperConfig
from hypercorn.asyncio import serve
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    config = HyperConfig()
    config.bind = [f"0.0.0.0:{Config.PORT}"]
    config.use_reloader = Config.DEBUG
    config.insecure_bind = True
    
    logger.info(f"Server starting on http://localhost:{Config.PORT}")
    await serve(app, config)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except OSError as e:
        if e.errno == 48:  # Address already in use
            logger.error(f"Port {Config.PORT} is already in use.")
            logger.info("Try running these commands to kill the process using the port:")
            logger.info(f"lsof -i :{Config.PORT} | grep LISTEN")
            logger.info(f"kill -9 <PID>")
        else:
            raise e
    