"""
Models do 2FA (autenticacao em dois fatores com TOTP).

Usuarios, grupos e permissoes continuam sendo os nativos do Django. Aqui ficam so
os dados do SEGUNDO FATOR de cada usuario.
"""

from django.conf import settings
from django.db import models


class SegundoFator(models.Model):
    """
    O segredo TOTP de um usuario (o mesmo que fica no aplicativo autenticador).

    - segredo_cifrado: o segredo NUNCA fica em texto puro no banco; e cifrado com
      uma chave que so existe na variavel de ambiente (ver usuarios/dois_fatores.py).
    - ativo: so vira True depois que o usuario prova que cadastrou no aplicativo
      (digitando um codigo valido). Antes disso o cadastro esta "pendente".
    - ultimo_passo: numero do ultimo intervalo de 30 s ja usado. Um codigo do mesmo
      intervalo (ou de um anterior) e recusado: impede reusar um codigo que vazou.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='segundo_fator',
    )
    segredo_cifrado = models.TextField()
    ativo = models.BooleanField(default=False)
    ultimo_passo = models.BigIntegerField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'segundo fator (2FA)'
        verbose_name_plural = 'segundos fatores (2FA)'

    def __str__(self):
        return f'2FA de {self.usuario} ({"ativo" if self.ativo else "pendente"})'


class CodigoRecuperacao(models.Model):
    """
    Codigo de recuperacao de uso unico (para quando o usuario perde o celular).

    O banco guarda so o HASH do codigo, nunca o codigo em si (igual a senha).
    usado_em preenchido = codigo gasto, nao vale mais.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='codigos_recuperacao',
    )
    codigo_hash = models.CharField(max_length=64, unique=True)
    usado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'código de recuperação'
        verbose_name_plural = 'códigos de recuperação'

    def __str__(self):
        return f'Código de {self.usuario} ({"usado" if self.usado_em else "disponível"})'
