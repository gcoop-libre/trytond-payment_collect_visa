# This file is part of the payment_collect_visa module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import PoolMeta, Pool


class CollectSendStart(metaclass=PoolMeta):
    __name__ = 'payment.collect.send.start'

    @classmethod
    def default_csv_format(cls):
        return False

    @property
    def origin_name(self):
        pool = Pool()
        PayModeVisa = pool.get('payment.paymode.visa')
        name = super().origin_name
        if isinstance(self.origin, PayModeVisa):
            name = self.origin.paymode.rec_name
        return name

    @classmethod
    def _get_origin(cls):
        models = super()._get_origin()
        models.append('payment.paymode.visa')
        return models


class CollectReturnStart(metaclass=PoolMeta):
    __name__ = 'payment.collect.return.start'

    @property
    def origin_name(self):
        pool = Pool()
        PayModeVisa = pool.get('payment.paymode.visa')
        name = super().origin_name
        if isinstance(self.origin, PayModeVisa):
            name = self.origin.paymode.rec_name
        return name

    @classmethod
    def _get_origin(cls):
        models = super()._get_origin()
        models.append('payment.paymode.visa')
        return models

    @classmethod
    def _paymode_types(cls):
        types = super()._paymode_types()
        return types
