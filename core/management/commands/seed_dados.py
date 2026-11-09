import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from cargas.models import Carga, FielDepositario, ModeloVeiculo, OperadorPortuario
from navios.models import Navio, Viagem
from manifestos.models import Manifesto, ItemManifesto
from movimentacoes.models import Movimentacao, TrabalhadorPortuario, registrar_movimentacao
from setores.models import Setor


# ============================================================
# COORDENADAS DO PÁTIO (Vitória/ES) — para simular o GPS
# ============================================================
PATIO_LAT_BASE = -20.328279
PATIO_LNG_BASE = -40.331324


def gerar_coordenada():
    """Gera uma coordenada com pequena variação aleatória em torno do pátio."""
    lat = PATIO_LAT_BASE + random.uniform(-0.0008, 0.0008)
    lng = PATIO_LNG_BASE + random.uniform(-0.0008, 0.0008)
    return round(lat, 6), round(lng, 6)


# ============================================================
# DADOS DO LINEUP Docksync (Nova Lineup)
# ============================================================
LINEUP_DATA = [
    ("2026049331", "103", "INTEGRADOR", "Aprovada", "03/11/2026 06:00", "09/11/2026 05:05", "09/11/2026 21:30", "ORION RODOS MARITIMA E PORTUÁRIA LTDA"),
    ("2026051571", "203", "GREEN PORTOCEL", "Aprovada", "03/11/2026 08:00", "05/11/2026 13:15", "09/11/2026 22:04", "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."),
    ("2026050064", "202", "PACIFICA", "Aprovada", "04/11/2026 15:30", "06/11/2026 10:50", "10/11/2026 10:25", "ATLANTIC AGENCIA DE NAVEGACAO LTDA ME"),
    ("2026044969", "906", "SAPURA DIAMANTE (BAND. GREYLIST PARIS MOU)", "Aprovada", "07/11/2026 07:00", "07/11/2026 10:40", "10/11/2026 21:40", "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"),
    ("2026052331", "502", "MANTA BEYOGLU", "Aprovada", "07/11/2026 15:00", "08/11/2026 13:33", "10/11/2026 13:30", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026052901", "204", "LOG-IN PANTANAL (REB)", "Aprovada", "08/11/2026 23:00", "09/11/2026 00:31", "10/11/2026 02:34", "MSC MEDITERRANEAN SHIPPING DO BRASIL LTDA"),
    ("2026053523", "102", "TS ARROJADO", "Aprovada", "09/11/2026 06:00", "09/11/2026 09:15", "10/11/2026 13:00", "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"),
    ("2026053529", "102", "TS 5", "Aprovada", "09/11/2026 06:00", "09/11/2026 09:15", "10/11/2026 13:00", "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"),
    ("2026051368", "203", "GREEN RIO DE JANEIRO", "Aprovada", "02/11/2026 08:30", "10/11/2026 14:23", "15/11/2026 05:51", "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."),
    ("2026050643", "101", "BAR", "Incluída", "17/11/2026 00:00", "17/11/2026 01:00", "19/11/2026 10:24", "ORION RODOS MARITIMA E PORTUÁRIA LTDA"),
    ("2026053006", "101", "ISLAND ENFORCER (REB)", "Incluída", "10/11/2026 05:00", "10/11/2026 05:30", "11/11/2026 08:00", "PROAMAR SERVIÇOS DE DESPACHOS MARÍTIMOS LTDA"),
    ("2026053060", "201", "COSCO SHIPPING XING WANG", "Incluída", "18/11/2026 17:00", "18/11/2026 18:00", "29/11/2026 13:48", "WILHELMSEN PORT SERVICES BRASIL LTDA"),
    ("2026052741", "201", "PAX MUNDI", "Incluída", "18/11/2026 01:00", "19/11/2026 05:59", "22/11/2026 22:39", "UNIPORT AGÊNCIA MARÍTIMA LTDA EPP"),
    ("2026053169", "201", "PEACE BAND", "Incluída", "13/11/2026 10:00", "13/11/2026 11:00", "16/11/2026 00:32", "WILSON SONS SHIPPING SERVICES LTDA"),
    ("2026052428", "201", "NORDIC LUEBECK", "Incluída", "20/11/2026 12:00", "20/11/2026 13:00", "23/11/2026 06:43", "GEM SHIPPING LTDA"),
    ("2026050725", "202", "GRANDE SAN PAOLO", "Incluída", "20/11/2026 07:00", "20/11/2026 08:00", "20/11/2026 18:27", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026051273", "202", "GRANDE GUINEA", "Incluída", "20/11/2026 06:00", "22/11/2026 23:39", "23/11/2026 09:03", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026053426", "202", "FEDERAL RUHR", "Incluída", "09/11/2026 16:30", "10/11/2026 11:45", "16/11/2026 08:19", "WILHELMSEN PORT SERVICES BRASIL LTDA"),
    ("2026052449", "202", "NIKOS", "Incluída", "14/11/2026 23:00", "16/11/2026 07:59", "21/11/2026 03:47", "Amart Services Consultoria, Agenciamento Marítimo e Transporte Ltda"),
    ("2026053141", "202", "POLARIS LEADER", "Incluída", "20/11/2026 04:00", "20/11/2026 04:01", "21/11/2026 03:00", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026051605", "203", "GREEN GUANGZHOU", "Incluída", "12/11/2026 12:00", "15/11/2026 06:51", "18/11/2026 16:00", "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."),
    ("2026052980", "204", "LOG-IN DISCOVERY (REB S/L)", "Aprovada", "09/11/2026 23:30", "10/11/2026 09:25", "12/11/2026 15:25", "MSC MEDITERRANEAN SHIPPING DO BRASIL LTDA 02.378.779/0009-66"),
    ("2026053097", "207", "MICHIGAN HIGHWAY", "Incluída", "14/11/2026 18:00", "16/11/2026 01:32", "16/11/2026 22:22", "UNIMAR AGENCIAMENTOS MARITIMOS LTDA"),
    ("2026053516", "207", "BOSPORUS HIGHWAY", "Incluída", "17/11/2026 06:00", "17/11/2026 07:00", "17/11/2026 07:00", "UNIMAR AGENCIAMENTOS MARITIMOS LTDA"),
    ("2026049799", "207", "YU AN", "Incluída", "12/11/2026 00:00", "12/11/2026 01:00", "14/11/2026 22:00", "ORION RODOS MARITIMA E PORTUÁRIA LTDA"),
    ("2026052325", "207", "MERMAID ACE", "Incluída", "10/11/2026 06:00", "10/11/2026 11:25", "10/11/2026 23:00", "Rochamar Agência Maritima S/A"),
    ("2026052435", "905", "MAERSK KATALIN", "Incluída", "14/11/2026 00:00", "14/11/2026 01:00", "17/11/2026 22:00", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026052166", "905", "AFRICAN MACAW", "Incluída", "18/11/2026 01:00", "18/11/2026 02:00", "24/11/2026 00:56", "UNIPORT AGÊNCIA MARÍTIMA LTDA EPP"),
    ("722", "909", "BRAM BRAVO", "Incluída", "10/11/2026 08:00", "10/11/2026 08:30", "10/11/2026 20:00", "PROAMAR SERVIÇOS DE DESPACHOS MARÍTIMOS LTDA"),
]


def parse_data(s):
    try:
        return datetime.strptime(s, "%d/%m/%Y %H:%M").date()
    except Exception:
        return None


VIN_PREFIX = {
    "GWM": "9BW", "TOYOTA": "9BR", "HYUNDAI": "9BH", "HONDA": "93H",
    "FIAT": "9BD", "CHEVROLET": "9BG", "NISSAN": "94D", "VOLKSWAGEN": "9BW",
}


def gerar_chassi(fabricante, seq):
    prefix = VIN_PREFIX.get(fabricante.upper(), "9BW")
    vds = "".join(random.choices("ABCDEFGHJKLMNPRSTUVWXYZ0123456789", k=6))
    check = random.choice("0123456789X")
    year = "R"
    plant = random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")
    seq_str = str(seq).zfill(5)
    return f"{prefix}{vds}{check}{year}{plant}{seq_str}"


def criar_movimentacao_com_data(carga, tipo, setor_origem, setor_destino, trabalhador, data_hora_alvo, **kwargs):
    mov = registrar_movimentacao(
        carga=carga,
        tipo=tipo,
        setor_origem=setor_origem,
        setor_destino=setor_destino,
        trabalhador=trabalhador,
        **kwargs
    )
    Movimentacao.objects.filter(pk=mov.pk).update(data_hora=data_hora_alvo)
    mov.refresh_from_db()
    return mov


class Command(BaseCommand):
    help = 'Popula o sistema com dados do lineup Docksync e simula movimentações'

    def add_arguments(self, parser):
        parser.add_argument('--manifestos', type=int, default=12,
                            help='Número de manifestos a simular (padrão: 12)')
        parser.add_argument('--chassis-min', type=int, default=10,
                            help='Mínimo de chassis por manifesto (padrão: 10)')
        parser.add_argument('--chassis-max', type=int, default=20,
                            help='Máximo de chassis por manifesto (padrão: 20)')

    def handle(self, *args, **options):
        random.seed(42)

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== SEED Docksync — Lineup Nova ===\n'))

        # 1. OPERADORES
        self.stdout.write('[1/7] Criando Operadores Portuários...')
        agencias = sorted(set(row[7].strip() for row in LINEUP_DATA))
        operadores_map = {}
        for agencia in agencias:
            op, _ = OperadorPortuario.objects.get_or_create(
                nome_empresa=agencia[:255],
                defaults={
                    'cnpj': f"00.{random.randint(100, 999)}.{random.randint(100, 999)}/0001-{random.randint(10, 99)}",
                    'situacao': 'Ativo',
                }
            )
            operadores_map[agencia] = op
        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(agencias)} operadores'))

        # 2. NAVIOS
        self.stdout.write('[2/7] Criando Navios...')
        navios_map = {}
        for nome in sorted(set(row[2] for row in LINEUP_DATA)):
            navio, _ = Navio.objects.get_or_create(nome=nome)
            navios_map[nome] = navio
        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(navios_map)} navios'))

        # 3. VIAGENS
        self.stdout.write('[3/7] Criando Viagens...')
        hoje = timezone.now().date()
        viagens_map = []
        for programacao, berco, navio_nome, psp, eta_s, etb_s, ets_s, agencia in LINEUP_DATA:
            eta = parse_data(eta_s)
            etb = parse_data(etb_s)
            ets = parse_data(ets_s)

            if ets and hoje >= ets:
                status = 'FINALIZADO'
            elif etb and hoje >= etb:
                status = 'ATRACADO'
            elif eta and hoje >= eta:
                status = 'FUNDEADO'
            else:
                status = 'AGUARDANDO_CHEGADA'

            sentido = 'DESCARGA' if random.random() < 0.6 else 'CARGA'

            viagem, _ = Viagem.objects.update_or_create(
                navio=navios_map[navio_nome],
                numero_viagem=programacao,
                defaults={
                    'operador_portuario': operadores_map.get(agencia),
                    'sentido': sentido,
                    'psp': psp,
                    'data_prevista_chegada': eta,
                    'data_chegada_real': etb,
                    'data_desatracacao': ets,
                    'bercario_atracacao': berco,
                    'agencia': agencia,
                    'status': status,
                }
            )
            viagens_map.append(viagem)
        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(viagens_map)} viagens'))

        # 4. FIEIS
        self.stdout.write('[4/7] Criando Fiel Depositários...')
        fieis_data = [
            ('Heisthen Mazzel Scarparo', 'HMS123456'),
            ('Carlos Eduardo Lima', 'CEL789012'),
            ('Mariana Alves Ribeiro', 'MAR345678'),
            ('João Pedro Santos', 'JPS901234'),
            ('Renata Oliveira Costa', 'ROC567890'),
        ]
        fieis = []
        for nome, mat in fieis_data:
            fiel, _ = FielDepositario.objects.get_or_create(matricula=mat, defaults={'nome_completo': nome})
            fieis.append(fiel)
        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(fieis)} fieis'))

        # 5. MODELOS
        self.stdout.write('[5/7] Criando Modelos de Veículos...')
        modelos_data = [
            ('GWM', 'HAVAL H6', 'HAVAL H6', 2026, 4.80, 1.85),
            ('TOYOTA', 'HILUX', 'HILUX', 2024, 5.30, 1.85),
            ('HYUNDAI', 'TUCSON', 'TUCSON', 2025, 4.50, 1.85),
            ('HONDA', 'CIVIC', 'CIVIC', 2025, 4.70, 1.80),
            ('FIAT', 'TORO', 'TORO', 2025, 4.95, 1.85),
            ('VOLKSWAGEN', 'AMAROK', 'AMAROK', 2025, 5.25, 1.95),
            ('CHEVROLET', 'S10', 'S10', 2025, 5.35, 1.85),
            ('NISSAN', 'FRONTIER', 'FRONTIER', 2025, 5.25, 1.85),
        ]
        modelos = []
        for fab, mod, abrev, ano, comp, larg in modelos_data:
            m, _ = ModeloVeiculo.objects.get_or_create(
                fabricante=fab, modelo=mod, ano=ano,
                defaults={'comprimento': comp, 'largura': larg, 'abreviado': abrev}
            )
            m.abreviado = abrev
            m.metragem_m2 = round(float(comp) * float(larg), 2)
            m.save()
            modelos.append(m)
        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(modelos)} modelos'))

        # 6. TRABALHADORES
        self.stdout.write('[6/7] Criando Trabalhadores Portuários...')
        trabalhadores_data = [
            ('José Santos Silva', 'JSS123456'),
            ('Antônio Pereira Costa', 'APC234567'),
            ('Marcos Vinícius Rocha', 'MVR345678'),
            ('Paulo Henrique Dias', 'PHD456789'),
            ('Ricardo Almeida Souza', 'RAS567890'),
            ('Fernando Oliveira Lima', 'FOL678901'),
        ]
        trabalhadores = []
        for nome, mat in trabalhadores_data:
            t, _ = TrabalhadorPortuario.objects.get_or_create(matricula=mat, defaults={'nome_completo': nome})
            trabalhadores.append(t)
        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(trabalhadores)} trabalhadores'))

        # 7. SETORES
        self.stdout.write('[7/7] Verificando Setores...')
        patio = Setor.objects.filter(setor_pai__isnull=True).first()
        if not patio:
            patio = Setor.objects.create(codigo='PAT-MODELO', nome='Pátio Modelo', capacidade_metragem=4815.08)
        subpatios = list(Setor.objects.filter(setor_pai=patio))
        if not subpatios:
            for i in range(1, 13):
                Setor.objects.create(codigo=f'P{i}', nome=f'P{i}', setor_pai=patio, capacidade_metragem=400.00)
            subpatios = list(Setor.objects.filter(setor_pai=patio))
        subpatios.sort(key=lambda x: int(''.join(filter(str.isdigit, x.codigo))) if any(c.isdigit() for c in x.codigo) else 999)
        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(subpatios)} subpátios'))

        # ============================================================
        # SIMULAÇÃO DE MANIFESTOS
        # ============================================================
        num_manifestos = options['manifestos']
        cmin = options['chassis_min']
        cmax = options['chassis_max']

        preferidas = ['ATRACADO', 'FUNDEADO', 'CARREGANDO', 'DESCARREGANDO']
        viagens_alvo = [v for v in viagens_map if v.status in preferidas]
        if len(viagens_alvo) < num_manifestos:
            viagens_alvo += [v for v in viagens_map if v.status == 'FINALIZADO']
        viagens_alvo = viagens_alvo[:num_manifestos]

        self.stdout.write(self.style.MIGRATE_HEADING(f'\n=== SIMULANDO {len(viagens_alvo)} MANIFESTOS ===\n'))

        chassi_seq = Carga.objects.count() + 1
        total_cargas = 0
        total_mov = 0
        agora = timezone.now()

        for idx, viagem in enumerate(viagens_alvo, start=1):
            metragem_atual = sum(
                float(c.metragem_unitaria)
                for c in Carga.objects.filter(setor_atual__isnull=False)
            )
            if metragem_atual >= 4500:
                self.stdout.write(self.style.WARNING(f'    ⚠ Pátio lotado. Parando.'))
                break

            operador = viagem.operador_portuario or random.choice(list(operadores_map.values()))
            fiel = random.choice(fieis)

            self.stdout.write(f'\n[{idx}/{len(viagens_alvo)}] {viagem.navio.nome} — {viagem.numero_viagem} ({viagem.status})')

            base_data = viagem.data_chegada_real or viagem.data_prevista_chegada or hoje
            base_dt = timezone.make_aware(datetime.combine(base_data, datetime.min.time())) + timedelta(hours=random.randint(6, 18))

            if base_dt > agora:
                base_dt = agora - timedelta(days=random.randint(5, 20))

            if random.random() < 0.15:
                data_est = (base_dt - timedelta(days=random.randint(2, 10))).date()
            else:
                data_est = hoje + timedelta(days=random.randint(15, 45))

            manifesto, _ = Manifesto.objects.get_or_create(
                viagem=viagem,
                defaults={
                    'operador': operador,
                    'dono_carga': fiel,
                    'numero_veiculos': 0,
                    'metragem_total': 0,
                    'status': 'EM_ANDAMENTO',
                    'data_estimada_retirada': data_est,
                }
            )

            if manifesto.cargas.exists():
                self.stdout.write(self.style.WARNING(f'    → Manifesto #{manifesto.id} já tem cargas. Ajustando quantidade_prevista.'))
                total_existente = manifesto.cargas.count()
                falta_existente = max(1, int(total_existente * random.uniform(0.05, 0.25)))
                viagem.quantidade_prevista = total_existente + falta_existente
                viagem.save(update_fields=['quantidade_prevista'])
                continue

            qtd_total = random.randint(cmin, cmax)
            itens = []
            restante = qtd_total
            while restante > 0:
                mod = random.choice(modelos)
                q = min(restante, random.randint(3, 6))
                itens.append((mod, q))
                restante -= q

            bl = f"BL-{viagem.numero_viagem[-4:]}" if len(viagem.numero_viagem) >= 4 else f"BL-{viagem.numero_viagem}"

            total_metragem_man = 0
            total_veiculos_man = 0
            cargas_criadas = []

            for mod, qtd in itens:
                chassis_lista = []
                for _ in range(qtd):
                    chassi = gerar_chassi(mod.fabricante, chassi_seq)
                    while Carga.objects.filter(chassi=chassi).exists():
                        chassi_seq += 1
                        chassi = gerar_chassi(mod.fabricante, chassi_seq)
                    chassi_seq += 1

                    carga = Carga.objects.create(
                        bl=bl, chassi=chassi, manifesto=manifesto,
                        operador=operador, dono=fiel, modelo=mod,
                        metragem_unitaria=mod.metragem_m2,
                    )
                    cargas_criadas.append(carga)
                    chassis_lista.append(chassi)
                    total_metragem_man += float(mod.metragem_m2)
                    total_veiculos_man += 1

                ItemManifesto.objects.create(
                    manifesto=manifesto, modelo=mod, quantidade=qtd,
                    lista_chassis="\n".join(chassis_lista),
                )

            manifesto.numero_veiculos = total_veiculos_man
            manifesto.metragem_total = round(total_metragem_man, 2)
            manifesto.save()

            sorteio = random.random()
            if sorteio < 0.60:
                viagem.quantidade_prevista = total_veiculos_man
            elif sorteio < 0.90:
                falta = max(1, int(total_veiculos_man * random.uniform(0.05, 0.25)))
                viagem.quantidade_prevista = total_veiculos_man + falta
            else:
                viagem.quantidade_prevista = max(1, total_veiculos_man - random.randint(3, 10))
            viagem.save(update_fields=['quantidade_prevista'])

            self.stdout.write(self.style.SUCCESS(
                f'    → Manifesto #{manifesto.id}: {total_veiculos_man} cadastrados, '
                f'{viagem.quantidade_prevista} previstos'
            ))
            total_cargas += total_veiculos_man

            # ----- MOVIMENTAÇÕES COM DATAS RECENTES -----
            for carga in cargas_criadas:
                destino = random.choice(subpatios)
                trab = random.choice(trabalhadores)
                
                # Força a chegada a ser entre 10 e 12 dias atrás
                dt_chegada = agora - timedelta(days=random.randint(10, 12), hours=random.randint(1, 24))
                lat, lng = gerar_coordenada()

                try:
                    criar_movimentacao_com_data(
                        carga=carga, tipo='CHEGADA',
                        setor_origem=None, setor_destino=destino,
                        trabalhador=trab,
                        data_hora_alvo=dt_chegada,
                        localizacao_destino=f"Berço {viagem.bercario_atracacao or '-'}",
                        latitude_destino=lat,
                        longitude_destino=lng,
                    )
                    total_mov += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Erro CHEGADA: {e}'))

            for carga in cargas_criadas:
                if random.random() < 0.40:
                    atual = carga.setor_atual
                    if not atual:
                        continue
                    candidatos = [s for s in subpatios if s != atual] or subpatios
                    novo = random.choice(candidatos)
                    trab = random.choice(trabalhadores)
                    
                    # Força a interna a ser entre 5 e 8 dias atrás
                    dt_interna = agora - timedelta(days=random.randint(5, 8), hours=random.randint(0, 12))
                    
                    lat, lng = gerar_coordenada()
                    try:
                        criar_movimentacao_com_data(
                            carga=carga, tipo='INTERNA',
                            setor_origem=atual, setor_destino=novo,
                            trabalhador=trab,
                            data_hora_alvo=dt_interna,
                            latitude_destino=lat,
                            longitude_destino=lng,
                        )
                        total_mov += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    Erro INTERNA: {e}'))

            for carga in cargas_criadas:
                if random.random() < 0.30: # 30% chance de ter saido
                    atual = carga.setor_atual
                    if not atual:
                        continue
                    trab = random.choice(trabalhadores)
                    
                    # Força a saída a ser entre 1 e 4 dias atrás (para o gráfico)
                    dt_saida = agora - timedelta(days=random.randint(1, 4), hours=random.randint(0, 20))
                    
                    try:
                        criar_movimentacao_com_data(
                            carga=carga, tipo='SAIDA',
                            setor_origem=atual, setor_destino=None,
                            trabalhador=trab,
                            data_hora_alvo=dt_saida,
                        )
                        total_mov += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    Erro SAIDA: {e}'))

            self.stdout.write(self.style.SUCCESS(f'    → Movimentações acumuladas: {total_mov}'))

        # ============================================================
        # AJUSTE FINAL: viagens SEM manifesto e previsões futuras
        # ============================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== AJUSTE FINAL ===\n'))
        
        # Força 5 viagens para o status "Aguardando Chegada" para popular o Card
        viagens_para_previsao = list(Viagem.objects.all().order_by('?')[:5])
        for v in viagens_para_previsao:
            v.status = 'AGUARDANDO_CHEGADA'
            v.data_prevista_chegada = hoje + timedelta(days=random.randint(2, 15))
            v.quantidade_prevista = random.randint(150, 350)
            v.save()

        viagens_sem_manifesto = Viagem.objects.filter(manifestos__isnull=True)
        for v in viagens_sem_manifesto:
            if not v.quantidade_prevista or v.quantidade_prevista == 0:
                v.quantidade_prevista = random.randint(50, 200)
                v.save(update_fields=['quantidade_prevista'])
        self.stdout.write(self.style.SUCCESS(f'    ✓ {viagens_sem_manifesto.count()} viagens sem manifesto ajustadas'))

        self._resumo(total_cargas, total_mov)

    def _resumo(self, novas_cargas=0, novas_mov=0):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== SEED CONCLUÍDO ===\n'))
        self.stdout.write(self.style.SUCCESS(f'  Operadores: {OperadorPortuario.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Navios: {Navio.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Viagens: {Viagem.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Fieis: {FielDepositario.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Modelos: {ModeloVeiculo.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Trabalhadores: {TrabalhadorPortuario.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Setores: {Setor.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Manifestos: {Manifesto.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Cargas: {Carga.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Movimentações: {Movimentacao.objects.count()}'))
        self.stdout.write('')