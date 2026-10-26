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
# DADOS DO LINEUP Docksync (atualizado em 20/10/2026)
# ============================================================
LINEUP_DATA = [
    ("2026041104", "202", "PRODIGY", "Aprovada", "02/10/2026 23:30", "13/10/2026 11:10", "24/10/2026 07:55", "ORION RODOS MARITIMA E PORTUÁRIA LTDA"),
    ("2026046784", "102", "SKANDI NITEROI", "Aprovada", "06/10/2026 07:00", "06/10/2026 09:35", "22/10/2026 07:00", "WILSON SONS SHIPPING SERVICES LTDA"),
    ("2026045038", "203", "GREEN TAICANG", "Aprovada", "06/10/2026 09:00", "13/10/2026 17:20", "20/10/2026 08:59", "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."),
    ("2026048156", "905", "BLUE NEPTUNE", "Aprovada", "13/10/2026 00:15", "14/10/2026 00:30", "24/10/2026 13:06", "ORION RODOS MARITIMA E PORTUÁRIA LTDA"),
    ("2026047733", "207", "ML SWALLOW", "Aprovada", "16/10/2026 08:00", "18/10/2026 17:45", "24/10/2026 23:00", "WILSON SONS SHIPPING SERVICES LTDA"),
    ("2026049405", "906", "SKANDI RECIFE", "Aprovada", "17/10/2026 00:00", "17/10/2026 08:05", "20/10/2026 08:00", "WILSON SONS SHIPPING SERVICES LTDA"),
    ("2026046732", "103", "SKANDI VITORIA", "Aprovada", "19/10/2026 11:59", "19/10/2026 13:20", "24/10/2026 07:00", "WILSON SONS SHIPPING SERVICES LTDA"),
    ("2026047667", "203", "GREEN ITAJAI", "Aprovada", "17/10/2026 18:30", "20/10/2026 09:59", "24/10/2026 11:06", "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."),
    ("2026047624", "207", "LARGO ENDEAVOR", "Incluída", "19/10/2026 09:42", "25/10/2026 00:00", "27/10/2026 09:24", "ATLANTIC AGENCIA DE NAVEGACAO LTDA ME"),
    ("2026049040", "204", "LOG-IN DISCOVERY (REB S/L)", "Aprovada", "20/10/2026 07:00", "20/10/2026 10:59", "22/10/2026 23:51", "MSC MEDITERRANEAN SHIPPING DO BRASIL LTDA 02.378.779/0009-66"),
    ("2026049073", "203", "ZHONG YUAN HAI YUN JIN QU", "Incluída", "20/10/2026 09:00", "22/10/2026 10:00", "23/10/2026 11:00", "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."),
    ("2026049890", "101", "WATERBUCK (REB)", "Incluída", "21/10/2026 07:00", "21/10/2026 08:00", "21/10/2026 19:00", "PROAMAR SERVIÇOS DE DESPACHOS MARÍTIMOS LTDA"),
    ("2026049444", "102", "TS PEREGRINO", "Incluída", "22/10/2026 06:00", "22/10/2026 07:00", "22/10/2026 08:00", "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"),
    ("2026049445", "102", "BALSA TS6", "Incluída", "22/10/2026 06:00", "22/10/2026 07:00", "23/10/2026 08:00", "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"),
    ("659", "102", "AMAZONAS", "Incluída", "22/10/2026 07:00", "22/10/2026 08:00", "26/10/2026 09:30", "MARINHA DE GUERRA"),
    ("2026044955", "201", "DAHLIA", "Incluída", "25/10/2026 08:00", "25/10/2026 09:00", "26/10/2026 20:27", "HMS BRASIL AGENCIAMENTOS MARITIMOS LTDA"),
    ("2026049513", "201", "MUROVDAG", "Incluída", "23/10/2026 13:00", "23/10/2026 14:00", "24/10/2026 07:43", "WILSON SONS SHIPPING SERVICES LTDA"),
    ("2026048558", "201", "GULLWING", "Incluída", "26/10/2026 05:00", "26/10/2026 21:27", "29/10/2026 18:18", "ORION RODOS MARITIMA E PORTUÁRIA LTDA"),
    ("2026049174", "202", "NOVA", "Incluída", "25/10/2026 12:00", "27/10/2026 17:21", "06/11/2026 13:09", "WILHELMSEN PORT SERVICES BRASIL LTDA"),
    ("2026044965", "202", "CORAL ISLAND", "Incluída", "25/10/2026 06:00", "25/10/2026 07:00", "27/10/2026 09:06", "SEATRADE OPERADORES PORTUARIOS LTDA"),
    ("2026047699", "202", "TORRENS", "Incluída", "24/10/2026 07:00", "24/10/2026 08:55", "25/10/2026 00:33", "WILHELMSEN PORT SERVICES BRASIL LTDA"),
    ("2026049948", "204", "LOG-IN JACARANDA", "Incluída", "24/10/2026 12:00", "24/10/2026 12:01", "25/10/2026 14:00", "MSC MEDITERRANEAN SHIPPING DO BRASIL LTDA"),
    ("2026045097", "207", "GRANDE AMBURGO", "Incluída", "26/10/2026 07:00", "27/10/2026 10:24", "27/10/2026 16:39", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026047736", "501", "JORGE AMADO", "Incluída", "24/10/2026 02:00", "24/10/2026 03:00", "24/10/2026 04:00", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026049402", "905", "MAERSK KATALIN", "Incluída", "21/10/2026 00:00", "24/10/2026 14:06", "29/10/2026 21:24", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("2026049869", "905", "VORIAS", "Incluída", "24/10/2026 00:00", "25/10/2026 16:06", "01/11/2026 22:21", "LACHMANN AGENCIA MARITIMA LTDA"),
    ("593", "909", "NORMAND COMMANDER", "Incluída", "25/10/2026 07:00", "25/10/2026 08:00", "25/10/2026 09:00", "SOLANA AGENCIA MARITIMA LTDA"),
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

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== SEED Docksync — Lineup Out/2026 ===\n'))

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

            # Sentido: 60% descarga (importação), 40% carga (exportação)
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

            # Se o manifesto já tem cargas, pula criação mas ajusta quantidade_prevista
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

            # AJUSTA quantidade_prevista
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

            # ----- MOVIMENTAÇÕES (com GPS) -----
            for carga in cargas_criadas:
                destino = random.choice(subpatios)
                trab = random.choice(trabalhadores)
                dt_chegada = base_dt + timedelta(minutes=random.randint(0, 180))
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
                if random.random() < 0.30:
                    atual = carga.setor_atual
                    if not atual:
                        continue
                    candidatos = [s for s in subpatios if s != atual] or subpatios
                    novo = random.choice(candidatos)
                    trab = random.choice(trabalhadores)
                    dt_interna = dt_chegada + timedelta(days=random.randint(1, 7), hours=random.randint(0, 12))
                    if dt_interna > agora:
                        dt_interna = agora - timedelta(hours=random.randint(1, 24))
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
                if random.random() < 0.12:
                    atual = carga.setor_atual
                    if not atual:
                        continue
                    trab = random.choice(trabalhadores)
                    dt_saida = dt_chegada + timedelta(days=random.randint(3, 20), hours=random.randint(0, 20))
                    if dt_saida > agora:
                        dt_saida = agora - timedelta(hours=random.randint(1, 48))
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
        # AJUSTE FINAL: viagens SEM manifesto ganham quantidade_prevista
        # ============================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== AJUSTE FINAL ===\n'))
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