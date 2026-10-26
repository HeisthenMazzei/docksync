from django.core.management.base import BaseCommand
from cargas.models import OperadorPortuario
import pandas as pd
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Atualiza os operadores portuários a partir do arquivo Excel (RelacaoOP.xlsx)'

    def handle(self, *args, **kwargs):
        # Caminho padrão onde o arquivo deve estar (pasta lineup montada no Docker)
        caminho_arquivo = '/app/lineup/RelacaoOP.xlsx'

        if not os.path.exists(caminho_arquivo):
            self.stdout.write(self.style.ERROR(f"Arquivo não encontrado em {caminho_arquivo}. Coloque o arquivo RelacaoOP.xlsx na pasta 'lineup' na raiz do seu projeto."))
            return

        try:
            df = pd.read_excel(caminho_arquivo, header=0)
            criados = 0
            atualizados = 0

            for index, row in df.iterrows():
                try:
                    nome = str(row.get('Nome Empresa', '')).strip()
                    cnpj = str(row.get('CNPJ', '')).strip()
                    telefone = str(row.get('Telefone', '')).strip()
                    responsavel = str(row.get('Responsável Técnico', row.get('Responsavel Tecnico', ''))).strip()
                    numero = str(row.get('Número', row.get('Numero', ''))).strip()
                    data_validade = row.get('Data Validade', '')
                    situacao = str(row.get('Situação', row.get('Situacao', ''))).strip()

                    try:
                        if isinstance(data_validade, datetime):
                            data_val = data_validade.date()
                        else:
                            data_str = str(data_validade).split(' ')[0]
                            data_val = datetime.strptime(data_str, '%d/%m/%Y').date()
                    except:
                        data_val = None

                    if not nome:
                        continue

                    # Busca primeiro pelo CNPJ, depois pelo Nome
                    operador = None
                    if cnpj:
                        operador = OperadorPortuario.objects.filter(cnpj=cnpj).first()

                    if not operador:
                        operador = OperadorPortuario.objects.filter(nome_empresa=nome).first()

                    if operador:
                        operador.nome_empresa = nome
                        operador.cnpj = cnpj
                        operador.telefone = telefone
                        operador.responsavel_tecnico = responsavel
                        operador.numero_registro = numero
                        operador.data_validade = data_val
                        operador.situacao = situacao
                        operador.save()
                        atualizados += 1
                    else:
                        OperadorPortuario.objects.create(
                            nome_empresa=nome,
                            cnpj=cnpj,
                            telefone=telefone,
                            responsavel_tecnico=responsavel,
                            numero_registro=numero,
                            data_validade=data_val,
                            situacao=situacao
                        )
                        criados += 1

                except Exception as e:
                    continue

            self.stdout.write(self.style.SUCCESS(f"Processo concluído! {criados} criados, {atualizados} atualizados."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar o arquivo: {str(e)}"))