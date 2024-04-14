from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import asyncio

Base = declarative_base()


# Определение модели данных пользователя
class FitnessGoal(Base):
    __tablename__ = 'fitness_goals'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    name = Column(String)
    age = Column(Integer)
    fitness_goal = Column(String)


# Создание соединения с базой данных
engine = create_engine('sqlite:///bot.db')

# Создание таблиц в базе данных
Base.metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()


# Функция обработки команды /start
async def start(update, context):
    chat_id = update.message.chat_id
    welcome_message = """
    Привет! Я здесь, чтобы помочь тебе с тренировками и здоровым образом жизни. 

    Для того чтобы начать, воспользуйся следующими командами:
    /start - начать общение с ботом
    /help - показать список доступных команд
    /setgoal - установить свою фитнес-цель
    /myprogress - просмотреть свой прогресс

    Помни, что забота о здоровье – это важно! Не забывай слушать свое тело и консультироваться с врачом перед началом 
    новой программы тренировок.
    """
    # Очищаем данные пользователя при запуске диалога
    context.user_data.clear()
    await context.bot.send_message(chat_id=chat_id, text=welcome_message)
    return ConversationHandler.END


# Функции обработки остальных команд и сообщений
async def help_command(update, context):
    chat_id = update.message.chat_id
    help_text = """
    Список доступных команд:
    /start - начать общение с ботом
    /help - показать список доступных команд
    /setgoal - установить свою фитнес-цель
    /myprogress - просмотреть свой прогресс
    """
    await context.bot.send_message(chat_id=chat_id, text=help_text)


# Определение состояний
GOAL, AGE, WEIGHT, HEIGHT, HANDLE_INPUT, PHOTO, PLAN = range(7)


# Функция для обработки команды /setgoal
async def set_goal(update, context):
    reply_keyboard = [['Набор мышечной массы', 'Похудение', 'Отдых']]
    await update.message.reply_text(
        "Выберите вашу цель:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return GOAL


# Функция для обработки выбора варианта
async def process_goal_choice(update, context):
    user_data = context.user_data
    user_data['goal'] = update.message.text

    # Сохраняем цель пользователя в базе данных
    chat_id = update.message.chat_id
    user = session.query(FitnessGoal).filter_by(chat_id=chat_id).first()
    if user:
        user.fitness_goal = user_data['goal']
    else:
        new_user = FitnessGoal(chat_id=chat_id, fitness_goal=user_data['goal'])
        session.add(new_user)
    session.commit()

    await update.message.reply_text(f"Ваша цель: {user_data['goal']}")
    await context.bot.send_message(chat_id=update.message.chat_id, text="Сколько вам лет?")
    return AGE


# Функция для получения возраста
async def get_age(update, context):
    user_data = context.user_data
    user_data['age'] = update.message.text
    await context.bot.send_message(chat_id=update.message.chat_id, text="Какой ваш вес?")
    return WEIGHT


# Функция для получения веса
async def get_weight(update, context):
    user_data = context.user_data
    user_data['weight'] = update.message.text
    await context.bot.send_message(chat_id=update.message.chat_id, text="Какой ваш рост?")
    return HEIGHT


# Функция для получения роста
async def get_height(update, context):
    user_data = context.user_data
    user_data['height'] = update.message.text
    await context.bot.send_message(chat_id=update.message.chat_id, text="Теперь, пожалуйста, присылайте ваше фото.")
    return PHOTO


# Функция для обработки ответов пользователя
async def handle_input(update, context):
    user_data = context.user_data
    await context.bot.send_message(chat_id=update.message.chat_id, text="Вы установили следующие данные:")
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"Цель: {user_data['goal']}")
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"Возраст: {user_data['age']}")
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"Вес: {user_data['weight']}")
    await context.bot.send_message(chat_id=update.message.chat_id, text=f"Рост: {user_data['height']}")

    # Сохраняем возраст пользователя в базе данных
    chat_id = update.message.chat_id
    user = session.query(FitnessGoal).filter_by(chat_id=chat_id).first()
    if user:
        user.age = user_data['age']
        session.commit()

    # Сбросить состояние пользователя
    return ConversationHandler.END


# Функция для запроса фото
async def request_photo(update, context):
    await update.message.reply_text(
        'Пожалуйста, отправьте ваше фото.',
        reply_markup=ReplyKeyboardRemove()
    )
    return PHOTO


# Функция для проверки фото
# Функция для проверки фото и отправки соответствующего сообщения
async def check_photo(update, context):
    user_data = context.user_data
    if update.message.photo:
        # Обработка полученного фото
        await update.message.reply_text('Спасибо за фото!')
        # Отправляем сообщение о том, что план составляется
        await update.message.reply_text('Сейчас составим для вас план.')
        # Имитация задержки в обработке
        await asyncio.sleep(2)  # Задержка в 2 секунды
        # Отправляем сообщение о готовности плана
        await update.message.reply_text('Ваш план готов!')

        # Отправляем сообщение в зависимости от выбора пользователя
        if user_data.get('goal') == 'Набор мышечной массы':
            await update.message.reply_text('''Ваш фитнес-план:Разминка (5-10 минут): 
- Кардио
- Растяжка

Основные упражнения:
- Грудь: Жим штанги на скамье, Жим гантелей, Разведение гантелей
- Спина: Тяга штанги в наклоне, Подтягивания, Гиперэкстензии
- Ноги: Приседания со штангой, Жим ногами в тренажере, Румынская тяга
- Плечи: Армейский жим, Махи гантелей, Подъемы штанги перед собой
- Руки: Сгибание рук со штангой, Французский жим, Молотковые подъемы гантелей

Кардио (по желанию):
- 10-20 минут бега или быстрой ходьбы

Питание и восстановление:
- Богатая белком, углеводами и здоровыми жирами диета
- Много воды
- Достаточный отдых

Прогрессия:
- Увеличивайте нагрузку постепенно''')
        elif user_data.get('goal') == 'Похудение':
            await update.message.reply_text('''Разминка (5-10 минут):
- Кардио
- Растяжка

Основные упражнения:
- Кардио: Бег на беговой дорожке, Эллиптический тренажер, Велосипед
- Силовые упражнения: Приседания, Жим ногами в тренажере, Тяга гантелей в наклоне, Подтягивания, Сгибание рук со штангой

Кардио (по желанию):
- 20-30 минут высокоинтенсивного кардио (например, HIIT)

Питание и восстановление:
- Контролируйте калорийный баланс: потребляйте меньше калорий, чем вы тратите
- Увеличьте потребление белка и ограничьте потребление углеводов и жиров
- Пейте много воды
- Обеспечьте своему организму достаточный отдых для восстановления и регуляции аппетита

Прогрессия:
- Увеличивайте интенсивность тренировок по мере улучшения физической формы
''')
        elif user_data.get('goal') == 'Отдых':
            await update.message.reply_text('''Разминка (5-10 минут):
- Прогулка на свежем воздухе
- Легкая растяжка

Основные упражнения (выберите упражнения, которые приносят удовольствие):
- Бег: 20-30 минут по парку или по берегу реки
- Йога: 30-45 минут для укрепления мышц и улучшения гибкости
- Плавание: 20-30 минут в бассейне для расслабления и укрепления всего тела
- Велосипед: 30-45 минут прогулки по окрестностям или велосипедная тренировка

Расслабление:
- После тренировки проведите время в сауне или горячей ванне для расслабления мышц и умственного отдыха
- Практика медитации или дыхательных упражнений для уменьшения стресса и улучшения общего самочувствия

Питание и восстановление:
- Питайтесь сбалансированно, уделяя внимание потреблению достаточного количества белка, углеводов и здоровых жиров
- Пейте достаточное количество воды
- Уделите время сна и отдыху, чтобы восстановиться после тяжелого дня на работе и тренировок
''')

        # Завершаем диалог
        return ConversationHandler.END
    else:
        await update.message.reply_text('Это не фото:) Пожалуйста, отправьте фотографию.')
        return PHOTO


# Сообщение, что план готов
async def plan(update, context):
    await update.message.reply_text('Ваш план готов!')
    return ConversationHandler.END


# Функция с отображением процесса
async def my_progress(update, context):
    chat_id = update.message.chat_id
    user = session.query(FitnessGoal).filter_by(chat_id=chat_id).first()
    if user and user.fitness_goal:
        progress_text = f"Ваша текущая фитнес-цель: {user.fitness_goal}"
    else:
        progress_text = "Вы еще не установили фитнес-цель. Используйте команду /setgoal, чтобы установить ее."
    await context.bot.send_message(chat_id=chat_id, text=progress_text)


async def echo(update, context):
    chat_id = update.message.chat_id
    text = update.message.text
    await context.bot.send_message(chat_id=chat_id, text=f"Ваша цель: {text}")


def main():
    # Создание объекта Application с токеном вашего бота
    application = Application.builder().token('6612558741:AAHH5pRdc-GrtbizIb8lvk1CIOlzO9XfGo0').build()

    # Добавление обработчиков команд

    # Обработчик команды "/start"
    application.add_handler(CommandHandler("start", start))

    # Обработчик команды "/help"
    application.add_handler(CommandHandler("help", help_command))

    # Обработчик команды "/myprogress"
    application.add_handler(CommandHandler("myprogress", my_progress))

    # Создание ConversationHandler

    # Определение начального состояния для ConversationHandler
    entry_points = [CommandHandler('setgoal', set_goal)]

    # Определение состояний и соответствующих им обработчиков
    states = {
        GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_goal_choice)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
        WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
        HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_photo)],
        PHOTO: [MessageHandler(filters.PHOTO, check_photo),
                MessageHandler(filters.ALL, request_photo)],
        # Если пользователь не отправил фото, запросить еще раз
        PLAN: [MessageHandler(filters.ALL, plan)]  # Обработка состояния PLAN
    }

    # Определение fallbacks (выходных точек)
    fallbacks = []

    # Создание ConversationHandler
    conv_handler = ConversationHandler(entry_points=entry_points, states=states, fallbacks=fallbacks)

    # Добавление ConversationHandler в Application
    application.add_handler(conv_handler)

    # Добавление обработчика для текстовых сообщений

    # Обработчик для всех текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, echo))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
