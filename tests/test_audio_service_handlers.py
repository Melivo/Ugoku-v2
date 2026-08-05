import unittest

from spotipy.exceptions import SpotifyException

from bot.vocal.audio_service_handlers import get_error_message


class AudioServiceHandlerTests(unittest.TestCase):
    def test_spotify_404_explains_personalized_mix_limitations(self):
        error = SpotifyException(404, -1, "Resource not found")

        message = get_error_message(error)

        self.assertIn("personalized Mix", message)
        self.assertIn("regular playlist", message)

    def test_spotify_403_does_not_expose_internal_api_details(self):
        error = SpotifyException(403, -1, "Forbidden")

        message = get_error_message(error)

        self.assertIn("denied", message)
        self.assertNotIn("https://", message)
