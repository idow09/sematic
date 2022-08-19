# Standard Library
import os

import __main__

CONTAINER_IMAGE_ENV_VAR = "SEMATIC_CONTAINER_IMAGE"


def get_image_uri() -> str:
    """Get the URI of the docker image associated with this execution.

    Returns
    -------
    The URI of the image to be used in this execution.
    """
    if CONTAINER_IMAGE_ENV_VAR in os.environ:
        return os.environ[CONTAINER_IMAGE_ENV_VAR]

    with open(
        "{}_push_at_build.uri".format(os.path.splitext(__main__.__file__)[0])
    ) as f:
        return f.read()
