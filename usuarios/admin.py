"""
Admin do Django com SEGUNDO FATOR no login.

Sem isto, o /admin/ seria uma porta dos fundos: quem tivesse a senha de um
superusuario entraria no painel administrativo (que pode tudo) sem o codigo.
"""

from django import forms
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm

from . import dois_fatores
from .models import CodigoRecuperacao, SegundoFator


class LoginAdminComCodigo(AdminAuthenticationForm):
    """Usuario + senha (validados pelo Django) + codigo do autenticador (validado aqui)."""

    codigo = forms.CharField(
        label='Código do autenticador (ou de recuperação)', max_length=16,
        widget=forms.TextInput(attrs={'autocomplete': 'one-time-code', 'inputmode': 'numeric'}),
    )

    def clean(self):
        dados = super().clean()  # confere usuario, senha e se e staff
        usuario = self.get_user()
        codigo = (dados.get('codigo') or '').strip()
        if usuario is None:
            return dados
        if not dois_fatores.tem_2fa_ativo(usuario):
            dois_fatores.registrar_recusa(self.request, usuario, 'admin sem 2FA configurado')
            raise forms.ValidationError(
                'Configure o autenticador antes de entrar no admin '
                '(pelo aplicativo ou: python manage.py configurar_2fa <e-mail>).'
            )
        if '-' in codigo or len(codigo) == 8:
            valido = dois_fatores.usar_codigo_recuperacao(usuario, codigo)
        else:
            valido = dois_fatores.verificar_codigo(usuario, codigo) == 'ok'
        if not valido:
            dois_fatores.registrar_recusa(self.request, usuario, 'codigo invalido no login do admin')
            raise forms.ValidationError('Código inválido, vencido ou já utilizado.')
        return dados


admin.site.login_form = LoginAdminComCodigo
admin.site.login_template = 'admin/login_com_codigo.html'


@admin.register(SegundoFator)
class SegundoFatorAdmin(admin.ModelAdmin):
    # O segredo cifrado nao aparece: so o estado.
    list_display = ['usuario', 'ativo', 'ativado_em', 'criado_em']
    fields = ['usuario', 'ativo', 'ativado_em', 'criado_em']
    readonly_fields = ['usuario', 'ativado_em', 'criado_em']
    search_fields = ['usuario__email', 'usuario__username']


@admin.register(CodigoRecuperacao)
class CodigoRecuperacaoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'usado_em', 'criado_em']
    readonly_fields = ['usuario', 'codigo_hash', 'usado_em', 'criado_em']
    search_fields = ['usuario__email', 'usuario__username']
