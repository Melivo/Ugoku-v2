import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import discord

from bot.vocal.voice_client import UgokuVoiceClient


class UgokuVoiceClientTests(unittest.TestCase):
    def test_member_leave_without_reader_removes_ssrc(self):
        client = object.__new__(UgokuVoiceClient)
        client._id_to_ssrc = {42: 1234}
        client._ssrc_to_id = {1234: 42}
        client._reader = discord.utils.MISSING

        client._remove_ssrc(user_id=42)

        self.assertEqual(client._id_to_ssrc, {})
        self.assertEqual(client._ssrc_to_id, {})

    def test_member_leave_updates_active_reader(self):
        client = object.__new__(UgokuVoiceClient)
        speaking_timer = SimpleNamespace(drop_ssrc=Mock())
        client._id_to_ssrc = {42: 1234}
        client._ssrc_to_id = {1234: 42}
        client._reader = SimpleNamespace(speaking_timer=speaking_timer)

        client._remove_ssrc(user_id=42)

        speaking_timer.drop_ssrc.assert_called_once_with(1234)
        self.assertEqual(client._id_to_ssrc, {})
        self.assertEqual(client._ssrc_to_id, {})
