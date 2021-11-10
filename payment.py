# This file is part of payment_collect_visa module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import time
import logging
from decimal import Decimal

from trytond.model import ModelStorage
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.modules.payment_collect.payments import PaymentMixIn

logger = logging.getLogger(__name__)


class PayModeVisa(ModelStorage, PaymentMixIn):
    'Pay Mode Visa'
    __name__ = 'payment.paymode.visa'

    def generate_collect(self, start):
        logger.info("generate_collect: visa")
        pool = Pool()
        Configuration = pool.get('payment_collect.configuration')
        Company = pool.get('company.company')
        Invoice = pool.get('account.invoice')
        Currency = pool.get('currency.currency')
        Attachment = pool.get('ir.attachment')

        config = Configuration(1)
        if config.visa_company_code:
            company_code = config.visa_company_code
        else:
            raise UserError(gettext(
                'payment_collect_visa.msg_missing_company_code'))
        company = Company(Transaction().context.get('company'))
        today = (Transaction().context.get('date') or
            pool.get('ir.date').today())

        self.cantidad_registros = 0
        self.monto_total = Decimal('0')
        csv_format = start.csv_format
        format_number = self.get_format_number()

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
            self.fecha_vencimiento = start.expiration_date.strftime('%Y%m%d')
            self.constate2 = '0005'
            self.amount = Currency.round(invoice.currency,
                invoice.amount_to_pay)
            self.importe = self._formatear_importe(self.amount, 15)
            self.identificador_debito = invoice.party.code.rjust(15, '0')
            self.codigo_alta_identificador = 'E' or ' '
            self.estado_registro = '  '
            self.reservado = ' '.ljust(26)
            self.marca_fin = '*'

            self.res.append(self.a_texto(csv_format))

            self.cantidad_registros = self.cantidad_registros + 1
            self.monto_total = Currency.round(invoice.currency,
                self.monto_total + self.amount)

        self.visa_pie(company_code, today)
        self.res.append(self.a_texto_pie(csv_format))

        self.type = 'send'
        self.filename = 'DEBLIQC.txt'
        self.periods = start.periods
        collect = self.attach_collect()

        remito_info = """
        Nombre Empresa: %s
        Fecha de Vto: %s, Cant. Ditos: %s, Importe Total: %s""" % (
            company.party.name, start.expiration_date.strftime('%d/%m/%Y'),
            self.cantidad_registros, format_number(self.monto_total))
        remito = Attachment()
        remito.name = 'REMITO.txt'
        remito.resource = collect
        remito.data = remito_info.encode('utf8')
        remito.save()

        return [collect]

    def _formatear_importe(self, importe, digitos):
        return importe.to_eng_string().replace('.', '').rjust(digitos, '0')

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
        super().return_collect(start, {})
        pool = Pool()
        Configuration = pool.get('payment_collect.configuration')
        Invoice = pool.get('account.invoice')

        self.validate_return_file(self.return_file)

        config = Configuration(1)
        payment_method = None
        if config.payment_method_visa:
            payment_method = config.payment_method_visa

        pay_date = pool.get('ir.date').today()

        domain = self.get_domain(start.periods)
        domain.append(('paymode.type', '=', self.__name__))
        order = self.get_order()
        for line in self.return_file.decode('utf-8').splitlines():
            if line[0] != '1':
                continue
            invoice_domain = self.get_invoice_domain(line)
            invoice = Invoice.search(domain + invoice_domain,
                order=order, limit=1)
            if not invoice:
                continue
            pay_amount = invoice[0].amount_to_pay
            if line[129] == '0':
                transaction = self.message_invoice(invoice, 'A',
                    'Movimiento Aceptado', pay_amount, pay_date,
                    payment_method=payment_method)
            else:
                transaction = self.message_invoice(invoice, 'R',
                    'Movimiento Rechazado', pay_amount,
                    payment_method=payment_method)
            transaction.collect = self.collect
            transaction.save()

        self.filename = 'visa-return-%s' % pay_date.strftime("%Y-%m-%d")
        collect = self.attach_collect()
        return [collect]

    @classmethod
    def validate_return_file(cls, return_file):
        if not return_file:
            raise UserError(gettext('payment_collect.msg_return_file_empty'))

    @classmethod
    def get_invoice_domain(cls, line):
        party_code = line[98:109].lstrip('0')
        domain = [
            ('party.code', '=', party_code),
            ]
        return domain
