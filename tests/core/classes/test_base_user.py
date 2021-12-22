import pytest
from mock.mock import AsyncMock
from tortoise.exceptions import IntegrityError

from core.classes import BaseUser
from core.database.models import DbAccount, DbUser, DbNumber


# @pytest.mark.asyncio
# async def test_connect_db():
#     await init_tortoise('postgres', 'postgres', 'localhost', '5432', 'testdb')
# pytest_plugins = ('user_fixtures',)

@pytest.mark.asyncio()
@pytest.mark.usefixtures('init_db', 'delete_all')
class TestBaseUser:

    # async def setup_class(self):
    #     print('setup_class')

    async def test_add_state_increased(self, user: BaseUser, db_user: DbUser):
        """Проверка увеличения стадии"""

        user.db_user = db_user
        await user.add_state()
        await user.db_user.refresh_from_db()

        assert user.state == 2
        assert user.db_user.state == user.state

    async def test_send_number_calling(self, user: BaseUser):
        """Проверка вызова  у Admin функции send number tg через юзера"""

        user.overlord.send_number_tg = AsyncMock()
        user.overlord.first_name = "test_name"
        user.overlord.info = {"last_name": "test_name"}
        number_text = "number123"
        await user.send_number(number_text)

        assert user.overlord.send_number_tg.call_count == 1
        assert number_text in user.overlord.send_number_tg.call_args[0][0]

    async def test_number_success_table_user_blocked(
            self, user: BaseUser, db_account, db_user: DbUser
    ):
        """Проверка блокировки аккаунта после получения номера"""

        user.db_user = db_user
        user.overlord.send_number_tg = AsyncMock()
        user.overlord.db_account = db_account

        assert user.db_user.blocked is False
        await user.number_success("ok")
        await user.db_user.refresh_from_db()
        assert user.db_user.blocked is True

    async def test_number_success_number_created(
            self, user: BaseUser, db_account: DbAccount, db_user
    ):
        """Проверка создания номера"""

        user.overlord.send_number_tg = AsyncMock()
        user.overlord.db_account = db_account
        user.db_user = db_user
        await user.number_success("ok")
        number = await DbNumber.get(number="ok")
        number_user = await number.user

        assert number.number == "ok"
        assert number_user == user.db_user

    async def test_number_success_raise(
            self, user: BaseUser, db_account: DbAccount, db_user
    ):
        """Проверка вызова исключения при повторном создании номера"""
        user.overlord.send_number_tg = AsyncMock()
        user.overlord.db_account = db_account
        user.db_user = db_user
        await user.number_success("ok")
        with pytest.raises(IntegrityError):
            await user.number_success("ok")

    async def test_number_success_user_add_in_unverified_users(
            self, user: BaseUser, db_account: DbAccount, db_user
    ):
        """Проверка добавления в черный список Admin после получения номера"""

        user.overlord.send_number_tg = AsyncMock()
        user.overlord.db_account = db_account
        user.db_user = db_user
        user.overlord.unverified_users = []
        await user.number_success("ok1234")

        assert user.user_id in user.overlord.unverified_users

    @pytest.mark.parametrize(
        "text", ["Hello friend", "Yes of course", "123 not a number just int", "198"]
    )
    async def test_act_calling_func_without_not_number(self, user: BaseUser, text):
        """Проверка вызовов функций без номера в тексте"""

        user.add_state = AsyncMock()
        user.number_success = AsyncMock()
        user.state = 4
        res = await user.act(text)

        assert isinstance(res, str)
        assert user.add_state.call_count == 1
        assert user.number_success.call_count == 0

    @pytest.mark.parametrize("text", ["test1234",
                                      "test523452345",
                                      "+23452345",
                                      "1234",
                                      "My number 4312", ], )
    async def test_act_calling_func_with_number(self, user: BaseUser, text):
        """Проверка вызовов функций с номером в тексте c цифрами 4 и больше"""

        user.add_state = AsyncMock()
        user.number_success = AsyncMock()
        user.state = 4
        res = await user.act(text)

        assert res is False
        assert user.add_state.call_count == 1
        assert user.number_success.call_count == 1

    async def test_act_more_states(self, user: BaseUser, db_user):
        """Проверка возвращаемого значения user.act для всей стадий"""

        user.number_success = AsyncMock()
        user.db_user = db_user

        for i in range(2, user.len_template + 2):
            res = await user.act("test")
            if i < user.len_template + 1:
                assert isinstance(res, str)
            else:
                assert res is False
