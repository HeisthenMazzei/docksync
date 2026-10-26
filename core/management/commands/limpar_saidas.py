from django.core.management.base import BaseCommand
from cargas.models import Carga

class Command(BaseCommand):
    help = 'Remove do pátio todos os veículos que já têm SAÍDA registrada.'

    def handle(self, *args, **kwargs):
        # Busca todas as cargas que têm movimentação de SAÍDA
        cargas_com_saida = Carga.objects.filter(
            movimentacoes__tipo='SAIDA'
        ).distinct()

        removidas = 0
        for carga in cargas_com_saida:
            if carga.setor_atual is not None:
                carga.setor_atual = None
                carga.save(update_fields=['setor_atual'])
                removidas += 1

        self.stdout.write(self.style.SUCCESS(f"{removidas} cargas removidas do pátio."))