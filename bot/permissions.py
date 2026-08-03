from typing import Any

def has_playback_permission(member: Any) -> bool:
    """Allow the owner or an admin explicitly allowed to manage video chats."""
    status = getattr(member.status, "value", member.status)
    if status == "creator":
        return True
    return bool(
        status == "administrator"
        and getattr(member, "can_manage_video_chats", False)
    )
