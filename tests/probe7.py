import asyncio


async def ali(x):
    return x


async def ali2(x):
    return x


async def ali3(x):
    return x


lst = ali, ali2, ali3
signs = (1, 2, 3)
end_lst = (await func(i) for func, i in zip(lst, signs))
print(end_lst)


async def end():
   async for i in end_lst:
        print(i)

asyncio.run(end())