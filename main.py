from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler
from telegram.ext import ApplicationBuilder
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import asyncio
from yandexgptlite import YandexGPTLite
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
GOAL, AGE, WEIGHT, HEIGHT, HANDLE_INPUT, PHOTO, PLAN = range(7)
PROMPT = range(1)

Base = declarative_base()
class FitnessGoal(Base):
    __tablename__ = 'fitness_goals'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    name = Column(String)
    age = Column(Integer)
    fitness_goal = Column(String)
    '''weight = Column(Integer)
    height = Column(Integer)'''


engine = create_engine('sqlite:///bot.db')

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()



async def start(update, context):
    context.user_data.clear()

    keyboard = [["Установить свою фитнес-цель"],
                ["Посмотреть информацию о себе"],
                ["Личный фитнес-тренер"]]
    
    await update.message.reply_text( 
        text='''Привет! Я здесь, чтобы помочь тебе с тренировками и здоровым образом жизни.\n\nДля того чтобы начать, выбери опцию на клавиатуре:''',
        reply_markup=ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True))


async def set_goal(update, context):
    user = update.message.from_user
    keyboard = [['Набор мышечной массы'], 
                ['Похудение'],
                ['Активное кардио']]
    
    await update.message.reply_text(
        "Выберите вашу цель на клавиатуре, \n\n"
        "В любой момент вы можете отправить команду /cancel, чтобы прервать создание плана",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    logging.info("User %s set goal:", user.first_name,)

    return GOAL


async def enter_goal(update, context):
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

    await update.message.reply_text("Сколько вам лет?")
    return AGE


async def age(update, context):
    user_data = context.user_data
    user_data['age'] = update.message.text

    chat_id = update.message.chat_id
    user = session.query(FitnessGoal).filter_by(chat_id=chat_id).first()
    if user:
        user.age = user_data['age']
    session.commit()

    await context.bot.send_message(chat_id=update.message.chat_id, text="Какой у вас вес?")

    return WEIGHT


async def weight(update, context):
    user_data = context.user_data
    user_data['weight'] = update.message.text

    await context.bot.send_message(chat_id=update.message.chat_id, text="Какой у вас рост?")

    return HEIGHT


async def height(update, context):
    user_data = context.user_data
    user_data['height'] = update.message.text

    keyboard = [['Пропустить']]

    await update.message.reply_text(
        "Теперь, пожалуйста, отправьте ваше фото.\n\n"
        "Или воспользуйтесь кнопкой ниже, если не хотите отправлять фото.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )    

    return PHOTO


async def skip(update, context):
    user_data = context.user_data
    user_data['photo'] = update.message.text
    await update.message.reply_text(
        'Жаль, но я уверен, что вы очень красивый',
        reply_markup=ReplyKeyboardRemove()
    )
    asyncio.sleep(1)
    await update.message.reply_text('Сейчас составим для вас план.')
    asyncio.sleep(2.5)
    await update.message.reply_text('Ваш план готов!')

    if user_data.get('goal') == 'Набор мышечной массы':
        await update.message.reply_text('''Ваш фитнес-план:
    Разминка (5-10 минут): 
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


async def plan(update, context):
    keyboard = [["Установить свою фитнес-цель"],
                ["Посмотреть информацию о себе"],
                ["Личный фитнес-тренер"]]


    user_data = context.user_data
    user_data['photo'] = update.message.text
    if update.message.photo:
        await update.message.reply_text('Спасибо за фото!')
        asyncio.sleep(1)
        await update.message.reply_text('Сейчас составим для вас план.')
        asyncio.sleep(2.5)
        await update.message.reply_text('Ваш план готов!')

        if user_data.get('goal') == 'Набор мышечной массы':
            await update.message.reply_text('''Ваш фитнес-план:
    Разминка (5-10 минут): 
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
    - Увеличивайте нагрузку постепенно''', 
    reply_markup=ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True))

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
    ''', reply_markup=ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True))

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
    ''', reply_markup=ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True))

            # Завершаем диалог
            return ConversationHandler.END
    else:
        await update.message.reply_text('Это не фото:) Пожалуйста, отправьте фотографию.')
        return PHOTO
    



async def cancel(update, context):
    user = update.message.from_user
    logging.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Пока! Надеюсь когда-нибудь ты вернешься(", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


async def my_info(update, context):

    chat_id = update.message.chat_id
    user = session.query(FitnessGoal).filter_by(chat_id=chat_id).first()
    if user and user.fitness_goal and user.age:
        progress_text = f"""Ваша текущая фитнес-цель: {user.fitness_goal}\nВаш возраст: {user.age}"""

    else:
        progress_text = "Вы еще не установили фитнес-цель. Используйте команду /setgoal, чтобы установить ее."
    await context.bot.send_message(chat_id=chat_id, text=progress_text)


async def coach(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Привет! Я твой личный тренер на базе YaGPT. Задавай любые вопросы, я с радостью на них отвечу.")
     
    return PROMPT


async def prompt(update, context):
    user_data = context.user_data
    user_data['prompt'] = update.message.text
    pr = str(user_data['prompt'])

    account = YandexGPTLite('b1gcod22tep1ctheen35', 'y0_AgAAAABX7bGzAATuwQAAAAECNlxxAAAInfGZcfpMF7HAIBwzQ3GZUrvVxA' )
    text = account.create_completion(f'{pr}', temperature=0.6, system_prompt = 'Представь, что ты личный фитнес-тренер и ответь на вопросы', max_tokens=100)

    await update.message.reply_text(text)


def main():
    application = ApplicationBuilder().token('6612558741:AAHH5pRdc-GrtbizIb8lvk1CIOlzO9XfGo0').build()

    application.add_handler(CommandHandler("start", start))

    conv_handler_goal = ConversationHandler(
        entry_points=[MessageHandler(filters.Text('Установить свою фитнес-цель'), set_goal)],
        states={
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_goal)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
            PHOTO: [MessageHandler(filters.PHOTO & ~filters.COMMAND, plan),
                    MessageHandler(filters.Text('Пропустить'), skip)],
        },
        fallbacks=[CommandHandler("cancel", cancel)] 
    )
    application.add_handler(conv_handler_goal)

    application.add_handler(
        MessageHandler(filters.Text('Посмотреть информацию о себе'), my_info))
    application.add_handler(CommandHandler('my_info', my_info))
    

    conv_handler_coach = ConversationHandler(
        entry_points=[MessageHandler(filters.Text('Личный фитнес-тренер'), coach), 
                      CommandHandler('coach', coach)],
        states={
            PROMPT: [MessageHandler(filters.TEXT, prompt)],
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler_coach)

    application.run_polling()


if __name__ == '__main__':
    main()
