import json
import logging
import re
import sys
import api_weather

from telegram import *
from telegram.ext import *


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

        
class weather_bot():

    # Базовые функции класса
    def __init__(self) -> None:
        self.YES,self.NO = range(2)
        self.weather_api = api_weather.WeatherAPI()
        self.bot_menu = self.set_menu_commands()
        self.bot_msg = self.set_msg()
        self.bot_keyboards = self.set_keyboards()

    def set_token(self, tg_token) -> None:
        self.tg_token = tg_token

    def set_menu_commands(self) -> list:
        json_file_name = "menu.json"
        commands_list = []

        with open(json_file_name,"r",encoding="utf-8") as json_file:
            for cmd in json.loads(json_file.read()):
                commands_list.append((cmd['cmd'],cmd['description']))

        return commands_list
    
    def set_msg(self) -> dict:
        json_file_name = "msg.json"
        msg_dict = dict()
        
        with open(json_file_name,encoding="utf-8") as json_file:
            for cmd in json.loads(json_file.read()):
                msg_dict[cmd['command']] = str(cmd['message'])

        return msg_dict

    def set_keyboards(self,resize = True):
        keyboard = []
        keyboards_dict = dict()
        json_file_name = "keyboards.json"
        
        with open(json_file_name,"r",encoding="utf-8") as json_file:
            keyboards_list = json.loads(json_file.read())
            for key in keyboards_list:
                btn_list = []
                
                for btn in keyboards_list[key]:
                    if btn['callback_data'] == "YES":
                        callback_data = self.YES
                    if btn['callback_data'] == "NO":
                        callback_data = self.NO
                        
                    btn_list.append(
                        InlineKeyboardButton(
                            btn['title'],
                            callback_data = callback_data))
                    
                keyboards_dict[key] = InlineKeyboardMarkup([btn_list])

        return keyboards_dict

    # Команды для бота
    def start (self, update: Update, context: CallbackContext) -> None:
        """
        Обработка команды /start
        """
        
        logger.info("User %s starts bot session", update.message.from_user.first_name)
        
        #Сообщене приветствия
        update.message.reply_text(text=self.bot_msg['greeting'])
        #Вопрос на продолжение
        update.message.reply_text(text = self.bot_msg['greeting_q'], 
                                  reply_markup= self.bot_keyboards['greeting_q'])
    
    def start_commit(self, update, context) -> None:
        """
        Обработка callback = self.YES и начало диалога get_city
        """
        query = update.callback_query
        query.answer()
        context.user_data['isStart'] = True
        
        logger.info("User %s starts [start_commit]", query.message.chat.username)
        query.edit_message_text(text=self.bot_msg['start_commit'])
        
        #Начало запроса города
        self.get_city(query, context)

    def start_negative(self, update: Update, _) -> None:
        """
        Обработка callback = self.NO
        """
        query = update.callback_query
        query.edit_message_text(text=self.bot_msg['start_negative'])
    
    def end(self, update: Update, context: CallbackContext):
        pass
    
    def get_city(self, update, context) -> None:
        logger.info("User starts self.get_city")
        
        #Вывод сообщения на запрос города
        update.message.reply_text(text=self.bot_msg['ask_city'])
        self.bot_ds.add_handler(MessageHandler(Filters.text, 
                                               self.get_city_msg_handler))
        
    def get_city_msg_handler(self, update, context) -> None:   
        logger.info("User starts self.get_city_msg_handler")
        context.user_data['user_city'] = self.weather_api.get_city_by_name(update.message.text)
        
        logger.info("User get city %s",context.user_data['user_city'])
        
        if context.user_data['user_city'] is not None:
            update.message.reply_text(text=self.bot_msg['get_city_msg_handler_true'].format(update.message.text))
            self.get_weather(update, context)
        else: 
            update.message.reply_text(text=self.bot_msg['get_city_msg_handler_false'].format(update.message.text))
            self.get_city(update, context)
            
    def change_city(self, update, context) -> None:
        logger.info("User starts self.change_city")
        self.get_city(update, context)
                
    def get_weather(self, update, context) -> None:
        logger.info("User starts self.get_weather")
        update.message.reply_text(text="get weather")
         
    # Запуск
    def run(self) -> None:
        self.bot = Bot(self.tg_token)
        self.bot_u = Updater(self.tg_token)
        self.bot_ds = self.bot_u.dispatcher
        
        #Передается список команд для меню
        self.bot.set_my_commands(self.bot_menu)
        
        #Диалог приветствия start и обработка callback от кнопко Да / Нет
        self.bot_ds.add_handler(CommandHandler('start', self.start))
        self.bot_ds.add_handler(CallbackQueryHandler(self.start_commit,pattern='^' + str(self.YES) + '$'))
        self.bot_ds.add_handler(CallbackQueryHandler(self.start_negative,pattern='^' + str(self.NO) + '$'))

        #Старт изменения города по команде /change_city
        self.bot_ds.add_handler(CommandHandler('change_city', self.change_city))
        
        logger.info("Запуск бота")
        
        self.bot_u.start_polling()
        print('Started')
        self.bot_u.idle()
