from __future__ import annotations

from threading import RLock

from Core.result import Result
from Engines.Intelligence.models import ProviderProfile


class ProviderCatalog:
    """Catálogo de configuração; não localiza providers executáveis."""

    def __init__(self) -> None:
        self._profiles: dict[str, ProviderProfile] = {}
        self._lock = RLock()

    def register(self, profile: ProviderProfile) -> Result:
        if not isinstance(profile, ProviderProfile):
            return Result.error(message="Perfil de provider inválido")
        error = self._validate(profile)
        if error:
            return Result.error(message=error)
        with self._lock:
            if profile.provider_id in self._profiles:
                return Result.error(message="ProviderProfile já registrado")
            self._profiles[profile.provider_id] = profile
        return Result.success(message="ProviderProfile registrado", data=profile)

    def get(self, provider_id: str | None) -> Result:
        normalized = provider_id.strip() if isinstance(provider_id, str) else ""
        with self._lock:
            profile = self._profiles.get(normalized)
        if profile is None:
            return Result.error(message="ProviderProfile não encontrado")
        return Result.success(message="ProviderProfile encontrado", data=profile)

    def list(self) -> tuple[ProviderProfile, ...]:
        with self._lock:
            return tuple(self._profiles.values())

    @staticmethod
    def _validate(profile: ProviderProfile) -> str | None:
        if not profile.provider_id.strip():
            return "provider_id deve ser texto não vazio"
        if not profile.display_name.strip():
            return "display_name deve ser texto não vazio"
        if not profile.capabilities or any(
            not isinstance(item, str) or not item.strip()
            for item in profile.capabilities
        ):
            return "capabilities deve conter textos não vazios"
        if not isinstance(profile.enabled, bool):
            return "enabled deve ser booleano"
        if not isinstance(profile.priority, int) or profile.priority < 0:
            return "priority deve ser maior ou igual a zero"
        return None
