# name = GichCO. Бот для погоды
import logging
import os
import sys 
os.chdir('/home/global_admin/weather_bot/')
try:
    
    import main

    format = '%(asctime)s - %(message)s'
    logging.basicConfig(filename='\log_file_start.log', filemode='w', level=logging.INFO, format=format)
    logger = logging.getLogger(__name__)

    bot = main.weather_bot()
    bot.run()

except Exception as e:
    pass
    # logger.error(str(e))
    