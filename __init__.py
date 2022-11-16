# name = GichCO. Бот для погоды
# user_name = gichcoweather_bot
# Token = 5661804749:AAExB906zhuSfqCMvEIKQR32cALFUAZ8dM0

import sys
import os 
from WeatherBot import main

bot = main.weather_bot()
bot.set_token('5661804749:AAExB906zhuSfqCMvEIKQR32cALFUAZ8dM0')
bot.run()

