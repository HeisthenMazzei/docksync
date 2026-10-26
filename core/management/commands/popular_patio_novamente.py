from django.core.management.base import BaseCommand
from setores.models import Setor
from cargas.models import Carga
from movimentacoes.models import Movimentacao, TrabalhadorPortuario, registrar_movimentacao
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Move todas as cargas sem setor para os pátios novamente.'

    def handle(self, *args, **kwargs):
        # Pega todos os subpátios (filhos)
        subpatios = list(Setor.objects.filter(setor_pai__isnull=False).order_by('codigo'))
        
        # Se não houver subpátios, aborta
        if not subpatios:
            self.stdout.write(self.style.ERROR("Nenhum subpátio cadastrado."))
            return

        # Pega o trabalhador para registrar as movimentações
        trabalhador, _ = TrabalhadorPortuario.objects.get_or_create(
            matricula='JSS123456',
            defaults={'nome_completo': 'José Santos Silva'}
        )

        # Carrega todas as cargas que NÃO têm setor atual
        cargas_sem_setor = list(Carga.objects.filter(setor_atual__isnull=True).order_by('chassi'))
        
        self.stdout.write(self.style.WARNING(f"Encontradas {len(cargas_sem_setor)} cargas sem setor."))

        # Mapeia a capacidade disponível de cada pátio
        capacidade_disponivel = {}
        for setor in subpatios:
            ocupado = setor.cargas_presentes.aggregate(total=Sum('metragem_unitaria'))['total'] or 0
            capacidade_disponivel[setor.id] = float(setor.capacidade_metragem) - float(ocupado)

        movidas = 0
        for carga in cargas_sem_setor:
            metragem = float(carga.metragem_unitaria)
            
            # Encontra o primeiro pátio com espaço para essa carga
            setor_escolhido = None
            for setor in subpatios:
                if capacidade_disponivel[setor.id] >= metragem:
                    setor_escolhido = setor
                    break
            
            # Se não achou espaço, para o processo
            if not setor_escolhido:
                self.stdout.write(self.style.ERROR("Sem espaço nos pátios. Abortando."))
                break
            
            # Atualiza a capacidade disponível
            capacidade_disponivel[setor_escolhido.id] -= metragem

            # 1. Atualiza o setor da carga diretamente
            carga.setor_atual = setor_escolhido
            carga.localizacao_aproximada = f"GPS: {setor_escolhido.codigo}"
            carga.save(update_fields=['setor_atual', 'localizacao_aproximada'])

            # 2. (Opcional) Registra uma movimentação de CHEGADA para manter o histórico correto
            if not Movimentacao.objects.filter(carga=carga, tipo='CHEGADA').exists():
                registrar_movimentacao(
                    carga=carga,
                    tipo='CHEGADA',
                    setor_origem=None,
                    setor_destino=setor_escolhido,
                    trabalhador=trabalhador,
                    localizacao_destino=f"GPS: {setor_escolhido.codigo}"
                )

            movidas += 1

        self.stdout.write(self.style.SUCCESS(f"{movidas} cargas movidas para os pátios com sucesso!"))