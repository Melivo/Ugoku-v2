import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from commands.vocal.search import Search


class FakeTrack:
    cover_url = "https://example.com/track.jpg"

    def __init__(self, track_id):
        self.track_id = track_id

    def __format__(self, _format_spec):
        return self.track_id

    def __str__(self):
        return self.track_id


class VocalSearchPlaylistTests(unittest.IsolatedAsyncioTestCase):
    async def test_playlist_search_aggregates_all_pages_for_play_all(self):
        first_page = {
            "items": [
                {"track": {"id": f"track-{index}", "type": "track"}}
                for index in range(50)
            ],
            "next": "page-2",
        }
        second_page = {
            "items": [{"item": {"id": "track-50", "type": "track"}}],
            "next": None,
        }
        spotify_api = SimpleNamespace(
            playlist=Mock(
                return_value={
                    "name": "Long playlist",
                    "images": [{"url": "https://example.com/playlist.jpg"}],
                }
            ),
            playlist_tracks=Mock(return_value=first_page),
            next=Mock(return_value=second_page),
        )
        spotify = SimpleNamespace(
            sessions=SimpleNamespace(sp=spotify_api),
            get_track=Mock(side_effect=lambda track: FakeTrack(track["id"])),
        )
        ctx = SimpleNamespace(
            defer=AsyncMock(),
            respond=AsyncMock(return_value=SimpleNamespace()),
        )
        search = Search(SimpleNamespace(spotify=spotify))
        playlist_url = "https://open.spotify.com/playlist/1234567890123456789012"

        with patch(
            "commands.vocal.search.get_dominant_rgb_from_url",
            new=AsyncMock(return_value=(1, 2, 3)),
        ):
            await search.execute_search(ctx, "track", playlist_url)

        self.assertEqual(spotify.get_track.call_count, 51)
        spotify_api.playlist_tracks.assert_called_once_with(
            playlist_id="1234567890123456789012",
            offset=0,
        )
        self.assertEqual(spotify_api.next.call_args_list, [call(first_page)])


if __name__ == "__main__":
    unittest.main()
