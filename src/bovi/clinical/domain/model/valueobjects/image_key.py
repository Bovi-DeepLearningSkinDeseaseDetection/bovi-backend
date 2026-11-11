from uuid import UUID


def image_key_for(user_id: UUID, evaluation_id: UUID) -> str:
    """S3 key of the photo of an evaluation.

    The backend decides it, never the app: it includes the user, so one farmer can
    never upload or read the photo of another one.
    """
    return f"evaluaciones/{user_id}/{evaluation_id}.jpg"
