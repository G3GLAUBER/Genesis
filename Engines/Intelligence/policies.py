from __future__ import annotations

from Engines.Intelligence.models import (
    AccessMode,
    CostTier,
    ProviderProfile,
    RoutingMode,
)


_COST_ORDER = {
    CostTier.LOCAL: 0,
    CostTier.FREE: 1,
    CostTier.LIMITED_FREE: 2,
    CostTier.PAID: 3,
}


def eligible_profiles(
    profiles: tuple[ProviderProfile, ...],
    *,
    capability: str,
    mode: RoutingMode,
) -> tuple[ProviderProfile, ...]:
    eligible = tuple(
        profile
        for profile in profiles
        if profile.enabled and capability in profile.capabilities
        and not (
            mode is RoutingMode.FREE_ONLY
            and profile.cost_tier is CostTier.PAID
        )
    )
    return tuple(sorted(eligible, key=lambda item: _ranking(item, mode)))


def _ranking(
    profile: ProviderProfile,
    mode: RoutingMode,
) -> tuple[int, int, str]:
    if mode is RoutingMode.LOCAL_FIRST:
        local_rank = 0 if profile.access_mode is AccessMode.LOCAL else 1
        return local_rank, profile.priority, profile.provider_id
    if mode in (RoutingMode.FREE_ONLY, RoutingMode.ECONOMY):
        return _COST_ORDER[profile.cost_tier], profile.priority, profile.provider_id
    return profile.priority, _COST_ORDER[profile.cost_tier], profile.provider_id


def routing_reason(profile: ProviderProfile, mode: RoutingMode) -> str:
    if mode is RoutingMode.LOCAL_FIRST and profile.access_mode is AccessMode.LOCAL:
        return "Provider local habilitado priorizado pelo modo LOCAL_FIRST."
    if mode is RoutingMode.FREE_ONLY:
        return (
            "Provider habilitado e compatível selecionado sem utilizar "
            "recursos pagos."
        )
    if mode is RoutingMode.ECONOMY:
        return "Provider compatível selecionado pela menor faixa de custo."
    return "Provider compatível selecionado por prioridade configurada."
