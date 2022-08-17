# Standard Library
from typing import Dict
import uuid
from enum import Enum, unique

# Third party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.json_encodable_mixin import ENUM_KEY, JSONEncodableMixin


@unique
class ResolutionStatus(Enum):
    """The status of the resolution itself.

    This is distinct from the status of the root run: the root run might not be running
    yet, but the resolution is. Or something may fail in the resolver itself, rather than
    in one of the runs involved in it.

    States
    ------
    CREATED:
        The Resolution is in the DB, but k8s has not been asked to execute it yet.
    SCHEDULED:
        K8s (or the local process, for non-detached) has been asked to execute the
        resolution, but the code has not started executing for it yet.
    RUNNING:
        The code for the resolution is executing.
    FAILED:
        There was an error in the resolution itself, NOT necessarily in the runs that it's
        managing. The resolution may have started getting too many 500s from the Sematic
        server, for example.
    COMPLETE:
        The resolution is done, and it will do no more work. This status may be used even
        if the root run failed, so long as it failed due to some issue in the Sematic
        func execution and not for some other reason. It may also be used if the root run
        was canceled, so long as the cancellation was exited cleanly.
    """

    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    COMPLETE = "COMPLETE"


class Resolution(Base, JSONEncodableMixin):
    """Represents a session of a resolver

    Attributes
    ----------
    root_id:
        The id of the root run which this resolution is resolving.
    current_state:
        The state of the resolver session, see ResolutionStatus.
    is_detached:
        Whether this resolver session is detached (aka executing in the cloud)
        or not.
    """

    __tablename__ = "resolutions"

    root_id: str = Column(
        types.String(),
        nullable=False,
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
    )
    status: ResolutionStatus = Column(  # type: ignore
        types.String(), nullable=False, info={ENUM_KEY: ResolutionStatus}
    )
    is_detached: bool = Column(types.Boolean)
    docker_image_uri: str = Column(types.String(), nullable=True, default=None)
    settings_env_vars: Dict[str, str] = Column(types.JSON, nullable=False, default= lambda: {})

    @validates("status")
    def validate_status(self, key, value) -> str:
        """
        Validates that the status value is allowed.
        """
        if isinstance(value, ResolutionStatus):
            return value.value

        try:
            return ResolutionStatus[value].value
        except Exception:
            raise ValueError("status must be a ResolutionStatus, got {}".format(value))
