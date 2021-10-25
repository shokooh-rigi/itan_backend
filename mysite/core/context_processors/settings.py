from ..models import Setting


def get_settings(request):
    return {
        "field_capitalizer": int(Setting.objects.get(key='Field Capitalizer').value),
    }
