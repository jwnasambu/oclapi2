from rest_framework.negotiation import DefaultContentNegotiation


class OptionallyCompressContentNegotiation(DefaultContentNegotiation):
    def select_renderer(self, request, renderers, format_suffix=None):
        if request.META.get('HTTP_COMPRESS', False) in ['true', True]:
            renderers = self.filter_renderers(renderers, 'zip')
            if renderers:
                return renderers[0], 'application/zip'
        return super().select_renderer(request, renderers, format_suffix)
