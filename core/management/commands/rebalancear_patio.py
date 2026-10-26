from django.core.management.base import BaseCommand
from setores.models import Setor
from cargas.models import Carga
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Move carros de pátios sobrecarregados para pátios com espaço.'

    def handle(self, *args, **kwargs):
        movidos = 0
        continuar = True

        while continuar:
            continuar = False
            
            # Recarrega os pátios do banco a cada iteração para pegar as novas ocupações
            subpatios = list(Setor.objects.filter(setor_pai__isnull=False).order_by('codigo'))
            
            # Atualiza a ocupação de cada pátio em tempo real
            for setor in subpatios:
                metragem = setor.cargas_presentes.aggregate(total=Sum('metragem_unitaria'))['total'] or 0
                setor.ocupacao_atual = float(metragem)
                setor.espaco_livre = float(setor.capacidade_metragem) - setor.ocupacao_atual

            # 1. Encontra o pátio mais cheio que estourou o limite
            patios_lotados = [s for s in subpatios if s.ocupacao_atual > float(s.capacidade_metragem)]
            patios_lotados.sort(key=lambda x: x.ocupacao_atual - float(x.capacidade_metragem), reverse=True)

            if not patios_lotados:
                break

            patio_origem = patios_lotados[0]
            excesso = patio_origem.ocupacao_atual - float(patio_origem.capacidade_metragem)

            # 2. Encontra o pátio com MAIS espaço livre
            patios_com_espaco = [s for s in subpatios if s.espaco_livre > 0]
            if not patios_com_espaco:
                self.stdout.write(self.style.ERROR("Sem nenhum pátio com espaço. Abortando."))
                break

            patio_destino = max(patios_com_espaco, key=lambda x: x.espaco_livre)

            # 3. Move os carros do mais antigo para o mais novo até zerar o excesso
            carros_para_mover = list(patio_origem.cargas_presentes.order_by('criado_em'))
            
            for carga in carros_para_mover:
                if excesso <= 0:
                    break
                    
                metragem_carga = float(carga.metragem_unitaria)

                if metragem_carga <= patio_destino.espaco_livre:
                    # Move o carro
                    carga.setor_atual = patio_destino
                    carga.save(update_fields=['setor_atual'])
                    
                    # Atualiza as variáveis
                    excesso -= metragem_carga
                    patio_destino.espaco_livre -= metragem_carga
                    movidos += 1
                    continuar = True  # Indica que ainda pode haver pátios estourados

        self.stdout.write(self.style.SUCCESS(f"Movimentação concluída! {movidos} carros foram movidos. Todos os pátios agora estão dentro do limite."))