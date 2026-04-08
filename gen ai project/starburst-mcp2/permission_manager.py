"""Permission manager for Starburst MCP server.

Loads developer permissions from permissions.yaml with profile+override resolution.
Supports hot-reload: file changes are detected via mtime check.
"""

import os
import yaml
from pathlib import Path


class PermissionManager:
    def __init__(self, config_path: str = None):
        self._config_path = config_path or str(
            Path(__file__).parent / "permissions.yaml"
        )
        self._config = None
        self._mtime = 0
        self._cache = {}
        self._load()

    def _load(self):
        mtime = os.path.getmtime(self._config_path)
        if mtime != self._mtime:
            with open(self._config_path, "r") as f:
                self._config = yaml.safe_load(f)
            self._mtime = mtime
            self._cache = {}

    def resolve(self, developer: str) -> dict:
        """Resolve permissions for a developer. Returns dict of operation -> bool."""
        self._load()
        if developer in self._cache:
            return self._cache[developer]

        defaults = dict(self._config.get("defaults", {}))
        profiles = self._config.get("profiles", {})
        developers = self._config.get("developers", {})

        dev_config = developers.get(developer)
        if dev_config is None:
            self._cache[developer] = defaults
            return defaults

        # For known developers: start all-False, inherit only True-defaults that
        # appear as True for EVERY profile (i.e. read is universally granted).
        # Profile completely replaces defaults for write operations.
        perms = {key: False for key in defaults}
        # Inherit read permission from defaults (always enabled for known developers)
        if defaults.get("read", False):
            perms["read"] = True
        profile_name = dev_config.get("profile")
        if profile_name and profile_name in profiles:
            for key, value in profiles[profile_name].items():
                perms[key] = value

        overrides = dev_config.get("overrides", {})
        for key, value in overrides.items():
            perms[key] = value

        self._cache[developer] = perms
        return perms

    def check(self, developer: str, operation: str) -> bool:
        """Check if a developer is allowed to perform an operation."""
        perms = self.resolve(developer)
        return perms.get(operation, False)

    def check_with_message(self, developer: str, operation: str) -> tuple:
        """Check permission and return (allowed, message) tuple."""
        perms = self.resolve(developer)
        allowed = perms.get(operation, False)
        if allowed:
            return True, ""

        dev_config = self._config.get("developers", {}).get(developer, {})
        profile = dev_config.get("profile", "defaults")
        msg = (
            f"Operation '{operation}' not permitted for developer '{developer}'. "
            f"Current profile: {profile}"
        )
        return False, msg
