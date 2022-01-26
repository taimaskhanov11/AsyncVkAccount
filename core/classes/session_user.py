import asyncio

from pydantic import BaseModel


# from base_user import BaseUser

class New(BaseModel):
    name: str


# class SessionUser(BaseModel):
#     user_id: int
#     text: str = Field()
#     overlord: New
#
#     def __init__(self, **data):
#         print(data)
#         super().__init__(**data)
#         # self.name = self.overlord.name


class SessionUser:
    def __init__(self, user_id, text, overlord):
        self._info = None
        self.user_id = user_id
        self.text = text
        self.overlord = overlord

    # def __str__(self):
    #     return self.user_id

    def __eq__(self, other):
        if isinstance(other, SessionUser):
            return self.user_id == other.user_id
        return self.user_id == other

    # async def init(self):
    #     self._info = await self.get_self_info()
    #
    # @property
    # def info(self):
    #     return self._info
    #
    # async def get_self_info(self) -> dict:
    #     # res = await self.vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'has_photo', 'city'])
    #     res = await self.overlord.api.users.get(user_ids=self.user_id,
    #                                             fields='sex, bdate, has_photo, city, photo_max_orig')
    #     return res[0]

    # def __contains__(self, item):
    #     print(item)


class AuthenticatedUser:
    pass


class TestUser(AuthenticatedUser):
    pass


dt = {
    1: SessionUser
}


if __name__ == '__main__':
    s1 = SessionUser(1, 'hi', 'k')
    s2 = SessionUser(1, 'hi', 'k')
    # match s1:
        # case dt[k]:
        #     print('True')
        # case _:
        #     print('False')

    # print(dir(AuthenticatedUser))
    # print(s2 in lst)
    # print(s2 in lst)

    # asyncio.run(main())
