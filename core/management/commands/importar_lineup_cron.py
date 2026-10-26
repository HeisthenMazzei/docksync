from django.core.management.base import BaseCommand
from navios.models import Navio, Viagem
import pandas as pd
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Importa automaticamente o Lineup.xlsx da pasta /app/lineup/'

    def handle(self, *args, **kwargs):
        # Caminho onde o arquivo deve estar
        pasta = '/app/lineup/'
        arquivo_path = os.path.join(pasta, 'Lineup.xlsx')

        if not os.path.exists(arquivo_path):
            self.stdout.write(self.style.ERROR(f"Arquivo não encontrado em {arquivo_path}"))
            return

        try:
            df = pd.read_excel(arquivo_path, header=0)
            
            # Encontrar colunas (reutilizando a lógica robusta)
            def encontrar_coluna(df, *nomes):
                for col in df.columns:
                    col_limpa = str(col).strip().lower()
                    for nome in nomes:
                        if nome.lower() in col_limpa:
                            return col
                return None

            idx_programacao = encontrar_coluna(df, 'programação', 'programacao')
            idx_berco = encontrar_coluna(df, 'berço', 'berco')
            idx_navio = encontrar_coluna(df, 'navio')
            idx_psp = encontrar_coluna(df, 'psp')
            idx_eta = encontrar_coluna(df, 'fundeio', 'eta')
            idx_etb = encontrar_coluna(df, 'atracação', 'etb')
            idx_ets = encontrar_coluna(df, 'desatracação', 'ets')
            idx_agencia = encontrar_coluna(df, 'agência', 'agencia')

            criados = 0
            atualizados = 0

            for index, row in df.iterrows():
                try:
                    def limpar_valor(valor):
                        if pd.isna(valor):
                            return ''
                        return str(valor).strip()

                    navio_nome = limpar_valor(row.get(idx_navio)) if idx_navio else ''
                    if not navio_nome:
                        continue

                    programacao = limpar_valor(row.get(idx_programacao)) if idx_programacao else ''
                    berco = limpar_valor(row.get(idx_berco)) if idx_berco else ''
                    psp = limpar_valor(row.get(idx_psp)) if idx_psp else ''
                    agencia = limpar_valor(row.get(idx_agencia)) if idx_agencia else ''

                    # Converter datas
                    def converter_data(valor):
                        if pd.isna(valor) or str(valor).strip() == '':
                            return None
                        try:
                            if hasattr(valor, 'to_pydatetime'):
                                return valor.to_pydatetime().date()
                            if isinstance(valor, datetime):
                                return valor.date()
                            text = str(valor).strip()
                            for fmt in ['%d/%m/%Y', '%d/%m/%Y %H:%M', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']:
                                try:
                                    return datetime.strptime(text.split(' ')[0], fmt).date()
                                except ValueError:
                                    continue
                        except:
                            pass
                        return None

                    data_eta = converter_data(row.get(idx_eta)) if idx_eta else None
                    data_etb = converter_data(row.get(idx_etb)) if idx_etb else None
                    data_ets = converter_data(row.get(idx_ets)) if idx_ets else None

                    navio, _ = Navio.objects.get_or_create(nome=navio_nome)

                    viagem, criado = Viagem.objects.update_or_create(
                        navio=navio,
                        numero_viagem=programacao,
                        defaults={
                            'psp': psp,
                            'data_prevista_chegada': data_eta,
                            'data_chegada_real': data_etb,
                            'data_desatracacao': data_ets,
                            'bercario_atracacao': berco,
                            'agencia': agencia,
                        }
                    )

                    if criado:
                        criados += 1
                    else:
                        atualizados += 1

                except Exception:
                    continue

            self.stdout.write(self.style.SUCCESS(f"Importação automática concluída: {criados} criados, {atualizados} atualizados."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar: {str(e)}"))