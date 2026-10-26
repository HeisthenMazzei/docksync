from django.core.management.base import BaseCommand
from django.db import transaction

from cargas.models import Carga, FielDepositario, ModeloVeiculo, OperadorPortuario
from navios.models import Navio, Viagem
from manifestos.models import Manifesto, ItemManifesto
from movimentacoes.models import Movimentacao, TrabalhadorPortuario


class Command(BaseCommand):
    help = 'Limpa TODOS os dados operacionais (cargas, manifestos, viagens, movimentações). Preserva usuários, grupos e setores.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tudo', action='store_true',
            help='Também apaga Navios, Operadores, Fieis, Modelos e Trabalhadores.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== LIMPEZA DE DADOS ===\n'))

        with transaction.atomic():
            # 1. Movimentações (dependem de Carga e Trabalhador)
            qtd_mov = Movimentacao.objects.count()
            Movimentacao.objects.all().delete()
            self.stdout.write(f'  ✓ {qtd_mov} movimentações apagadas')

            # 2. Itens de Manifesto
            qtd_itens = ItemManifesto.objects.count()
            ItemManifesto.objects.all().delete()
            self.stdout.write(f'  ✓ {qtd_itens} itens de manifesto apagados')

            # 3. Cargas
            qtd_cargas = Carga.objects.count()
            Carga.objects.all().delete()
            self.stdout.write(f'  ✓ {qtd_cargas} cargas apagadas')

            # 4. Manifestos
            qtd_man = Manifesto.objects.count()
            Manifesto.objects.all().delete()
            self.stdout.write(f'  ✓ {qtd_man} manifestos apagados')

            # 5. Viagens
            qtd_via = Viagem.objects.count()
            Viagem.objects.all().delete()
            self.stdout.write(f'  ✓ {qtd_via} viagens apagadas')

            # 6. Opcional: cadastros auxiliares
            if options['tudo']:
                qtd_nav = Navio.objects.count()
                Navio.objects.all().delete()
                self.stdout.write(f'  ✓ {qtd_nav} navios apagados')

                qtd_op = OperadorPortuario.objects.count()
                OperadorPortuario.objects.all().delete()
                self.stdout.write(f'  ✓ {qtd_op} operadores apagados')

                qtd_fiel = FielDepositario.objects.count()
                FielDepositario.objects.all().delete()
                self.stdout.write(f'  ✓ {qtd_fiel} fieis apagados')

                qtd_mod = ModeloVeiculo.objects.count()
                ModeloVeiculo.objects.all().delete()
                self.stdout.write(f'  ✓ {qtd_mod} modelos apagados')

                qtd_trab = TrabalhadorPortuario.objects.count()
                TrabalhadorPortuario.objects.all().delete()
                self.stdout.write(f'  ✓ {qtd_trab} trabalhadores apagados')

        self.stdout.write(self.style.SUCCESS('\n=== LIMPEZA CONCLUÍDA ===\n'))
        self.stdout.write('  Dica: rode `python manage.py seed_dados` para repopular.\n')