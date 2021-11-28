
class ControlMeta(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        # pprint(attrs)
        for key, val in attrs.items():

            # todo update for match case
            if inspect.isfunction(val):

                if key in ('__init__', 'act', 'parse_event', 'start_send_message', 'send_status_tg',
                           '_start_send_message_executor'):
                    continue
                # print(val)
                if asyncio.iscoroutinefunction(val):
                    prop_log.debug(f'async {val}')
                    # attrs[key] = async_time_track(val)
                    attrs[key] = new_async_func(val)
                else:
                    prop_log.debug(f'sync {val}')
                    attrs[key] = time_track(val)
        return super().__new__(mcs, name, bases, attrs, **kwargs)
