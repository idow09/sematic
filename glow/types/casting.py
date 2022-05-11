# Standard Library
import typing

# Glow
from glow.types.registry import CAN_CAST_REGISTRY, SAFE_CAST_REGISTRY
from glow.types.type import Type


# types must be `typing.Any` because `typing` aliases are not type
def can_cast_type(
    from_type: typing.Any, to_type: typing.Any
) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    `can_cast_type` is the main API to verify castability
    of one type into another.

    Types can be Python builtins, aliases and subscribed from
    `typing`, as well as arbitrary classes.

    Parameters
    ----------
    from_type : Any
        Origin type.
    to_type: Any
        Destination type.

    Returns
    -------
    Tuple[bool, Optional[str]]
        A 2-tuple whose first element is whether `from_type` can
        cast to `to_type`, and the second element is a reason
        if the first element is `False`.
    """
    # Should this be `if issubclass(from_type, to_type)`
    # Can instances of subclasses always cast to their parents?
    if from_type is to_type:
        return True, None

    registry_type = to_type
    if _is_valid_typing(to_type):
        registry_type = to_type.__origin__

    if registry_type in CAN_CAST_REGISTRY:
        _can_cast_func = CAN_CAST_REGISTRY[registry_type]
        return _can_cast_func(from_type, to_type)

    if isinstance(to_type, type) and issubclass(to_type, Type):
        return to_type.can_cast_type(from_type)

    return False, "{} cannot cast to {}".format(from_type, to_type)


# type_ must be `typing.Any` because `typing` aliases are not type
def safe_cast(
    value: typing.Any, type_: typing.Any
) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    """
    `safe_cast` is the main API to safely attempt to cast
    a value to a type.

    Parameters
    ----------
    value : Any
        The candidate value to attempt to cast
    type_ : Any
        The target type to attempt to cast value to

    Returns
    -------
    Tuple[Any, Optional[str]]
        A 2-tuple whose first element is the cast value if
        successful or `None`, and the second element is an error message
        if unsuccessful or `None`.
    """
    registry_type = type_
    if _is_valid_typing(type_):
        registry_type = type_.__origin__
    else:
        # isinstance is not allowed with generics
        if isinstance(value, type_):
            return value, None

    # builtin types and `typing` aliases
    if registry_type in SAFE_CAST_REGISTRY:
        _safe_cast_func = SAFE_CAST_REGISTRY[registry_type]
        return _safe_cast_func(value, type_)

    # Custom types
    if issubclass(type_, Type):
        return type_.safe_cast(value)

    return None, "Can't cast {} to {}".format(value, type_)


def cast(value: typing.Any, type_: type) -> typing.Any:
    """
    Similar to `safe_cast` but will raise an exception if
    casting is unsuccessful.

    Parameters
    ----------
    value : Any
        The candidate value to attempt to cast
    type_ : Any
        The target type to attempt to cast value to

    Returns
    -------
    Any
        Cast value

    Raises
    ------
    TypeError
        If the candidate value could not be cast to target type.
    """
    cast_value, error = safe_cast(value, type_)

    if error is not None:
        raise TypeError("Cannot cast {} to {}: {}".format(value, type_.__name__, error))

    return cast_value


def _is_valid_typing(type_: typing.Any) -> bool:
    """
    Is this a `typing` type, and if so, is it correctly subscribed?
    """
    if isinstance(
        type_, (typing._GenericAlias, typing._UnionGenericAlias)  # type: ignore
    ):
        return True

    if isinstance(type_, (typing._SpecialForm, typing._BaseGenericAlias)):  # type: ignore
        raise ValueError("{} must be parametrized")

    return False