"""
Helper so Mongo's ObjectId plays nicely with Pydantic v2 models.
"""

from typing import Annotated

from pydantic import BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]
