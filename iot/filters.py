"""Filtros de consulta das leituras (usados em /readings e em /shipments/{id}/readings)."""

from django_filters import rest_framework as filters

from .models import Reading


class ReadingFilter(filters.FilterSet):
    # /readings?shipment=3&start=2026-10-01T00:00:00Z&end=2026-10-02T00:00:00Z
    start = filters.IsoDateTimeFilter(field_name='recorded_at', lookup_expr='gte')
    end = filters.IsoDateTimeFilter(field_name='recorded_at', lookup_expr='lte')
    # So o que chegou depois de um instante: o front busca so as novas a cada atualizacao.
    since = filters.IsoDateTimeFilter(field_name='recorded_at', lookup_expr='gt')

    class Meta:
        model = Reading
        fields = ['device', 'shipment']
