"""
Regras dos alertas: classificar uma leitura e abrir/atualizar/resolver alertas.

Ideia central:
  1. Pegamos a faixa ideal da viagem (transporte.services.fruit_range).
  2. Classificamos cada medida: normal, warning (atencao) ou critical (critico).
  3. Para nao dar alarme falso (o DHT11 erra ~2 C e ~5% de umidade), so abrimos
     alerta se as ULTIMAS `CONSECUTIVE_READINGS` leituras estao fora da faixa.
  4. Nunca existem dois alertas ativos do mesmo tipo na mesma viagem (o banco
     garante). Enquanto continua fora da faixa, o alerta guarda a PIOR medicao
     (a mais distante do limite) e sobe para critico se piorar; nunca desce.
  5. Quando a medida volta ao normal, o alerta ativo e resolvido sozinho.
  6. Impacto e um evento pontual: abre (ou atualiza) o alerta de impacto na hora,
     sem esperar repeticao, e so e encerrado por uma pessoa.
  7. Concorrencia: a avaliacao trava a linha da viagem (select_for_update), entao
     duas leituras da mesma viagem chegando juntas sao avaliadas uma de cada vez
     (sem IntegrityError por dois alertas "iguais" criados ao mesmo tempo).
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from iot.models import Reading
from transporte.models import Shipment
from transporte.services import fruit_range

from .models import Alert

# Quantas leituras seguidas fora da faixa sao necessarias para abrir um alerta.
CONSECUTIVE_READINGS = 2

# Impacto acima de (limite x este fator) ja e critico.
SHOCK_CRITICAL_FACTOR = Decimal('1.5')

ACTIVE_STATUSES = ['open', 'acknowledged']

UNIDADE = {'temperature': '°C', 'humidity': '%', 'shock': 'g'}
NOME = {'temperature': 'Temperatura', 'humidity': 'Umidade', 'shock': 'Impacto'}


def classify(value, minimum, maximum, critical_margin):
    """
    Classifica UMA medida. Devolve (nivel, limite_violado).

        dentro de [minimo, maximo]          -> ('normal', None)
        fora, ate a margem critica          -> ('warning', limite)
        alem da margem                      -> ('critical', limite)

    Funcao pura (sem banco): facil de testar e de entender.
    """
    if value < minimum:
        distancia, limite = minimum - value, minimum
    elif value > maximum:
        distancia, limite = value - maximum, maximum
    else:
        return 'normal', None

    nivel = 'critical' if distancia > critical_margin else 'warning'
    return nivel, limite


def classify_reading(reading, faixa):
    """Classifica temperatura e umidade de uma leitura contra uma FruitRange."""
    return {
        'temperature': classify(reading.temperature_c, faixa.temperature_min_c, faixa.temperature_max_c,
                                faixa.temperature_critical_margin_c),
        'humidity': classify(reading.humidity_pct, faixa.humidity_min_pct, faixa.humidity_max_pct,
                             faixa.humidity_critical_margin_pct),
    }


def _mensagem(tipo, valor, limite):
    lado = 'acima' if valor > limite else 'abaixo'
    return f'{NOME[tipo]} {valor} {UNIDADE[tipo]} {lado} do limite de {limite} {UNIDADE[tipo]}.'


def _anteriores_tambem_fora(reading, tipo, faixa):
    """As (N-1) leituras anteriores desta viagem tambem estavam fora da faixa neste `tipo`?"""
    necessarias = CONSECUTIVE_READINGS - 1
    if necessarias == 0:
        return True

    anteriores = list(
        Reading.objects
        .filter(shipment=reading.shipment, recorded_at__lt=reading.recorded_at)
        # Desempate deterministico para leituras com o mesmo horario (fila offline).
        .order_by('-recorded_at', '-sequence', '-id')[:necessarias]
    )
    if len(anteriores) < necessarias:
        return False  # ainda nao ha historico suficiente para confirmar
    return all(classify_reading(r, faixa)[tipo][0] != 'normal' for r in anteriores)


def _travar_viagem(shipment_id):
    """Trava a viagem ate o fim da transacao: avaliacoes da mesma viagem rodam em fila."""
    Shipment.objects.select_for_update().filter(pk=shipment_id).values_list('pk', flat=True).first()


@transaction.atomic
def evaluate_reading(reading):
    """
    Avalia uma leitura recem-registrada e abre, atualiza ou resolve alertas.
    Devolve a lista de alertas criados ou alterados por ela.

    A viagem vem da propria leitura: vale mesmo se a viagem ja terminou
    (dado atrasado que chega depois do fim tambem gera alerta).
    """
    faixa = fruit_range(reading.shipment)
    if faixa is None:
        return []  # sem parametros ativos (ou carga incompativel): nao ha como avaliar

    _travar_viagem(reading.shipment_id)
    mudancas = []
    valores = {'temperature': reading.temperature_c, 'humidity': reading.humidity_pct}

    for tipo, (nivel, limite) in classify_reading(reading, faixa).items():
        ativo = (
            Alert.objects.select_for_update()
            .filter(shipment=reading.shipment, type=tipo, status__in=ACTIVE_STATUSES).first()
        )

        if nivel == 'normal':
            if ativo is not None:
                ativo.status = 'resolved'
                ativo.resolved_at = timezone.now()
                ativo.save(update_fields=['status', 'resolved_at'])
                mudancas.append(ativo)
            continue

        if ativo is not None:
            # measured_value = a PIOR medicao enquanto o alerta esta ativo (mais
            # distante do limite), como no impacto, que guarda o maior pico.
            # A severidade so sobe; o alerta so fecha quando volta ao normal.
            pior = abs(valores[tipo] - limite) > abs(ativo.measured_value - ativo.violated_limit)
            sobe = nivel == 'critical' and ativo.severity != 'critical'
            if pior or sobe:
                if pior:
                    ativo.measured_value = valores[tipo]
                    ativo.violated_limit = limite
                    ativo.message = _mensagem(tipo, valores[tipo], limite)
                if sobe:
                    ativo.severity = 'critical'
                ativo.save(update_fields=['severity', 'measured_value', 'violated_limit', 'message'])
                mudancas.append(ativo)
            continue

        if _anteriores_tambem_fora(reading, tipo, faixa):
            mudancas.append(Alert.objects.create(
                shipment=reading.shipment, reading=reading, type=tipo, severity=nivel,
                measured_value=valores[tipo], violated_limit=limite,
                message=_mensagem(tipo, valores[tipo], limite),
            ))

    return mudancas


@transaction.atomic
def evaluate_shock(shock_event):
    """Abre ou atualiza o alerta de impacto se o pico passou do limite da carga. Devolve o alerta ou None."""
    faixa = fruit_range(shock_event.shipment)
    if faixa is None or faixa.impact_max_g is None:
        return None

    pico, limite = shock_event.impact_peak_g, faixa.impact_max_g
    if pico <= limite:
        return None

    nivel = 'critical' if pico > limite * SHOCK_CRITICAL_FACTOR else 'warning'
    _travar_viagem(shock_event.shipment_id)
    ativo = (
        Alert.objects.select_for_update()
        .filter(shipment=shock_event.shipment, type='shock', status__in=ACTIVE_STATUSES).first()
    )

    if ativo is None:
        return Alert.objects.create(
            shipment=shock_event.shipment, shock_event=shock_event, type='shock', severity=nivel,
            measured_value=pico, violated_limit=limite, message=_mensagem('shock', pico, limite),
        )

    # Ja ha alerta de impacto aberto: guarda o MAIOR pico e sobe para critico se for o caso.
    if pico > ativo.measured_value:
        ativo.measured_value = pico
        ativo.shock_event = shock_event
        ativo.message = _mensagem('shock', pico, limite)
        if nivel == 'critical':
            ativo.severity = 'critical'
        ativo.save(update_fields=['measured_value', 'shock_event', 'message', 'severity'])
    return ativo
