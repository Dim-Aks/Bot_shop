import logging
import os

from aiogram import types, Bot, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from database import fetch_product, \
    add_to_cart, fetch_cart, remove_from_cart, clear_cart, add_user_if_not_exists
from keyboards import create_categories_keyboard, \
    create_subcategories_keyboard, create_products_keyboard
from state import QuantityForm, DeliveryForm
from utils import check_subscription_by_username

router = Router()
load_dotenv()
logger = logging.getLogger(__name__)

# Канал/группа для проверки подписки
CHANNEL_USERNAME = os.getenv("CHANNEL_ID")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")


# Oбработчик команды start
@router.message(CommandStart())
async def command_start_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id

    # Добавляем пользователя в базу данных, если его там еще нет
    await add_user_if_not_exists(user_id, message.from_user.username, message.from_user.first_name,
                                 message.from_user.last_name
                                 )

    # Проверяем пользователя на подписку на канал
    if CHANNEL_USERNAME:
        is_subscribed = await check_subscription_by_username(bot, user_id, CHANNEL_USERNAME)
        if not is_subscribed:
            await message.reply("Пожалуйста, подпишитесь на канал @Aksenona, чтобы использовать бота.")
            return
    await message.answer("Добро пожаловать!\nВыберите категорию товаров:",
                         reply_markup=await create_categories_keyboard()
                         )


# Oбработчик выбора категории
@router.callback_query(F.data.startswith("category:"))
async def category_callback(query: CallbackQuery):
    category_id = int(query.data.split(":")[1])
    await query.message.edit_text("Выберите подкатегорию:",
                                  reply_markup=await create_subcategories_keyboard(category_id)
                                  )
    await query.answer()


# Обработчик выбора подкатегории
@router.callback_query(F.data.startswith("subcategory:"))
async def subcategory_callback(query: CallbackQuery):
    subcategory_id = int(query.data.split(":")[1])
    await query.message.edit_text("Выберите товар:", reply_markup=await create_products_keyboard(subcategory_id))
    await query.answer()


# Обработчик выбора товара
@router.callback_query(F.data.startswith("product:"))
async def product_callback(query: CallbackQuery, state: FSMContext):
    product_id = int(query.data.split(":")[1])
    product = await fetch_product(product_id)

    if product:

        # Создаем inline-клавиатуру
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_to_cart:{product_id}"))
        keyboard.row(InlineKeyboardButton(text="Назад к товарам", callback_data=f"subcategory:{product.subcategory_id}"))

        # Проверка на наличие фото
        if product.photo:
            try:
                await query.message.answer_photo(
                    photo=types.FSInputFile(product.photo),  # Или types.URLInputFile
                    caption=f"<b>{product.name}</b>\n\n{product.description}\n\nЦена: {product.price} руб.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard.as_markup()
                )
            except Exception as e:
                logging.error(f"Ошибка вывода фото: {e}")
                await query.message.answer(
                    f"<b>{product.name}</b>\n\n{product.description}\n\nЦена: {product.price} руб.\n"
                    f"(Фото не удалось загрузить)",
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard.as_markup()
                )

        else:
            await query.message.answer(
                f"<b>{product.name}</b>\n\n{product.description}\n\nЦена: {product.price} руб.",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard.as_markup()
            )

        # Сохраняем ID продукта в FSMContext
        await state.update_data(product_id=product_id)
        await query.answer()
    else:
        await query.answer("Товар не найден.")


# Обработчик нажатия кнопки Добавить в корзину
@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart_callback(query: CallbackQuery, state: FSMContext):
    product_id = int(query.data.split(":")[1])
    await state.set_state(QuantityForm.quantity)
    await state.update_data(product_id=product_id)  # Сохраняем ID продукта в state
    await query.message.answer("Введите количество товара:")
    await query.answer()


# Обработчик ввода количества товара
@router.message(QuantityForm.quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.reply("Пожалуйста, введите положительное число.")
            return

        user_data = await state.get_data()
        product_id = user_data.get('product_id')  # Получаем ID продукта из state

        if not product_id:
            logger.error(f"Product ID не найден в state для пользователя {message.from_user.id}")
            await message.reply("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            await state.clear()
            return

        success = await add_to_cart(message.from_user.id, product_id, quantity)
        if success:
            await message.answer(
                f"Добавлено {quantity} шт. в корзину!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перейти в корзину",
                                                                                         callback_data="view_cart"
                                                                                         )],
                                                                   [InlineKeyboardButton(text="Назад к категориям",
                                                                                         callback_data="back_to_categories"
                                                                                         )]
                                                                   ]
                                                  )
            )
        else:
            await message.answer("Не удалось добавить товар в корзину. Попробуйте позже.")

        await state.clear()  # Очищаем state после успешного добавления
    except ValueError:
        await message.reply("Пожалуйста, введите число.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в process_quantity для пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла непредвиденная ошибка. Попробуйте позже.")
        await state.clear()


# Обработчик просмотра корзины
@router.callback_query(F.data == "view_cart")
async def view_cart_callback(query: CallbackQuery):
    cart_items = await fetch_cart(query.from_user.id)

    if not cart_items:
        await query.message.answer("Ваша корзина пуста.")
        await query.answer()
        return

    total_amount = 0
    cart_text = "<b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        cart_text += f"{item['name']} x {item['quantity']} - {item['price'] * item['quantity']} руб.\n"
        total_amount += item['price'] * item['quantity']

    cart_text += f"\n<b>Итого: {total_amount} руб.</b>"

    # Добавляем кнопки для удаления товаров и перехода к оформлению
    keyboard = InlineKeyboardBuilder()
    for item in cart_items:
        keyboard.row(
            InlineKeyboardButton(text=f"Удалить {item['name']}", callback_data=f"remove_from_cart:{item['id']}")
        )
    keyboard.row(InlineKeyboardButton(text="Оформить заказ", callback_data="checkout"))
    keyboard.row(InlineKeyboardButton(text="Назад к категориям", callback_data="back_to_categories"))

    await query.message.answer(cart_text, parse_mode=ParseMode.HTML, reply_markup=keyboard.as_markup())
    await query.answer()


# Обработчик удаления товара из корзины
@router.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_from_cart_callback(query: CallbackQuery):
    item_id = int(query.data.split(":")[1])
    if await remove_from_cart(item_id):
        await query.message.answer("Товар удален из корзины.")
        # Обновляем отображение корзины
        await view_cart_callback(query)
    else:
        await query.answer("Не удалось удалить товар.")


# Обработчик начала оформления заказа
@router.callback_query(F.data == "checkout")
async def checkout_callback(query: CallbackQuery, state: FSMContext):
    await state.set_state(DeliveryForm.name)
    await query.message.answer("Пожалуйста, введите ваше имя:")
    await query.answer()


# Обработчик ввода имени для доставки
@router.message(DeliveryForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(DeliveryForm.address)
    await message.answer("Введите ваш адрес доставки:")


# Обработчик ввода адреса для доставки
@router.message(DeliveryForm.address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(DeliveryForm.phone)
    await message.answer("Введите ваш номер телефона:")


# Обработчик ввода номера телефона для доставки и подтверждения заказа
@router.message(DeliveryForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    delivery_data = await state.get_data()

    # Получаем данные о корзине пользователя
    cart_items = await fetch_cart(message.from_user.id)
    if not cart_items:
        await message.answer("Ваша корзина пуста.")
        await state.clear()
        return

    total_amount = 0
    order_text = "<b>Подтвердите ваш заказ:</b>\n\n"
    for item in cart_items:
        order_text += f"{item['name']} x {item['quantity']} - {item['price'] * item['quantity']} руб.\n"
        total_amount += item['price'] * item['quantity']

    order_text += f"\n<b>Итого: {total_amount} руб.</b>"
    order_text += (f"\n\n<b>Данные доставки:</b>\nИмя: {delivery_data['name']}\n"
                   f"Адрес: {delivery_data['address']}\nТелефон: {delivery_data['phone']}")

    # Создаем кнопку для оплаты
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Оплатить", callback_data="pay"))
    keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_order"))  # Добавляем кнопку отмены

    await message.answer(order_text, parse_mode=ParseMode.HTML, reply_markup=keyboard.as_markup())
    await state.update_data(total_amount=total_amount)  # Сохраняем сумму для оплаты
    await state.set_state(None)  # Сбрасываем состояние


# Обработчик нажатия кнопки "Оплатить
@router.callback_query(F.data == "pay")
async def pay_callback(query: CallbackQuery, state: FSMContext):
    if not PAYMENT_TOKEN:
        await query.answer("Ошибка: не настроен токен для платежей.")
        return

    user_data = await state.get_data()
    total_amount = user_data.get('total_amount', 0)

    if total_amount <= 0:
        await query.answer("Некорректная сумма заказа.")
        return

    prices = [LabeledPrice(label="Заказ", amount=int(total_amount * 100))]

    await Bot.send_invoice(
        chat_id=query.from_user.id,
        title="Оплата заказа",
        description="Оплата вашего заказа в Telegram боте.",
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="example",
        payload="some_invoice_payload",
        need_name=True,
        need_phone_number=True,
        need_shipping_address=False,  # если нужен адрес доставки
        send_email_to_provider=False,  # отправка почты
        # is_flexible=False   Указывает, можно ли менять сумму
    )
    await query.answer()  # Подтверждаем получение callback_query


# @router.pre_checkout_query()
# async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
#     """
#     Проверка перед оплатой. В реальном проекте здесь нужно проверять
#     наличие товара, возможность доставки и другие параметры заказа.
#     """
#     await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# Обработчик успешной оплаты
@router.message(F.content_type == types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message, state: FSMContext):
    await message.answer("Спасибо за оплату! Ваш заказ принят в обработку.")
    await clear_cart(message.from_user.id)  # Очищаем корзину после успешной оплаты
    await state.clear()


# Обработчик отмены заказа
@router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Заказ отменен.")
    await state.clear()  # Сбрасываем состояние
    await query.answer()


# Обработчик inline-запросов для FAQ
@router.inline_query(lambda q: len(q.query) > 3)
async def faq_inline_query(inline_query: types.InlineQuery):
    # Здесь должна быть логика получения вопросов и ответов из базы данных
    # или другого источника. Для примера, просто заглушка:
    results = [
        types.InlineQueryResultArticle(
            id="1",
            title="Как сделать заказ?",
            description="Подробная инструкция по оформлению заказа.",
            input_message_content=types.InputTextMessageContent(
                message_text="Чтобы сделать заказ, выберите товары и перейдите в корзину."
            ),
        ),
        types.InlineQueryResultArticle(
            id="2",
            title="Как оплатить заказ?",
            description="Информация о способах оплаты.",
            input_message_content=types.InputTextMessageContent(
                message_text="Оплатить заказ можно через платежный шлюз ЮKassa."
            ),
        ),
    ]
    await inline_query.answer(results, cache_time=1)  # cache_time - время кеширования результатов в секундах


# Обработчик пагинации категорий
@router.callback_query(F.data.startswith("categories:page:"))
async def categories_page_callback(query: CallbackQuery):
    page = int(query.data.split(":")[2])
    await query.message.edit_text("Выберите категорию:", reply_markup=await create_categories_keyboard(page))
    await query.answer()


# Обработчик пагинации подкатегорий
# Максимум 10 страниц для примера
@router.callback_query(F.data.startswith("subcategory:") & F.data.endswith((":page:" + str(i) for i in range(1, 10))))
async def subcategories_page_callback(query: CallbackQuery):
    data_parts = query.data.split(":")
    category_id = int(data_parts[1])
    page = int(data_parts[3])
    await query.message.edit_text("Выберите подкатегорию:",
                                  reply_markup=await create_subcategories_keyboard(category_id, page)
                                  )
    await query.answer()


# Обработчик пагинации товаров
# Максимум 10 страниц для примера
@router.callback_query(F.data.startswith("products:") & F.data.endswith((":page:" + str(i) for i in range(1, 10))))
async def products_page_callback(query: CallbackQuery):
    data_parts = query.data.split(":")
    subcategory_id = int(data_parts[1])
    page = int(data_parts[3])
    await query.message.edit_text("Выберите товар:", reply_markup=await create_products_keyboard(subcategory_id,
                                                                                                 page
                                                                                                 )
                                  )
    await query.answer()


# Обработчик кнопки Назад к категориям
@router.callback_query(F.data == "back_to_categories")
async def back_to_categories_callback(query: CallbackQuery):
    await query.message.edit_text("Выберите категорию:", reply_markup=await create_categories_keyboard())
    await query.answer()
