from telegram.ext import Application, CommandHandler, MessageHandler, filters
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

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

    Помни, что забота о здоровье – это важно! Не забывай слушать свое тело и консультироваться с врачом перед началом новой программы тренировок.
    """
    await context.bot.send_message(chat_id=chat_id, text=welcome_message)


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


async def button(update, context):
    query = update.callback_query
    query.answer()
    await query.message.reply_text('Пожалуйста, укажите вашу фитнес-цель после команды /setgoal.')


async def set_goal(update, context):
    # Получаем текст фитнес-цели, отправленной пользователем
    goal = update.message.text

    # Проверяем, что пользователь отправил фитнес-цель
    if goal:
        # Сохраняем цель пользователя в базе данных или обрабатываем ее по вашему усмотрению
        # Например, можно сохранить в базу данных
        chat_id = update.message.chat_id
        user = session.query(FitnessGoal).filter_by(chat_id=chat_id).first()
        if user:
            user.fitness_goal = goal
        else:
            new_user = FitnessGoal(chat_id=chat_id, fitness_goal=goal)
            session.add(new_user)
        session.commit()

        # Отправляем подтверждение пользователю
        await context.bot.send_message(chat_id=chat_id, text=f"Ваша фитнес-цель установлена на: {goal}")
    else:
        # Если пользователь не отправил цель, сообщаем ему об этом
        chat_id = update.message.chat_id
        await context.bot.send_message(chat_id=chat_id,
                                       text="Пожалуйста, укажите вашу фитнес-цель после команды /setgoal.")

async def my_progress(update, context):
    chat_id = update.message.chat_id
    user = session.query(FitnessGoal).filter_by(chat_id=chat_id).first()
    if user:
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

    # Создание аватарки профиля
    photo_path = "C:\Users\1\PycharmProjects\pythonProject3\icon.jpg"  # Путь к изображению профиля
    with open(photo_path, "rb") as photo_file:
        application.set_avatar(photo_file)

    # Добавляем описание для бота
    application.set_description("Этот бот поможет вам отслеживать ваши фитнес-цели и прогресс.")

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setgoal", set_goal))
    application.add_handler(CommandHandler("myprogress", my_progress))

    # Добавление обработчика для текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, echo))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
