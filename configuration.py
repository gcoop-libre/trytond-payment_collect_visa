# This file is part of the payment_collect_visa module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.modules.company.model import CompanyValueMixin

__all__ = ['Configuration', 'ConfigurationPaymentCollectVISA']


class Configuration(metaclass=PoolMeta):
    __name__ = 'payment_collect.configuration'
    payment_method_visa = fields.MultiValue(fields.Many2One(
            'account.invoice.payment.method', "Payment Method VISA",
            required=True))
    visa_company_code = fields.MultiValue(fields.Char('Comany code VISA'))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'visa_company_code':
            return pool.get('payment_collect.configuration.visa')
        elif field == 'payment_method_visa':
            return pool.get('payment_collect.configuration.visa')
        return super(Configuration, cls).multivalue_model(field)


class ConfigurationPaymentCollectVISA(ModelSQL, CompanyValueMixin):
    "PaymentCollect Configuration VISA"
    __name__ = 'payment_collect.configuration.visa'
    payment_method_visa = fields.Many2One('account.invoice.payment.method',
        "Payment Method VISA")
    visa_company_code = fields.Char('Compay code VISA')
