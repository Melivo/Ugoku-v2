from discord.voice import VoiceClient


class UgokuVoiceClient(VoiceClient):
    """Voice client with Pycord's send-only member-leave crash guarded."""

    def _remove_ssrc(self, *, user_id: int) -> None:
        ssrc = self._id_to_ssrc.pop(user_id, None)
        if ssrc is None:
            return

        speaking_timer = getattr(self._reader, "speaking_timer", None)
        if speaking_timer is not None:
            speaking_timer.drop_ssrc(ssrc)
        self._ssrc_to_id.pop(ssrc, None)
