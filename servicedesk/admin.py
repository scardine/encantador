from django.contrib import admin

from servicedesk.models import Request, Queue, Update


class UpdateInline(admin.StackedInline):
    model = Update
    extra = 1
    can_delete = False

    def get_queryset(self, request):
        return self.model.objects.none()


class RequestAdmin(admin.ModelAdmin):
    raw_id_fields = ['responsible']
    readonly_fields = ['created_by', 'created', 'updated']
    inlines = [UpdateInline]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['update_list'] = Update.objects.filter(request=object_id)
        return super().change_view(request, object_id, form_url, extra_context)


admin.site.site_header = 'Encantador'
admin.site.register(Request, RequestAdmin)
admin.site.register(Queue)

