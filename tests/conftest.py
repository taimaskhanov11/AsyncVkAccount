import pytest



# request setup
# params ids
from core.database import DbAccount, DbUser


@pytest.fixture(scope='function')
async def delete_all():
    print('!@#!@#!@#!@#!@#delete_all')
    yield
    # await DbUser.delete_all()
    print('!@#!@#!@#!@#!@#END_delete_all')
    await DbAccount.all().delete()


@pytest.fixture
async def db_account():
    return await DbAccount.create(
        token="1test1",
        first_name="test_first_name_account",
        last_name="test_last_name_account",
        user_id=1,
    )


@pytest.fixture
async def db_user(db_account):
    return await DbUser.create(
        user_id=1, account=db_account, first_name="a", last_name="b"
    )
