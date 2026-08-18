class AssistantJoinError(RuntimeError):
    """The assistant could not be added to the target group."""


class MediaNotFoundError(RuntimeError):
    """No playable media was found for a query."""


class MediaSearchError(RuntimeError):
    """The media provider could not complete a search."""


class PlaybackError(RuntimeError):
    """Telegram voice-chat playback could not be started."""
