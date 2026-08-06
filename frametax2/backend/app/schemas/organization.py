from app.schemas.base import TimestampedSchema


class OrganizationRead(TimestampedSchema):
    name: str
    slug: str
    description: str | None
    website: str | None
    is_active: bool
