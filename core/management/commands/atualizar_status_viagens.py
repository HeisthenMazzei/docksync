from django.core.management.base import BaseCommand
from navios.models import Viagem
from datetime import date

class Command(BaseCommand):
    help = 'Atualiza automaticamente o status das viagens com base nas datas (ETA, ETB, ETS).'

    def handle(self, *args, **kwargs):
        hoje = date.today()
        atualizadas = 0

        viagens = Viagem.objects.all()
        for viagem in viagens:
            novo_status = 'AGUARDANDO_CHEGADA'
            
            # Se já tem data de atracação (ETB) e não passou da data de desatracação (ETS)
            if viagem.data_chegada_real and viagem.data_chegada_real <= hoje:
                if viagem.data_desatracacao and viagem.data_desatracacao < hoje:
                    novo_status = 'FINALIZADO'
                else:
                    novo_status = 'ATRACADO'
            
            if viagem.status != novo_status:
                viagem.status = novo_status
                viagem.save()
                atualizadas += 1

        self.stdout.write(self.style.SUCCESS(f"Status atualizado! {atualizadas} viagens foram atualizadas automaticamente."))