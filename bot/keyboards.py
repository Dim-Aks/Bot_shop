from aiogram import types

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import fetch_categories, fetch_subcategories, fetch_products_by_subcategory, fetch_subcategory


# Клавиатура категорий
async def send_categories_keyboard(query: types.CallbackQuery):
    await query.message.edit_text(
        "Выберите категорию товаров:",
        reply_markup=await create_categories_keyboard()
    )
    await query.answer()


# кнопки пагинации
def create_pagination_buttons(current_page: int, total_pages: int, prefix: str) -> list[InlineKeyboardButton]:
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:page:{current_page - 1}"))
    buttons.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="ignore"))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:page:{current_page + 1}"))
    return buttons


# Клавиатура категорий с пагинацией
async def create_categories_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    categories = await fetch_categories()
    if not categories:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Нет категорий",
                                                                           callback_data="ignore")],
                                                     [InlineKeyboardButton(text="Перейти в корзину",
                                                                           callback_data="view_cart")]])

    items_per_page = 5  # Количество категорий на одной странице
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_categories = categories[start_index:end_index]
    total_pages = (len(categories) + items_per_page - 1) // items_per_page

    builder = InlineKeyboardBuilder()
    for category in current_categories:
        builder.row(InlineKeyboardButton(text=category.name, callback_data=f"category:{category.id}"))
    builder.row(InlineKeyboardButton(text="Перейти в корзину", callback_data="view_cart"))

    if total_pages > 1:
        builder.row(*create_pagination_buttons(page, total_pages, "category"))

    return builder.as_markup()


# Клавиатура подкатегорий с пагинацией
async def create_subcategories_keyboard(category_id: int, page: int = 1) -> InlineKeyboardMarkup:
    subcategories = await fetch_subcategories(category_id)
    if not subcategories:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Нет подкатегорий",
                                                                           callback_data="ignore")],
                                                     [InlineKeyboardButton(text="Перейти в корзину",
                                                                           callback_data="view_cart")]])

    items_per_page = 5  # Количество подкатегорий на одной странице
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_subcategories = subcategories[start_index:end_index]
    total_pages = (len(subcategories) + items_per_page - 1) // items_per_page

    builder = InlineKeyboardBuilder()
    for subcategory in current_subcategories:
        builder.row(InlineKeyboardButton(text=subcategory.name, callback_data=f"subcategory:{subcategory.id}"))

    if total_pages > 1:
        builder.row(*create_pagination_buttons(page, total_pages, f"subcategory:{category_id}"))

    builder.row(InlineKeyboardButton(text="Назад к категориям", callback_data=f"back_to_categories"))
    builder.row(InlineKeyboardButton(text="Перейти в корзину", callback_data="view_cart"))

    return builder.as_markup()


# клавиатура товаров с пагинацией
async def create_products_keyboard(subcategory_id: int, page: int = 1) -> InlineKeyboardMarkup:
    products = await fetch_products_by_subcategory(subcategory_id)
    subcategory = await fetch_subcategory(subcategory_id)
    if not products:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="Нет товаров", callback_data="ignore"))
        keyboard.row(InlineKeyboardButton(text="Назад к подкатегориям",
                                          callback_data=f"category:{subcategory.category_id}"))
        keyboard.row(InlineKeyboardButton(text="Перейти в корзину", callback_data="view_cart"))
        return keyboard.as_markup()

    items_per_page = 3  # Количество товаров на одной странице
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_products = products[start_index:end_index]
    total_pages = (len(products) + items_per_page - 1) // items_per_page

    builder = InlineKeyboardBuilder()
    for product in current_products:
        builder.row(InlineKeyboardButton(text=product.name, callback_data=f"product:{product.id}"))

    if total_pages > 1:
        builder.row(*create_pagination_buttons(page, total_pages, f"products:{subcategory_id}"))

    builder.row(InlineKeyboardButton(text="Назад к подкатегориям", callback_data=f"category:{subcategory.category_id}"))
    builder.row(InlineKeyboardButton(text="Перейти в корзину", callback_data="view_cart"))

    return builder.as_markup()


# Обработчик кнопки FAQ
async def create_faq_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Как сделать заказ?", callback_data="faq_order")
    keyboard.button(text="Как оплатить заказ?", callback_data="faq_payment")
    keyboard.button(text="Всё сломалось 😢", callback_data="faq_who_boss")
    keyboard.adjust(1)  # Кнопки в один столбец

    return keyboard.as_markup()
