from django.core.management.base import BaseCommand
from navios.models import Navio, Viagem
from datetime import datetime

# Dados extraídos da sua planilha Lineup.xls
LINEUP_DATA = [
    {"programacao": "2026038138", "berco": "101", "navio": "CHIPOLBROK MOON", "eta": "18/08/2026 01:00", "etb": "18/08/2026 03:10", "agencia": "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"},
    {"programacao": "515", "berco": "909", "navio": "PARCEL DE MANUEL LUÍS (REB)", "eta": "20/08/2026 11:00", "etb": "20/08/2026 13:02", "agencia": "ESVIX SHIPPING AGENCIA MARITIMA LTDA - ME"},
    {"programacao": "2026039313", "berco": "207", "navio": "BRILLANTE", "eta": "20/08/2026 16:00", "etb": "24/08/2026 06:35", "agencia": "Rochamar Agência Maritima S/A"},
    {"programacao": "2026035996", "berco": "201", "navio": "DAHLIA", "eta": "21/08/2026 01:00", "etb": "24/08/2026 08:20", "agencia": "HMS BRASIL AGENCIAMENTOS MARITIMOS LTDA"},
    {"programacao": "2026039672", "berco": "103", "navio": "SAPURA ONIX", "eta": "23/08/2026 00:00", "etb": "23/08/2026 19:30", "agencia": "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"},
    {"programacao": "2026038376", "berco": "203", "navio": "COSCO SHIPPING XING WANG", "eta": "23/08/2026 01:00", "etb": "23/08/2026 03:10", "agencia": "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."},
    {"programacao": "506", "berco": "102", "navio": "CRUZEIRO DO SUL H38", "eta": "23/08/2026 08:00", "etb": "23/08/2026 15:40", "agencia": "MARINHA DE GUERRA"},
    {"programacao": "2026039956", "berco": "501", "navio": "WINNIPEG", "eta": "23/08/2026 08:00", "etb": "23/08/2026 16:30", "agencia": "LACHMANN AGENCIA MARITIMA LTDA"},
    {"programacao": "507", "berco": "102", "navio": "DRS DEEP SEA", "eta": "23/08/2026 08:30", "etb": "23/08/2026 15:45", "agencia": "MARINHA DE GUERRA"},
    {"programacao": "2026039470", "berco": "204", "navio": "LOG-IN PANTANAL (REB)", "eta": "23/08/2026 11:00", "etb": "23/08/2026 15:00", "agencia": "MSC MEDITERRANEAN SHIPPING DO BRASIL LTDA"},
    {"programacao": "2026035490", "berco": "201", "navio": "EC TURAN", "eta": "08/08/2026 08:00", "etb": "26/08/2026 11:42", "agencia": "WILSON SONS SHIPPING SERVICES LTDA"},
    {"programacao": "2026038757", "berco": "101", "navio": "CHIPOL TAIHU", "eta": "14/08/2026 11:02", "etb": "26/08/2026 20:31", "agencia": "ORION RODOS MARITIMA E PORTUÁRIA LTDA"},
    {"programacao": "2026040075", "berco": "101", "navio": "WATERBUCK (REB)", "eta": "25/08/2026 06:00", "etb": "25/08/2026 14:21", "agencia": "PROAMAR SERVIÇOS DE DESPACHOS MARÍTIMOS LTDA"},
    {"programacao": "2026040079", "berco": "101", "navio": "WATERBUCK (REB)", "eta": "29/08/2026 08:00", "etb": "29/08/2026 08:01", "agencia": "PROAMAR SERVIÇOS DE DESPACHOS MARÍTIMOS LTDA"},
    {"programacao": "2026040089", "berco": "101", "navio": "WATERBUCK (REB)", "eta": "03/09/2026 08:00", "etb": "03/09/2026 08:01", "agencia": "PROAMAR SERVIÇOS DE DESPACHOS MARÍTIMOS LTDA"},
    {"programacao": "2026040147", "berco": "201", "navio": "AAL HOUSTON", "eta": "27/08/2026 19:00", "etb": "27/08/2026 20:00", "agencia": "WILHELMSEN PORT SERVICES BRASIL LTDA"},
    {"programacao": "2026038679", "berco": "201", "navio": "SANTAMARIA", "eta": "05/09/2026 07:00", "etb": "05/09/2026 08:00", "agencia": "ORION RODOS MARITIMA E PORTUÁRIA LTDA"},
    {"programacao": "2026037503", "berco": "202", "navio": "SPAR ELECTRA", "eta": "25/08/2026 07:00", "etb": "25/08/2026 08:42", "agencia": "LBH BRASIL AGENCIAMENTO MARÍTIMO LTDA"},
    {"programacao": "2026037718", "berco": "202", "navio": "BAHRI ABHA", "eta": "28/08/2026 22:00", "etb": "31/08/2026 13:47", "agencia": "GAC LOGISTICA DO BRASIL LTDA"},
    {"programacao": "2026036990", "berco": "202", "navio": "GRANDE AMBURGO", "eta": "28/08/2026 19:00", "etb": "31/08/2026 00:17", "agencia": "LACHMANN AGENCIA MARITIMA LTDA"},
    {"programacao": "2026038976", "berco": "202", "navio": "MICHIGAN HIGHWAY", "eta": "29/08/2026 01:00", "etb": "01/09/2026 09:32", "agencia": "UNIMAR AGENCIAMENTOS MARITIMOS LTDA"},
    {"programacao": "2026039995", "berco": "202", "navio": "MIRACULOUS ACE", "eta": "29/08/2026 00:00", "etb": "01/09/2026 19:56", "agencia": "Rochamar Agência Maritima S/A"},
    {"programacao": "2026040419", "berco": "202", "navio": "PACIFIC VIRTUE", "eta": "04/09/2026 21:00", "etb": "04/09/2026 22:00", "agencia": "WILHELMSEN PORT SERVICES BRASIL LTDA"},
    {"programacao": "2026040412", "berco": "204", "navio": "MSC RUTH F", "eta": "27/08/2026 19:00", "etb": "27/08/2026 19:01", "agencia": "MSC MEDITERRANEAN SHIPPING DO BRASIL LTDA 02.378.779/0009-66"},
    {"programacao": "2026039458", "berco": "204", "navio": "LOG-IN DISCOVERY (REB S/L)", "eta": "27/08/2026 07:00", "etb": "27/08/2026 08:00", "agencia": "MSC MEDITERRANEAN SHIPPING DO BRASIL LTDA 02.378.779/0009-66"},
    {"programacao": "2026038200", "berco": "206", "navio": "DA XIN", "eta": "30/08/2026 00:00", "etb": "30/08/2026 01:00", "agencia": "TRANSHIPPING AGENCIAMENTO MARITIMO LTDA."},
    {"programacao": "2026038792", "berco": "207", "navio": "NOCC ATLANTIC", "eta": "03/09/2026 23:59", "etb": "06/09/2026 14:59", "agencia": "WILHELMSEN PORT SERVICES BRASIL LTDA"},
    {"programacao": "2026037019", "berco": "207", "navio": "GRANDE SAN PAOLO", "eta": "09/09/2026 06:00", "etb": "09/09/2026 07:00", "agencia": "LACHMANN AGENCIA MARITIMA LTDA"},
    {"programacao": "2026039675", "berco": "207", "navio": "MAERSK KATALIN", "eta": "29/08/2026 12:00", "etb": "01/09/2026 16:06", "agencia": "LACHMANN AGENCIA MARITIMA LTDA"},
    {"programacao": "2026039317", "berco": "207", "navio": "BOW EXPLORER", "eta": "27/08/2026 12:00", "etb": "27/08/2026 13:00", "agencia": "Rochamar Agência Maritima S/A"},
    {"programacao": "2026039996", "berco": "207", "navio": "BOSPORUS HIGHWAY", "eta": "04/09/2026 06:00", "etb": "07/09/2026 15:58", "agencia": "UNIMAR AGENCIAMENTOS MARITIMOS LTDA"},
    {"programacao": "2026040259", "berco": "501", "navio": "HORIZON THETIS", "eta": "24/08/2026 20:00", "etb": "25/08/2026 05:30", "agencia": "LACHMANN AGENCIA MARITIMA LTDA"},
    {"programacao": "2026038846", "berco": "905", "navio": "ISABELLA M II", "eta": "26/08/2026 00:00", "etb": "26/08/2026 00:01", "agencia": "LACHMANN AGENCIA MARITIMA LTDA"},
    {"programacao": "2026040374", "berco": "906", "navio": "SEAGEMS RUBI", "eta": "24/08/2026 16:00", "etb": "24/08/2026 16:30", "agencia": "LOTUS AGENCIA MARITIMA E OPERADORA PORTUARIA LTDA"},
]

class Command(BaseCommand):
    help = 'Importa dados de programações (Lineup) para Navios e Viagens.'

    def handle(self, *args, **kwargs):
        criados = 0
        atualizados = 0

        for item in LINEUP_DATA:
            # Converte a data/hora para datetime (ignora o horário)
            data_eta = datetime.strptime(item['eta'], '%d/%m/%Y %H:%M').date() if item['eta'] else None
            data_etb = datetime.strptime(item['etb'], '%d/%m/%Y %H:%M').date() if item['etb'] else None

            # Cria ou pega o navio
            navio, _ = Navio.objects.get_or_create(nome=item['navio'])

            # Cria ou atualiza a viagem (considerando navio + numero_viagem únicos)
            viagem, criado = Viagem.objects.update_or_create(
                navio=navio,
                numero_viagem=item['programacao'],
                defaults={
                    'data_prevista_chegada': data_eta,
                    'data_chegada_real': data_etb,
                    'bercario_atracacao': item['berco'],
                    'agencia': item['agencia'],
                }
            )
            if criado:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(f"Importação concluída! {criados} viagens criadas, {atualizados} atualizadas."))