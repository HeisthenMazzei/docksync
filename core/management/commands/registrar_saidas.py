from django.core.management.base import BaseCommand
from cargas.models import Carga
from movimentacoes.models import Movimentacao, TrabalhadorPortuario, registrar_movimentacao
from setores.models import Setor
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Registra saídas dos veículos do pátio para popular o Dashboard.'

    def handle(self, *args, **kwargs):
        # Pega o trabalhador de exemplo (ou cria)
        trabalhador, _ = TrabalhadorPortuario.objects.get_or_create(matricula='JSS123456', defaults={'nome_completo': 'José Santos Silva'})
        
        # Pega as cargas que AINDA estão no pátio
        cargas = Carga.objects.filter(setor_atual__isnull=False)
        
        # Para cada carga, se não tiver saída, cria uma
        registradas = 0
        for carga in cargas:
            # Se a carga já tem saída, pula
            if Movimentacao.objects.filter(carga=carga, tipo='SAIDA').exists():
                continue
            
            # Cria uma saída com uma data aleatória nos últimos 3 dias
            data_saida = timezone.now() - timedelta(days=random.randint(0, 3))
            
            # Usamos o comando de registrar movimentação que limpa o setor atual
            # Precisamos de um setor "fora do porto" ou passar um setor fictício, mas o serviço limpa o campo automaticamente
            # No service, se o tipo for SAIDA, setor_destino pode ser qualquer um, pois ele vai limpar o setor_atual
            setor_destino = carga.setor_atual  # Usa o próprio setor para não quebrar a lógica (o service limpa depois)
            
            # Registrar a saída
            registrar_movimentacao(
                carga=carga,
                tipo='SAIDA',
                setor_origem=carga.setor_atual,
                setor_destino=setor_destino,
                trabalhador=trabalhador
            )
            registradas += 1
        
        self.stdout.write(self.style.SUCCESS(f"{registradas} saídas registradas com sucesso!"))