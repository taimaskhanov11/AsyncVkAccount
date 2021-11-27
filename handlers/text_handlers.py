async def text_handler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True, prop=False):
    if not color:
        color = LOG_COLORS[log_type][0]
    if TEXT_HANDLER_CONTROLLER['accept_logging']:
        if talk:
            talk_log.__getattribute__(log_type)(f'{sign} {text}')
        if prop:
            prop_log.__getattribute__(log_type)(text)

    if TEXT_HANDLER_CONTROLLER['accept_printing']:
        p_sign = colored(sign, f'bright {color}')
        if prop:
            if TEXT_HANDLER_CONTROLLER['accept_print_property']:
                print(f'{p_sign} {text}')
        else:
            print(f'{p_sign} {text}')

    if TEXT_HANDLER_CONTROLLER['accept_interface']:
        if not off_interface:
            await interface(sign, text, color, full)


def stext_handler(sign, text, log_type='info', color=None, full=False, off_interface=False, talk=True, prop=False):
    if not color:
        color = LOG_COLORS[log_type][0]
    if TEXT_HANDLER_CONTROLLER['accept_logging']:
        if talk:
            talk_log.__getattribute__(log_type)(f'{sign} {text}')
        if prop:
            prop_log.__getattribute__(log_type)(text)

    if TEXT_HANDLER_CONTROLLER['accept_printing']:
        p_sign = colored(sign, f'bright {color}')
        if prop:
            if TEXT_HANDLER_CONTROLLER['accept_print_property']:
                print(f'{p_sign} {text}')
        else:
            print(f'{p_sign} {text}')

    if TEXT_HANDLER_CONTROLLER['accept_interface']:
        if not off_interface:
            asyncio.create_task(interface(sign, text, color, full))


def time_track(func):
    path = os.path.basename(inspect.getsourcefile(func))

    # loop = asyncio.get_event_loop()
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        # print(func_name)
        stext_handler(signs['time'], f'{func_name:<36} {execute_time} | sync', 'debug',
                      off_interface=True, talk=False, prop=True)
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return res

    return sync_wrapper


def async_time_track(func):
    path = os.path.basename(inspect.getsourcefile(func))

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        now = time.monotonic()
        res = await func(*args, **kwargs)
        end = time.monotonic() - now
        execute_time = f'{"Executed time"} {end} s'
        func_name = f'{path}/{func.__name__}'
        await text_handler(signs['time'], f'{func_name:<36} {execute_time} | async', 'debug',
                           off_interface=True, talk=False, prop=True)
        # prop_log.debug(f'{func.__name__} Executed time {round(time.time() - now, 5)} s')
        return res

    return async_wrapper
