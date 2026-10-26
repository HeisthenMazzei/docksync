from django.core.management.base import BaseCommand
from setores.models import Setor

class Command(BaseCommand):
    help = 'Cria o Pátio Modelo e os 12 subpátios (P1 ao P12)'

    def handle(self, *args, **kwargs):
        # 1. Criar o Pátio Modelo (Setor Pai)
        patio_modelo, created = Setor.objects.get_or_create(
            codigo='PAT-MODELO',
            defaults={
                'nome': 'Pátio Modelo',
                'capacidade_metragem': 4815.08
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Pátio Modelo criado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING('Pátio Modelo já existia.'))

        # 2. Criar os 12 subpátios (P1 ao P12)
        capacidade_subpatio = 400.00
        for i in range(1, 13):
            nome = f'P{i}'
            codigo = f'P{i}'
            
            # get_or_create evita criar duplicados se você rodar o comando de novo
            subpatio, created = Setor.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nome': nome,
                    'setor_pai': patio_modelo,
                    'capacidade_metragem': capacidade_subpatio
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Subpátio {nome} criado!'))
            else:
                self.stdout.write(self.style.WARNING(f'Subpátio {nome} já existia.'))

        self.stdout.write(self.style.SUCCESS('Processo finalizado com sucesso!'))