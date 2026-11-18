from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from usuarios.acesso import (
    ProtecaoDonoMixin, locais_visiveis, pode_alterar_cadastro, registrar_bloqueio, veiculos_visiveis,
)

from .models import Fruit, FruitParameter, Location, Vehicle
from .serializers import (
    FruitParameterSerializer, FruitSerializer, LocationSerializer, VehicleSerializer,
)

# As views sao "finas": o ModelViewSet ja entrega listar, criar, ver, editar e
# apagar. A permissao vem do padrao do projeto (grupos + permissoes do Django).


class CadastroComDonoMixin(ProtecaoDonoMixin):
    """
    Locais e veiculos (protecao contra IDOR, igual a das viagens e placas):
    - ver: so o que filtrar_por_dono deixa (o de outro vendedor -> 404);
    - criar: o dono e SEMPRE o usuario do token;
    - alterar/apagar: so o dono ou a plataforma (quem so ve -> 403).
    """

    recurso = ''

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def exigir_dono(self, objeto):
        if not pode_alterar_cadastro(self.request.user, objeto):
            registrar_bloqueio(self.request, self.recurso, objeto.pk, motivo='alterar cadastro de outro usuario')
            raise PermissionDenied('Você só pode alterar o que você cadastrou.')

    def perform_update(self, serializer):
        self.exigir_dono(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self.exigir_dono(instance)
        instance.delete()


class LocationViewSet(CadastroComDonoMixin, viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filterset_fields = ['type', 'is_active']
    recurso = 'location'

    def filtrar_por_dono(self, usuario, queryset):
        return locais_visiveis(usuario, queryset)


class VehicleViewSet(CadastroComDonoMixin, viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    filterset_fields = ['is_active']
    recurso = 'vehicle'

    def filtrar_por_dono(self, usuario, queryset):
        return veiculos_visiveis(usuario, queryset)


class FruitViewSet(viewsets.ModelViewSet):
    # Busca os parametros junto (1 consulta a mais no total, nao 1 por fruta).
    queryset = Fruit.objects.prefetch_related(Prefetch('parameters', queryset=FruitParameter.objects.all()))
    serializer_class = FruitSerializer
    filterset_fields = ['is_active']


class FruitParameterViewSet(viewsets.ModelViewSet):
    queryset = FruitParameter.objects.select_related('fruit')
    serializer_class = FruitParameterSerializer
    filterset_fields = ['fruit', 'is_active']
