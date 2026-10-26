"""
Serviços de importação de cargas para manifestos.
"""
import re
import pandas as pd
from pypdf import PdfReader
from django.db import transaction

from cargas.models import Carga, ModeloVeiculo


# ============================================================
# FORMATO DO CHASSI PROVISÓRIO
# Padrão: {numero_viagem}-{abreviado}-{ano}-{seq:03d}
# Exemplo: 2026044850-HAVALH9-2026-001
# ============================================================
CHASSI_PROVISORIO_REGEX = re.compile(r'^[A-Z0-9]+-[A-Z0-9]+-\d{4}-\d{3}$')

# Regex para VIN padrão (17 caracteres, sem I, O, Q)
VIN_REGEX = re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b')


def validar_chassi(chassi):
    if not chassi:
        return False
    chassi = str(chassi).strip().upper()
    if len(chassi) < 10 or len(chassi) > 50:
        return False
    if not re.match(r'^[A-Z0-9\-]+$', chassi):
        return False
    return True


def limpar_chassi(chassi):
    if not chassi:
        return ''
    return str(chassi).strip().upper().replace(' ', '')


# ============================================================
# IMPORTAÇÃO DE LISTA (5.1)
# ============================================================
def parsear_lista_chassis(arquivo):
    chassis = []
    erros = []
    nome = arquivo.name.lower()

    try:
        if nome.endswith('.xlsx') or nome.endswith('.xls'):
            df = pd.read_excel(arquivo, header=None)
            for valor in df.iloc[:, 0].dropna().astype(str):
                chassi = limpar_chassi(valor)
                if chassi and not chassi.lower().startswith(('chassi', 'vin', 'nº')):
                    chassis.append(chassi)
        else:
            conteudo = arquivo.read()
            if isinstance(conteudo, bytes):
                try:
                    conteudo = conteudo.decode('utf-8')
                except UnicodeDecodeError:
                    conteudo = conteudo.decode('latin-1')

            conteudo = conteudo.replace(',', '\n').replace(';', '\n').replace('\t', '\n')

            for linha in conteudo.splitlines():
                chassi = limpar_chassi(linha)
                if not chassi:
                    continue
                if chassi.lower() in ('chassi', 'vin', 'chassis', 'chassi/vin'):
                    continue
                chassis.append(chassi)
    except Exception as e:
        erros.append(f"Erro ao ler arquivo: {e}")
        return [], erros

    chassis_validos = []
    chassis_vistos = set()
    for c in chassis:
        if c in chassis_vistos:
            erros.append(f"Chassi duplicado na lista: {c}")
            continue
        if not validar_chassi(c):
            erros.append(f"Chassi inválido (ignorado): {c}")
            continue
        chassis_vistos.add(c)
        chassis_validos.append(c)

    return chassis_validos, erros


def importar_chassis_em_manifesto(manifesto, arquivo):
    resultado = {'criados': 0, 'duplicados': [], 'invalidos': [], 'erros': []}
    chassis, erros = parsear_lista_chassis(arquivo)
    resultado['erros'] = erros

    chassis_existentes = set(
        Carga.objects.filter(chassi__in=chassis).values_list('chassi', flat=True)
    )

    for chassi in chassis:
        if chassi in chassis_existentes:
            resultado['duplicados'].append(chassi)
            continue
        try:
            Carga.objects.create(
                bl=None, chassi=chassi, manifesto=manifesto,
                operador=manifesto.operador, dono=manifesto.dono_carga,
                modelo=None, metragem_unitaria=0,
                origem=Carga.Origem.LISTA, provisorio=False,
            )
            resultado['criados'] += 1
        except Exception as e:
            resultado['erros'].append(f"Erro ao criar {chassi}: {e}")

    total_cargas = manifesto.cargas.count()
    manifesto.numero_veiculos = total_cargas
    manifesto.save(update_fields=['numero_veiculos'])

    return resultado


# ============================================================
# CHASSI PROVISÓRIO
# ============================================================
def gerar_chassi_provisorio(numero_viagem, modelo_abreviado, ano, sequencial):
    abreviado_limpo = re.sub(r'[^A-Z0-9]', '', str(modelo_abreviado).upper())[:20]
    numero_viagem_limpo = re.sub(r'[^A-Z0-9]', '', str(numero_viagem).upper())[:20]
    ano_str = str(ano)[:4] if ano else '0000'
    seq_str = f"{sequencial:03d}"
    return f"{numero_viagem_limpo}-{abreviado_limpo}-{ano_str}-{seq_str}"


def criar_chassis_provisorios(manifesto, modelo, quantidade):
    criados = []
    viagem = manifesto.viagem
    abreviado = modelo.abreviado or modelo.modelo or 'MODELO'
    ano = modelo.ano or 0

    prefixo = f"{viagem.numero_viagem}-{re.sub(r'[^A-Z0-9]', '', abreviado.upper())[:20]}-{ano}-"
    ultimo = Carga.objects.filter(chassi__startswith=prefixo).order_by('-chassi').first()

    if ultimo:
        try:
            seq_inicial = int(ultimo.chassi.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq_inicial = 1
    else:
        seq_inicial = 1

    for i in range(quantidade):
        chassi = gerar_chassi_provisorio(
            numero_viagem=viagem.numero_viagem,
            modelo_abreviado=abreviado,
            ano=ano,
            sequencial=seq_inicial + i,
        )
        try:
            carga = Carga.objects.create(
                bl=None, chassi=chassi, manifesto=manifesto,
                operador=manifesto.operador, dono=manifesto.dono_carga,
                modelo=modelo, metragem_unitaria=modelo.metragem_m2 or 0,
                origem=Carga.Origem.PDF, provisorio=True,
            )
            criados.append(carga)
        except Exception:
            continue

    total_cargas = manifesto.cargas.count()
    total_metragem = sum(float(c.metragem_unitaria or 0) for c in manifesto.cargas.all())
    manifesto.numero_veiculos = total_cargas
    manifesto.metragem_total = round(total_metragem, 2)
    manifesto.save(update_fields=['numero_veiculos', 'metragem_total'])

    return criados


# ============================================================
# LEITURA DE PDF (5.2)
# ============================================================
def extrair_texto_pdf(arquivo):
    try:
        reader = PdfReader(arquivo)
        texto_completo = []
        for page in reader.pages:
            texto_completo.append(page.extract_text() or '')
        return "\n".join(texto_completo)
    except Exception as e:
        return f"ERRO_AO_LER_PDF: {e}"


def extrair_chassis_de_texto(texto):
    if not texto:
        return []
    texto_upper = texto.upper()
    matches = VIN_REGEX.findall(texto_upper)
    vistos = set()
    resultado = []
    for m in matches:
        if m not in vistos:
            vistos.add(m)
            resultado.append(m)
    return resultado


def extrair_dados_do_pdf(arquivo):
    texto = extrair_texto_pdf(arquivo)

    if texto.startswith('ERRO_AO_LER_PDF'):
        return {
            'sucesso': False,
            'erro': texto.replace('ERRO_AO_LER_PDF: ', ''),
            'texto': '',
            'chassis': [],
            'quantidade_detectada': 0,
            'tem_vin_list': False,
        }

    chassis = extrair_chassis_de_texto(texto)

    quantidade = 0
    m = re.search(r'(\d{1,4})\s*(UNITS|PACKAGES|VEHICLES)', texto.upper())
    if m:
        quantidade = int(m.group(1))

    return {
        'sucesso': True,
        'erro': None,
        'texto': texto[:5000],
        'chassis': chassis,
        'quantidade_detectada': quantidade,
        'tem_vin_list': 'VIN LIST' in texto.upper() or 'VEHICLES VIN' in texto.upper(),
    }


# ============================================================
# EDIÇÃO EM MASSA DE CHASSIS PROVISÓRIOS (5.3)
# ============================================================
def listar_chassis_provisorios(manifesto=None):
    """Lista chassis provisórios, opcionalmente filtrado por manifesto."""
    qs = Carga.objects.filter(provisorio=True).select_related(
        'manifesto', 'manifesto__viagem__navio', 'modelo'
    )
    if manifesto:
        qs = qs.filter(manifesto=manifesto)
    return qs.order_by('manifesto_id', 'chassi')


def atualizar_chassis_em_lote(chassis_dict):
    """
    Recebe um dict {carga_id: novo_chassi} e atualiza em lote.
    Retorna dict com resultado.
    """
    resultado = {
        'atualizados': 0,
        'erros': [],
        'vazios': 0,
        'iguais': 0,
    }

    with transaction.atomic():
        for carga_id, novo_chassi in chassis_dict.items():
            novo_chassi = limpar_chassi(novo_chassi)

            if not novo_chassi:
                resultado['vazios'] += 1
                continue

            try:
                carga = Carga.objects.get(pk=carga_id)
            except Carga.DoesNotExist:
                resultado['erros'].append(f"Carga #{carga_id} não encontrada.")
                continue

            if novo_chassi == carga.chassi:
                resultado['iguais'] += 1
                continue

            if not validar_chassi(novo_chassi):
                resultado['erros'].append(f"Chassi inválido (não salvo): {novo_chassi}")
                continue

            if Carga.objects.filter(chassi=novo_chassi).exclude(pk=carga.id).exists():
                resultado['erros'].append(f"Chassi {novo_chassi} já existe em outra carga.")
                continue

            carga.chassi = novo_chassi
            carga.provisorio = False
            carga.origem = Carga.Origem.MANUAL
            carga.save(update_fields=['chassi', 'provisorio', 'origem'])
            resultado['atualizados'] += 1

    return resultado