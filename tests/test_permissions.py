import unittest
from types import SimpleNamespace

from bot.permissions import has_playback_permission


class PlaybackPermissionTests(unittest.TestCase):
    def test_creator_is_allowed(self) -> None:
        member = SimpleNamespace(status="creator")
        self.assertTrue(has_playback_permission(member))

    def test_video_chat_admin_is_allowed(self) -> None:
        member = SimpleNamespace(
            status="administrator",
            can_manage_video_chats=True,
        )
        self.assertTrue(has_playback_permission(member))

    def test_admin_without_video_chat_right_is_denied(self) -> None:
        member = SimpleNamespace(
            status="administrator",
            can_manage_video_chats=False,
        )
        self.assertFalse(has_playback_permission(member))

    def test_regular_member_is_denied(self) -> None:
        member = SimpleNamespace(
            status="member",
            can_manage_video_chats=True,
        )
        self.assertFalse(has_playback_permission(member))


if __name__ == "__main__":
    unittest.main()
