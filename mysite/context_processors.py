from .settings import SITE_READ_ONLY


def read_only(request):
    if SITE_READ_ONLY:
        return {"READONLY": True}
    else:
        return {"READONLY": False}
