import pytest

# request setup
# params ids
from core.database.models import DbAccount, DbUser


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
        token="test_token",
        first_name="test_first_name",
        last_name="test_last_name",
        user_id=1,
        photo_url='test_photo_url',

    )


@pytest.fixture
async def db_user(db_account):
    return await DbUser.create(
        user_id=1, account=db_account, first_name="a", last_name="b"
    )

