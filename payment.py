# This file is part of payment_collect_visa module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import time
import logging
from decimal import Decimal
from trytond.pool import Pool
from trytond.modules.payment_collect.payments import PaymentMixIn
from trytond.model import ModelStorage
from trytond.transaction import Transaction

logger = logging.getLogger(__name__)


class PayModeVisa(ModelStorage, PaymentMixIn):
    'Pay Mode Visa'
    __name__ = 'payment.paymode.visa'

    @classmethod
    def __setup__(cls):
        super(PayModeVisa, cls).__setup__()
        cls._error_messages.update({
            'missing_company_code':
                'Debe establecer el número de comercio de VISA.',
                })

    def generate_collect(self, start):
        logger.info("generate_collect: visa")
        pool = Pool()

        Company = pool.get('company.company')
        Attachment = pool.get('ir.attachment')
        Invoice = pool.get('account.invoice')
        Currency = pool.get('currency.currency')
        Configuration = pool.get('payment_collect.configuration')
        fecha = Transaction().context.get('date')
        today = pool.get('ir.date').today()
        if fecha:
            today = fecha
        config = Configuration(1)
        if config.visa_company_code:
            company_code = config.visa_company_code
        else:
            self.raise_user_error('missing_company_code')
        self.periods = start.periods
        csv_format = start.csv_format
        self.monto_total = Decimal('0')
        self.cantidad_registros = 0
        self.type = 'send'
        self.filename = 'DEBLIQC.txt'
        format_number = self.get_format_number()
        format_date = self.get_format_date()
        domain = self.get_domain(start.periods)
        domain.append(('paymode.type', '=', start.paymode_type))
        order = self.get_order()
        invoices = Invoice.search(domain, order=order)
        self.res = []

        self.visa_cabecera(company_code, today)
        self.res.append(self.a_texto_cabecera(csv_format))

        for invoice in invoices:
            self.tipo_registro = '1'
            self.credit_card_number = invoice.paymode.credit_number.ljust(16)
            self.constate1 = ' '.ljust(3)
            self.nro_secuencial = str(self.cantidad_registros).rjust(8, '0')
            self.fecha_vencimiento = start.expiration_date.strftime("%Y%m%d")
            self.constate2 = '0005'
            self.amount = Currency.round(invoice.currency, invoice.amount_to_pay)
            self.importe = self.amount.to_eng_string().replace('.',
                '').rjust(15, '0')
            self.identificador_debito = invoice.party.code.rjust(15, '0')
            self.codigo_alta_identificador = 'E'
            self.estado_registro = '  '
            self.reservado = ' '.ljust(26)
            self.marca_fin = '*'
            self.monto_total = Currency.round(invoice.currency,
                self.monto_total + self.amount)
            self.cantidad_registros = self.cantidad_registros + 1
            self.res.append(self.a_texto(csv_format))

        self.visa_pie(company_code, today)
        self.res.append(self.a_texto_pie(csv_format))
        collect = self.attach_collect()

        company = Company(Transaction().context.get('company'))
        remito_info = """
        Nombre Empresa: %s
        Fecha de Vto: %s, Cant. Ditos: %s, Importe Total: %s
        """ % (company.party.name, format_date(start.expiration_date),
            self.cantidad_registros, format_number(self.monto_total))
        remito = Attachment()
        remito.name = 'REMITO.txt'
        remito.resource = collect
        remito.data = remito_info.encode('utf8')
        remito.save()

        return [collect]

    def a_texto_pie(self, csv_format=False):
        """ Concatena los valores de los campos de la clase y los
        devuelve en una cadena de texto.
        """
        campos = self.lista_campo_pie()
        campos = [x for x in campos if x != '']
        separador = csv_format and self._SEPARATOR or ''
        return separador.join(campos) + self._EOL

    def a_texto_cabecera(self, csv_format=False):
        """ Concatena los valores de los campos de la clase y los
        devuelve en una cadena de texto.
        """
        campos = self.lista_campo_cabecera()
        campos = [x for x in campos if x != '']
        separador = csv_format and self._SEPARATOR or ''
        return separador.join(campos) + self._EOL

    def visa_cabecera(self, company_code, today):
        self.tipo_registro = '0'
        self.constate1 = 'DEBLIQC '
        self.company_code = company_code
        self.constate2 = '900000    '
        self.fecha_hoy = today.strftime("%Y%d%m")
        self.hora = time.strftime("%H%M")
        self.tipo_archivo = '0'
        self.estado_archivo = '  '
        self.reservado = ' '.ljust(55)
        self.marca_fin = '*'

    def lista_campo_cabecera(self):
        """ Devuelve lista de campos ordenados """
        return [
            self.tipo_registro,
            self.constate1,
            self.company_code,
            self.constate2,
            self.fecha_hoy,
            self.hora,
            self.tipo_archivo,
            self.estado_archivo,
            self.reservado,
            self.marca_fin,
            ]

    def visa_pie(self, company_code, today):
        self.tipo_registro = '9'
        self.constate1 = 'DEBLIQC '
        self.company_code = company_code
        self.constate2 = '900000    '
        self.fecha_hoy = today.strftime("%Y%d%m")
        self.hora = time.strftime("%H%M")
        self.total_registros = str(self.cantidad_registros).rjust(7, '0')
        self.monto_total_registros = self.monto_total.to_eng_string().replace(
            '.', '').rjust(15, '0')
        self.reservado = ' '.ljust(36)
        self.marca_fin = '*'

    def lista_campo_pie(self):
        """ Devuelve lista de campos ordenados """
        return [
            self.tipo_registro,
            self.constate1,
            self.company_code,
            self.constate2,
            self.fecha_hoy,
            self.hora,
            self.total_registros,
            self.monto_total_registros,
            self.reservado,
            self.marca_fin,
            ]

    def lista_campo_ordenados(self):
        """ Devuelve lista de campos ordenados """
        return [
            self.tipo_registro,
            self.credit_card_number,
            self.constate1,
            self.nro_secuencial,
            self.fecha_vencimiento,
            self.constate2,
            self.importe,
            self.identificador_debito,
            self.codigo_alta_identificador,
            self.estado_registro,
            self.reservado,
            self.marca_fin,
            ]

    def return_collect(self, start):
        logger.info("return_collect: visa")
        super(PayModeVisa, self).return_collect(start, {})
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Configuration = pool.get('payment_collect.configuration')
        config = Configuration(1)
        payment_method = None
        if config.payment_method_visa:
            payment_method = config.payment_method_visa

        if not self.return_file:
            self.raise_user_error('return_file_empty')

        # Obtener numeros de invoices de self.start.return_file
        order = self.get_order()

        party_codes = []
        codigo_retorno = {}
        for line in self.return_file.decode('utf-8').splitlines():
            if line[0] == '1':
                party_code = line[98:109].lstrip('0')
                party_codes.append(party_code)
                codigo_retorno[party_code] = line[129]

        domain = self.get_domain(start.periods)
        domain.append(('paymode.type', '=', self.__name__))
        domain.append(('party.code', 'in', party_codes))
        invoices = Invoice.search(domain, order=order)
        pay_date = pool.get('ir.date').today()
        self.filename = 'visa-return-%s' % pay_date.strftime("%Y-%m-%d")

        for invoice in invoices:
            if codigo_retorno[invoice.party.code] == '0':
                transaction = self.message_invoice([invoice], 'A',
                    'Movimiento Aceptado', invoice.amount_to_pay, pay_date,
                    payment_method=payment_method)
            else:
                transaction = self.message_invoice([invoice], 'R',
                    'Movimiento Rechazado', invoice.amount_to_pay,
                    payment_method=payment_method)
            transaction.collect = self.collect
            transaction.save()
        self.attach_collect()
        return [self.collect]
