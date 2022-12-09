# name = GichCO. Бот для погоды
import logging
format = '%(asctime)s - %(message)s'
logging.basicConfig(filename='log_file_start.log', filemode='w', level=logging.INFO, format=format)
logger = logging.getLogger(__name__)
try:
    
    import main

    bot = main.weather_bot()
    bot.run()

except Exception as e:
    logger.error(str(e))
    