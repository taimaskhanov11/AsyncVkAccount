import pytest
from mock.mock import Mock

from core.classes.time_track import TimeTrack


class TestTimeTrack:

    # async def test_init(self):
    #     pass  # todo

    def test_stop(self):
        time_track = TimeTrack(123, Mock())
        time_track.stop()
        assert time_track.log.call_count == 1

