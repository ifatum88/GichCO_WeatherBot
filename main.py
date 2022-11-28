import json
import logging
import re
import sys
import api_weather

from telegram import *
from telegram.ext import *


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

"""
TO DO

1. Сделать запоминание нескольких городов / добавление в список / удаление из списка
2. Сделать сохранение данных при перезапуске Persisted Bot
3. Сделать вывод погоды по расписанию (задать раписание кнопками), ручной запрос, изменить раписание.

"""

        
class weather_bot():

    # Базовые функции класса
    def __init__(self) -> None:
        self.YES,self.NO,self.INPUT,self.HANDLER = range(4) # Состояния для ConvHandler
        self.weather_api = api_weather.WeatherAPI() # Подключение WeatherAPI
        self.bot_menu = self.set_menu_commands() # Получение команд бота в меню
        self.bot_msg = self.set_msg() # Получение словаря с сообщениями 
        self.bot_keyboards = self.set_keyboards() # Получение словаря с клавиатурами
        self.max_city_cnt = 5
        self.bot_token = self.set_token()

    def set_token(self) -> str:
        """
        Возращает токен бота из JSON файла
        """
        json_file_name = "api_keys.json"
        
        with open(json_file_name,"r",encoding="utf-8") as json_file:
            reader = json.loads(json_file.read())
            return reader.get('bot').get('token')
        
    def set_menu_commands(self) -> list:
        """
        Функция читает список команд бота в кнопке "меню"
        
        Retrun - List
        """
        json_file_name = "menu.json"
        commands_list = []

        with open(json_file_name,"r",encoding="utf-8") as json_file:
            for cmd in json.loads(json_file.read()):
                commands_list.append((cmd['cmd'],cmd['description']))

        return commands_list
    
    def set_msg(self) -> dict:
        """
        Функция читает текст выводимых ботом сообщений из 
        JSON файла
        
        Retrun - List
        """
        json_file_name = "msg.json"
        msg_dict = dict()
        
        with open(json_file_name,encoding="utf-8") as json_file:
            for cmd in json.loads(json_file.read()):
                msg_dict[cmd['command']] = str(cmd['message'])

        return msg_dict

    def set_keyboards(self, resize = True):
        """
        Функция читает текст клавиатур
        
        Retrun - List
        """   
        keyboard = []
        keyboards_dict = dict()
        json_file_name = "keyboards.json"
        
        with open(json_file_name,"r",encoding="utf-8") as json_file:
            return json.loads(json_file.read())
        
    def find_city(self, local_name:str, city_list:list) -> dict:
        ret = {}
        
        if city_list:
            for i,city in enumerate(city_list):
                if city['local_name'] == local_name:
                    ret['key'] = str(i)
                    ret['city'] = city
                    break

        return ret
    
    def make_city_keyboard_markup(self, context) -> ReplyKeyboardMarkup:
        
        #Формируем клавиатуру для вывода списка городов + добавляем кнопку выхода из диалога
        keyboard = [[KeyboardButton(city['local_name'])] for city in context.user_data['user_city_list']]
        keyboard.append([KeyboardButton(self.bot_keyboards['get_weather']['back'])])
        keyboard = ReplyKeyboardMarkup(
            keyboard = keyboard,
            one_time_keyboard = True,
            resize_keyboard = True
        )
        
        return keyboard

    # Команды для бота
    def start (self, update: Update, context: CallbackContext) -> int:
        """
        Обработка команды /start
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "start",
                    "Command",
                    "Start session")
        
        #Формирование клавиатуры Да / Нет
        keyboadr = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text=self.bot_keyboards['greeting_q']['Yes'],
                                     callback_data = self.YES),
                InlineKeyboardButton(text=self.bot_keyboards['greeting_q']['No'],
                                     callback_data = self.NO)
                ]
            ]
        )
        
        #Сообщене приветствия
        update.message.reply_text(text=self.bot_msg['greeting'])
        #Вопрос на продолжение с кнопками Да / Нет
        update.message.reply_text(text=self.bot_msg['greeting_q'], 
                                  reply_markup=keyboadr)
        
        #Заходим в блок обработки ответа и ожидания ввода сообщения
        return self.INPUT
    
    def start_commit(self, update: Update, context: CallbackContext) -> int:
        """
        Обработка callback = self.YES
        """
        query = update.callback_query
        query.answer()
        
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    query.message.chat.username,
                    "start_commit",
                    "CallbackQueryHandler",
                    "")
        
        #Вывод подтверждения и переход на получение города get_city
        query.edit_message_text(text=self.bot_msg['start_commit'])
        self.get_city(query, context)
        
        return self.HANDLER

    def start_negative(self, update: Update, _) -> int:
        """
        Обработка callback = self.NO
        """
        query = update.callback_query
        
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    query.message.chat.username,
                    "start_negative",
                    "CallbackQuery",
                    "")
        
        query.edit_message_text(text=self.bot_msg['start_negative'])

        return ConversationHandler.END
    
    def get_city(self, update: Update, context: CallbackContext) -> int:
        """
        Функция начинает диалог получения города.
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "get_city",
                    "Command",
                    "")
         
        # Проверка, что количество введенных ранее городов не превышает self.max_city_cnt
        # Если превышает = завершаем диалог
        if  len(context.user_data.get('user_city_list',[])) == self.max_city_cnt:
            update.message.reply_text(text=self.bot_msg['max_city_capacity'].format(self.max_city_cnt))
            return ConversationHandler.END
        
        # Вывод сообщения на запрос города
        update.message.reply_text(text=self.bot_msg['ask_city'])
        
        # Заходим в блок обработки ответа
        return self.HANDLER
            
    def set_city_msg_handler(self, update: Update, context: CallbackContext) -> int: 
        """
        Обработчик сообщения с названием города
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "set_city_msg_handler",
                    "Message",
                    "")
        
        context_users_city_list = context.user_data.get('user_city_list',[])
        
        # Получение информации о городе через API
        new_city = self.weather_api.get_city_by_name(update.message.text)
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "set_city_msg_handler",
                    "Message",
                    "API has returned city = " + str(new_city))
        #ОБРАБОТКА ИСКЛЮЧЕНИЙ
        
        #Город был введен некорректно (результат работы API is None)
        #Возвращаем коверсейшн на повторный ввод города
        if new_city is None:
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "set_city_msg_handler",
                        "Message",
                        "State = FALSE")
        
            update.message.reply_text(text=self.bot_msg['get_city_msg_handler_false'].format(update.message.text))
            
            return self.HANDLER
        
        #Проверка на наличие такого города в контексте user_city_list. 
        #Возвращаем конверсейшн на повторный ввод города
        if self.find_city(new_city['local_name'], context_users_city_list):
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "set_city_msg_handler",
                        "Message",
                        "State = DOUBLE")
            update.message.reply_text(text=self.bot_msg['get_city_msg_handler_double'].format(new_city['local_name']))
            
            return self.HANDLER

        #ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "set_city_msg_handler",
                    "Message",
                    "State = TRUE")
        update.message.reply_text(text=self.bot_msg['get_city_msg_handler_true'].format(new_city['local_name']))
        
        logger.info("contex = %s",context.user_data)
        
        if context.user_data.get('user_city_pos_to_change'):
            logger.info("i'm here")
            context_users_city_list[int(context.user_data['user_city_pos_to_change'])] = new_city
            del context.user_data['user_city_pos_to_change']
        else:
           context_users_city_list.append(new_city) 
        
        context.user_data['user_city_list'] = context_users_city_list
        
        #Запускаем старт вывода погоды
        self.get_weather_start(update, context)
        
        #Завершаем диалог получения города
        return ConversationHandler.END
                        
    def change_city(self, update: Update, context: CallbackContext) -> int:
        """
        Запуск компанды смены городв
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "change_city",
            "Command",
            "")

        update.message.reply_text(text=self.bot_msg['change_city'].format(len(context.user_data['user_city_list'])),
                                  reply_markup=self.make_city_keyboard_markup(context)
                                  )
        
        return self.INPUT
    
    def change_city_msg_handler(self, update: Update, context: CallbackContext) -> int:
        """_
        Обработчик введенного сообщения с именем города
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "change_city_msg_handler",
                    "Message",
                    "")
        
        user_city_list = context.user_data['user_city_list']

        #ОБРАБОТКА ИСКЛЮЧЕНИЙ
        
        #Нажал кнопку "Ничего не хочу менять"
        #Сообщение и завершение диалога
        if update.message.text == self.bot_keyboards['change_city_disagree']['back']:
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "change_city_msg_handler",
                        "Message",
                        "State = Back")
            update.message.reply_text(text=self.bot_msg['change_city_msg_handler_back'],
                                      reply_markup=ReplyKeyboardRemove())
            self.get_weather_start(update, context)
            return ConversationHandler.END
        
        #Ввел с клавиатуры город, которого нет в списке
        #Отправляем на повторный ввод
        if not self.find_city(update.message.text, user_city_list):
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "change_city_msg_handler",
                        "Message",
                        "State = FALSE")
            update.message.reply_text(text=self.bot_msg['change_city_msg_handler_false'])
            return self.INPUT
        
        #ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "change_city_msg_handler",
                    "Message",
                    "State = TRUE")
        update.message.reply_text(text=self.bot_msg['change_city_msg_handler_true'].format(update.message.text))
        
        #Получаем позицию города, который нужно изменить
        context.user_data['user_city_pos_to_change'] = self.find_city(update.message.text, user_city_list).get('key')

        #Выходим в обработку ввода
        return self.HANDLER
                
    def get_weather_start(self, update: Update, context: CallbackContext) -> None:
        """
        Функция для начала диалога получения погоды
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "get_weather_start",
                    "NO",
                    "")

        #Формируем клавиатуру для старта получения погоды
        keyboard = [[KeyboardButton(self.bot_keyboards['get_weather']['get'])]]
        keyboard = ReplyKeyboardMarkup(
            keyboard = keyboard,
            one_time_keyboard = True,
            resize_keyboard = True
        )
        
        #Вывод сообщения и клавиатуры
        update.message.reply_text(text=self.bot_msg['get_weather_start'],
                                  reply_markup = keyboard)
        
        
    def get_weather_keyboard_handler(self, update: Update, context: CallbackContext) -> int:
        """
        Функция для вывода списка городов
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "get_weather_keyboard_handler",
                    "Message",
                    "")

        update.message.reply_text(text=self.bot_msg['get_weather_keyboard_handler'],
                                  reply_markup=self.make_city_keyboard_markup(context))
        
        #Получаем город и переходим в обработчика get_weather_handler
        return self.HANDLER
        
    
    def get_weather_handler(self, update: Update, context: CallbackContext) -> int:
        """
        Функция обработки введенного города
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "get_weather_handler",
                    "Message",
                    "")
        user_reply = update.message.text
        user_city_list = context.user_data['user_city_list']
        
        # ОБРАБОТКА ИСКЛЮЧЕНИЙ
        # Нажата кнопка выхода
        if user_reply == self.bot_keyboards['get_weather']['back']:
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "get_weather_handler",
                        "Message",
                        "State = Back")
            update.message.reply_text(text=self.bot_msg['get_weather_handler_back'],
                            reply_markup=ReplyKeyboardRemove())
            self.get_weather_start(update, context)
            return ConversationHandler.END
        
        # Вручную введен город, которого нет в списке
        if not self.find_city(user_reply, user_city_list):
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "get_weather_handler",
                        "Message",
                        "State = False")
            update.message.reply_text(text=self.bot_msg['get_weather_handler_false'])
            return self.HANDLER
        
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "get_weather_handler",
            "Message",
            "State = True")

        # Получение погоды
        self.get_weather(update, context)
        
        # Делаем петлю для вывода клавиатуры
        self.get_weather_start(update, context)
        
        # Завершение диалога
        return ConversationHandler.END
    
    def get_weather(self, update, context) -> None:
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "get_weather",
            "NO",
            "")
        
        city = self.find_city(update.message.text, context.user_data['user_city_list'])
        city_weather_list = self.weather_api.get_weather(city.get('city'))

        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "get_weather",
            "NO",
            "Get city position = " + city.get('key'))
        
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "get_weather",
            "NO",
            city_weather_list)
        
        # Вывод погоды по каждому брокеру
        for weather in city_weather_list:
            update.message.reply_text(
                text=self.bot_msg['get_weather'].format(broker_name=weather['name'],
                                                        city_name=city['city']['local_name'],
                                                        weather= weather['weather'])
                )
    
    def remove_city(self, update: Update, context: CallbackContext) -> int:
        """
        Запуск команды удаления города
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "remove_city",
            "Command",
            "")

        update.message.reply_text(text=self.bot_msg['remove_city'],
                                  reply_markup=self.make_city_keyboard_markup(context)
                                  )
        
        return self.INPUT
    
    def remove_city_msg_handler(self, update: Update, context: CallbackContext) -> int:
        """_
        Обработчик введенного сообщения с именем города
        """
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "remove_city_msg_handler",
                    "Message",
                    "")
        
        user_city_list = context.user_data['user_city_list']

        #ОБРАБОТКА ИСКЛЮЧЕНИЙ
        
        #Нажал кнопку "Пока не надо"
        #Сообщение и завершение диалога
        if update.message.text == self.bot_keyboards['get_weather']['back']:
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "remove_city_msg_handler",
                        "Message",
                        "State = Back")
            update.message.reply_text(text=self.bot_msg['change_city_msg_handler_back'],
                                      reply_markup=ReplyKeyboardRemove())
            self.get_weather_start(update, context)
            return ConversationHandler.END
        
        #Ввел с клавиатуры город, которого нет в списке
        #Отправляем на повторный ввод
        if not self.find_city(update.message.text, user_city_list):
            logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                        update.message.chat.username,
                        "remove_city_msg_handler",
                        "Message",
                        "State = FALSE")
            update.message.reply_text(text=self.bot_msg['change_city_msg_handler_false'])
            return self.INPUT
        
        #ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
                    update.message.chat.username,
                    "remove_city_msg_handler",
                    "Message",
                    "State = TRUE")
        update.message.reply_text(text=self.bot_msg['remove_city_msg_handler_true'].format(update.message.text))
        
        #Удаляем город
        del user_city_list[int(self.find_city(update.message.text, user_city_list).get('key'))]
        self.get_weather_start(update, context)

        #Выходим из диалога
        return ConversationHandler.END
    
    def cancel(self, update, context) -> None:
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "cancel",
            "Command",
            "")
        
    def get(self, update, context) -> None:
        logger.info("user = %s - Command = %s - Handler = %s - Msg = %s",
            update.message.chat.username,
            "get",
            "Command",
            "")
        
        update.message.reply_text(text=f"User_data: {context.user_data}")
         
    # Запуск
    def run(self) -> None:
        self.bot = Bot(self.bot_token)
        self.bot_u = Updater(self.bot_token)
        self.bot_ds = self.bot_u.dispatcher
        
        #Передается список команд для меню
        self.bot.set_my_commands(self.bot_menu)
        
        #Диалог приветствия start и обработка callback от кнопок Да / Нет
        conv_handler_start = ConversationHandler(
            entry_points = [CommandHandler('start', self.start)],
            states = {
                self.INPUT: [
                    CallbackQueryHandler(self.start_commit,pattern='^' + str(self.YES) + '$'),
                    CallbackQueryHandler(self.start_negative,pattern='^' + str(self.NO) + '$')
                ],
                self.HANDLER: [MessageHandler(Filters.text, self.set_city_msg_handler)]
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )
        self.bot_ds.add_handler(conv_handler_start)
        
        #Старт изменения города по команде /add_city
        conv_handler_add_city = ConversationHandler(
            entry_points = [CommandHandler('add_city', self.get_city)],
            states = {
                self.HANDLER: [MessageHandler(Filters.text, self.set_city_msg_handler)]     
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )
        self.bot_ds.add_handler(conv_handler_add_city)
        
        #Старт изменения города по команде /change_city
        conv_handler_change_city = ConversationHandler(
            entry_points = [CommandHandler('change_city', self.change_city)],
            states = {
                self.INPUT: [MessageHandler(Filters.text, self.change_city_msg_handler)],     
                self.HANDLER: [MessageHandler(Filters.text, self.set_city_msg_handler)]  
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )
        self.bot_ds.add_handler(conv_handler_change_city)
        
        #Старт изменения города по команде /remove_city
        conv_handler_remove_city = ConversationHandler(
            entry_points = [CommandHandler('remove_city', self.remove_city)],
            states = {
                self.INPUT: [MessageHandler(Filters.text, self.remove_city_msg_handler)]
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )
        self.bot_ds.add_handler(conv_handler_remove_city)
        
        #Обработка нажатия кнопки с погодой
        conv_handler_get_weather = ConversationHandler(
            entry_points = [MessageHandler(
                                    Filters.regex(
                                        re.compile(self.bot_keyboards['get_weather']['get'], re.IGNORECASE)),
                                    self.get_weather_keyboard_handler)],
            states = {
                self.HANDLER: [MessageHandler(Filters.text, self.get_weather_handler)] 
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )  
        self.bot_ds.add_handler(conv_handler_get_weather)
        
        #Обработчик для получения контекста
        self.bot_ds.add_handler(CommandHandler('get', self.get))
        
        self.bot_u.start_polling()
        logger.info("Bot started")
        self.bot_u.idle()
