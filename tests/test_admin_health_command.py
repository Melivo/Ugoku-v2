import inspect
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from commands.admin import health as admin_health


def user(user_id, administrator=False):
    return SimpleNamespace(
        id=user_id,
        guild_permissions=SimpleNamespace(administrator=administrator),
    )


def state():
    return {
        "version": 1,
        "gateway": {"connected": True, "ready": True, "latency_ms": 25.0},
        "readiness": {"slash_ready": True, "audio_ready": True},
        "sessions": {"count": 1, "playing": 0},
        "spotify": {"session_alive": True},
        "ffmpeg": {"orphan_sources": 0},
        "voice": {"stuck_connects": 0},
        "event_loop": {"lag_ms": 1.25},
        "resource_blocked": {"blocked": False, "reason": None},
    }


class AdminHealthCommandTests(unittest.IsolatedAsyncioTestCase):
    def test_setup_registers_exactly_health_with_audio_bool_option(self):
        bot = Mock()
        admin_health.setup(bot)
        bot.add_cog.assert_called_once()
        cog = bot.add_cog.call_args.args[0]
        commands = cog.get_commands()
        self.assertEqual([command.name for command in commands], ["health"])
        options = [option for option in commands[0].options if option.name != "ctx"]
        self.assertEqual([option.name for option in options], ["audio"])
        self.assertFalse(options[0].default)
        annotation = inspect.signature(
            admin_health.HealthAdminCog.health.callback
        ).parameters["audio"].annotation
        self.assertNotIsInstance(annotation, str)

    def test_authorization_accepts_admin_guild_owner_and_configured_bot_owner(self):
        guild = SimpleNamespace(owner_id=2)
        contexts = (
            SimpleNamespace(user=user(1, administrator=True), guild=guild),
            SimpleNamespace(user=user(2), guild=guild),
            SimpleNamespace(user=user(3), guild=None),
        )
        with patch.object(admin_health, "ADMIN_OWNER_IDS", [3]):
            self.assertTrue(all(admin_health.HealthAdminCog._is_authorized(ctx) for ctx in contexts))

    async def test_normal_member_is_denied_ephemerally_without_status_leak(self):
        monitor = SimpleNamespace(snapshot=AsyncMock(return_value=state()))
        cog = admin_health.HealthAdminCog(SimpleNamespace(health_monitor=monitor))
        ctx = SimpleNamespace(
            user=user(9),
            guild=SimpleNamespace(owner_id=1),
            respond=AsyncMock(),
        )

        await admin_health.HealthAdminCog.health.callback(cog, ctx, False)

        ctx.respond.assert_awaited_once_with("unauthorized", ephemeral=True)
        monitor.snapshot.assert_not_awaited()

    async def test_authorized_command_returns_ephemeral_embed_and_optional_probe(self):
        probe = {
            "audio_probe": {
                "ok": True,
                "service": "spotify",
                "bytes_read": 8192,
                "duration_s": 0.01,
                "error": None,
            }
        }
        monitor = SimpleNamespace(
            snapshot=AsyncMock(return_value=state()),
            run_readiness_probe=AsyncMock(return_value=probe),
        )
        cog = admin_health.HealthAdminCog(SimpleNamespace(health_monitor=monitor))
        ctx = SimpleNamespace(
            user=user(7, administrator=True),
            guild=SimpleNamespace(owner_id=1),
            respond=AsyncMock(),
        )

        await admin_health.HealthAdminCog.health.callback(cog, ctx, True)

        monitor.run_readiness_probe.assert_awaited_once_with()
        monitor.snapshot.assert_awaited_once_with()
        kwargs = ctx.respond.await_args.kwargs
        self.assertTrue(kwargs["ephemeral"])
        self.assertEqual(kwargs["embed"].title, "Ugoku health")
        self.assertIn("Audio probe", [field.name for field in kwargs["embed"].fields])
