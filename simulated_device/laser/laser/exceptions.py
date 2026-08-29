class LaserDomainError(Exception):
    """Error base para las reglas del dominio del láser."""


class InvalidStateTransitionError(LaserDomainError):
    """Un comando no puede ejecutarse desde el estado actual."""


class TargetPowerNotConfiguredError(LaserDomainError):
    """No existe una potencia objetivo configurada."""


class InvalidTargetPowerError(LaserDomainError):
    """La potencia indicada está fuera del rango permitido."""
class UnsafeRecoveryError(LaserDomainError):
    """No se puede recuperar la maquina"""