import telebot
import random
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from db_bot import get_db_connection
from db_telebot import (
    data_base, user_check, fill_common_words,
    get_random_words, check_words, add_word_user,
    delete_words_users, update_users_words)

get_db_connection()

data_base()

print('Бот работает')

state_storage = StateMemoryStorage()
token_bot = '8161554872:AAGRBCgd_AjdtNSqvE5DmLsM0QyaJZtvR7M'
bot = TeleBot(token_bot, state_storage=state_storage)

user_check(user_id=bot.get_me().id, username=bot.get_me().username)

class Command:
    ADD_WORD = 'Добавить слово '
    DELETE_WORD = 'Удалить слово'
    NEXT = 'Следующее слово'

class MyStates(StatesGroup):
    english_word = State()
    russian_word = State()
    other_words = State()
    adding_new_words = State()
    saving_new_words = State()
    deleting_words = State()
    
common_words = [
    ('Peace', 'Мир'), ('Without', 'Без'), ('Nurse', 'Медсестра'), 
    ('Target', 'Цель'), ('Timeless', 'Вневременной'), ('Often', 'Часто'), 
    ('Shoes', 'Обувь'), ('Blouse', 'Кофта'), ('Crowd', 'Толпа'), 
    ('Developer', 'Разработчик')      
]


fill_common_words(common_words)



@bot.message_handler(commands=['start'])
def create_cards(message):
    cid = message.chat.id
    username = message.chat.username or 'Unknown'
    user_check(cid, username)
    print('Запуск бота в первый раз')
    
    bot.send_message('Привет, давай учить английский')
    
    create_cards(message)

def create_cards(message):
    
    cid = message.chat.id
    
    words = get_random_words(cid, limit=4)
    print(f'Случайные слова{words}')
    
    if not words or len(words) < 4:
        bot.send_message(cid,'Нет доступных слов!\nДобавьте новые слова!')
        print('Недостаточно слов. Добавьте ещё!')
        return
    english_word, russian_word = words[0]
    other_words = [w[0]for w in words[1:]]
    
    options = other_words + [english_word]
    random.shuffle(options)
    
    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = [types.KeyboardButton(options) for option in options]
    buttons.append(types.KeyboardButton(Command.NEXT))
    buttons.append(types.KeyboardButton(Command.ADD_WORD))
    buttons.append(types.KeyboardButton(Command.DELETE_WORD))
    markup.add(*buttons)
    
    bot.set_state(user_id=message.from_user.id, chat_id=message.chat_id, state=MyStates.english_word)
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat_id) as data:
        data['english_word'] = english_word
        data['russian_word'] = russian_word
        
    greeting = f'Выбери перевод слова:{russian_word}'
    bot.send_message(cid, greeting, reply_markup=markup)
    
    
@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        print(data['english_word'])  # удалить из БД


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    bot.set_state(user_id=message.from_user.id, chat_id=cid, state=MyStates.adding_new_words)
    bot.send_message(cid, 'Введите слово, которое вы хотите добавить, на английском:')  # сохранить в БД
    
@bot.message_handler(state=MyStates.adding_new_words)
def add_translate_word(message):
    cid = message.chat.id
    word = message.text.strip().capitalize()
    
    if check_words(word):
        bot.send_message(cid, 'Это слово уже есть в общем словаре. Пожалуйста, введите другое слово.')
        return
    
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=cid) as data:
        data['english_word'] = word
        
    bot.set_state(user_id=message.from_user.id, chat_id=cid, state=MyStates.saving_new_words)
    bot.send_message(cid, f'Теперь введите перевод для слова {word}:') 

@bot.message_handler(state=MyStates.saving_new_words)
def save_new_word(message):
    cid = message.chat_id
    translation = message.text.strip().capitalize()
    
    
    if not translation:
        bot.send_message(cid, 'Перевод не может быть пустым. Пожалуйста, введите перевод.')
        return
    try:
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=cid) as data:
            english_word = data.get('english_word').capitalize()
            
        if not english_word:
            bot.send_message(cid, 'Ошибка! Попробуй снова начать с /start.')
            bot.delete_state(user_id=message.from_user.id, chat_id=cid)
            return
        add_word_user(message.from_user.id, english_word, translation)
        
        bot.send_message(cid, f'Слово {english_word} и его перевод {translation} успешно добавлены!')
    except Exception as e:
        print(f'Произошла ошибка при сохранении слова: {e}')
        bot.send_message(cid, 'Произошла ошибка при сохранении слова: {e}')
    finally:
        bot.delete_state(user_id=message.from_user.id, chat_id=cid)
        
    send_main_menu(cid)
    
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    bot.set_state(user_id=message.from_user.id, chat_id = message.chat.id, state=MyStates.deleting_words)
    bot.send_message(cid, 'Введите слово, которое хотите удалить, на английском:')
    
@bot.message_handler(state=MyStates.deleting_words)
def delete_word(message):
    cid = message.chat.id
    word_to_delete = message.text.strip().capitalize()
    
    word_to_delete = delete_words_users(message.from_user.id, word_to_delete)
    if word_to_delete:
        bot.send_message(cid, f'Слово {word_to_delete[0]} успешно удалено из вашего словаря!')
        print(f'Удалено слово: {word_to_delete[0]}')
    else:
        bot.send_message(cid, 'Слово не найдено в вашем персональном словаре.')
        print('Слово не удалено.')
    bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
    send_main_menu(cid)
    
def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = [
        types.KeyboardButton(Command.ADD_WORD),
        types.KeyboardButton(Command.DELETE_WORD),
        types.KeyboardButton(Command.NEXT)  
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, 'Выберите дальнейшее действие:', reply_markup=markup)

@bot.message_handler(func=lambda message:True, content_types=['text'])
def message_reply(message):
    user_input = message.text.strip()
    print(f'Ответ пользователя: {user_input}')
    
    state = bot.get_state(user_id=message.from_user.id, chat_id=message.chat.id)
    print(f'Полученное состояние для пользователя {message.from_user.id}, чат {message.chat.id}: {state}')
    
    if state != MyStates.english_word.name:
        bot.send_message(message.chat.id, 'Ошибка! Начните заново с /start.')
        return
    
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        english_word = data.get('english_word')
        russian_word = data.get('russian_word')
        attempts = data.get('attempts', 0)
        print(f'Данные из состояний: target_word={english_word}, translate_word={russian_word}')
        
    if not english_word or not russian_word:
        bot.send_message(message.chat.id, 'Ошибка! Попробуй снова начать с /start.')
        return
    
    if user_input.strip().lower() == english_word.strip().lower():
        try:
            update_users_words(message.from_user.id, english_word, russian_word)
            bot.send_message(message.chat.id, f'Правильно!\n{english_word} => {russian_word}!')
        except ValueError as e:
            print(f'Ошибка при обновлении слова:{e}')
        data.clear()
        return
    attempts += 1
    data['attemps'] = attempts
    if attempts < 3:
        bot.send_message(message.chat.id, f'Неправильно! Попробуй снова.\nПеревод слова: {russian_word}, Попытка {attempts} из 3')
    else:
        bot.send_message(message.chat.id, f'К сожалению, вы исчерпали попытки.\nПравильный перевод: {english_word}')
        data.clear()
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
        
    
        
        















