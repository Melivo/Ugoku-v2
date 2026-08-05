import logging
from typing import Any

import discord
from discord.ext import commands

from config import ADMIN_OWNER_IDS, DEFAULT_EMBED_COLOR


logger = logging.getLogger(__name__)


class HealthAdminCog(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @staticmethod
    def _is_authorized(ctx: discord.ApplicationContext) -> bool:
        user = ctx.user
        user_id = getattr(user, "id", None)
        if user_id in ADMIN_OWNER_IDS:
            return True
        guild = ctx.guild
        if guild is None:
            return False
        permissions = getattr(user, "guild_permissions", None)
        is_administrator = bool(
            permissions and getattr(permissions, "administrator", False)
        )
        is_guild_owner = getattr(guild, "owner_id", None) == user_id
        return is_administrator or is_guild_owner

    @commands.slash_command(
        name="health",
        description="Show Ugoku's production health state.",
    )
    async def health(
        self,
        ctx: discord.ApplicationContext,
        audio: discord.Option(  # type: ignore[valid-type]
            bool,
            description="Run the additional single-flight audio readiness probe.",
            default=False,
        ),
    ) -> None:
        if not self._is_authorized(ctx):
            logger.warning(
                "Unauthorized /health request from user %s",
                getattr(ctx.user, "id", "unknown"),
            )
            await ctx.respond("unauthorized", ephemeral=True)
            return

        monitor = getattr(self.bot, "health_monitor", None)
        if monitor is None:
            await ctx.respond("Health monitor unavailable.", ephemeral=True)
            return

        audio_probe = None
        if audio:
            probe = await monitor.run_readiness_probe()
            audio_probe = probe.get("audio_probe")
        state = await monitor.snapshot()
        await ctx.respond(
            embed=self._build_embed(state, audio_probe),
            ephemeral=True,
        )

    @staticmethod
    def _build_embed(
        state: dict[str, Any], audio_probe: dict[str, Any] | None
    ) -> discord.Embed:
        gateway = state.get("gateway") or {}
        readiness = state.get("readiness") or {}
        sessions = state.get("sessions") or {}
        spotify = state.get("spotify") or {}
        ffmpeg = state.get("ffmpeg") or {}
        voice = state.get("voice") or {}
        event_loop = state.get("event_loop") or {}
        blocked = state.get("resource_blocked") or {}

        embed = discord.Embed(
            title="Ugoku health",
            description=f"State schema v{state.get('version', '?')}",
            color=discord.Colour.from_rgb(*DEFAULT_EMBED_COLOR),
        )
        embed.add_field(
            name="Gateway",
            value=(
                f"connected={gateway.get('connected')}\n"
                f"ready={gateway.get('ready')}\n"
                f"latency_ms={_display(gateway.get('latency_ms'))}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Readiness",
            value=(
                f"slash={readiness.get('slash_ready')}\n"
                f"audio={readiness.get('audio_ready')}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Sessions",
            value=(
                f"count={sessions.get('count', 0)}\n"
                f"playing={sessions.get('playing', 0)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Resources",
            value=(
                f"spotify_alive={spotify.get('session_alive')}\n"
                f"ffmpeg_orphans={ffmpeg.get('orphan_sources', 0)}\n"
                f"voice_stuck={voice.get('stuck_connects', 0)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Loop",
            value=f"lag_ms={_display(event_loop.get('lag_ms'))}",
            inline=True,
        )
        embed.add_field(
            name="RESOURCE_BLOCKED",
            value=(
                f"blocked={blocked.get('blocked')}\n"
                f"reason={blocked.get('reason') or 'none'}"
            ),
            inline=True,
        )
        if audio_probe is not None:
            embed.add_field(
                name="Audio probe",
                value=(
                    f"ok={audio_probe.get('ok')}\n"
                    f"service={audio_probe.get('service')}\n"
                    f"bytes={audio_probe.get('bytes_read', 0)}\n"
                    f"duration_s={_display(audio_probe.get('duration_s'))}\n"
                    f"error={audio_probe.get('error') or 'none'}"
                ),
                inline=False,
            )
        return embed


def _display(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(HealthAdminCog(bot))
