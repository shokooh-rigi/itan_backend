from ajax_select import register, LookupChannel
from mysite.order.models import ControlSystemManufacturer


@register('controlsystem')
class TagsLookup(LookupChannel):

    model = ControlSystemManufacturer

    def get_query(self, q, request):
        return self.model.objects.filter(manufacturer_name__contains=q)

    def format_item_display(self, item):
        return u"<span class='tag'>%s</span>" % item.manufacturer_name
