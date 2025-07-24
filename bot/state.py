from aiogram.fsm.state import State, StatesGroup


class QuantityForm(StatesGroup):
    quantity = State()
    product_id = State()  # Добавлено состояние для хранения ID продукта


# форма для оформления доставки
class DeliveryForm(StatesGroup):
    name = State()
    address = State()
    phone = State()
