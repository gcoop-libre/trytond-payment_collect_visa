# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import paymode
from . import payment
from . import collect
from . import configuration


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationPaymentCollectVISA,
        paymode.PayMode,
        payment.PayModeVisa,
        collect.CollectSendStart,
        collect.CollectReturnStart,
        module='payment_collect_visa', type_='model')
