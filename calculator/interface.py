from decimal import ROUND_DOWN
from typing import Dict
from .offer import Offer, INVERTER_TYPES, INSTALLATION_TYPES, PANEL_TYPES, THERMO_TYPES
from wtforms import Form, BooleanField, SelectField, StringField, DecimalField


class OfferClass(Form):

    address = StringField('Adres')
    owner = StringField('Właściciel')
    yearly_mean = DecimalField('Średnie roczne zużycie energetyczne [MWh]', places=3,\
            rounding=ROUND_DOWN)
    installation_type = SelectField('Typ instalacji', choices=INSTALLATION_TYPES)
    inverter = SelectField('Typ inwertera', choices=INVERTER_TYPES.keys())
    optimisers = BooleanField('Optymalizatory')
    thermo = SelectField('Ulga termomodernizacyjna', choices=THERMO_TYPES)

    def __dict__(self):
        data = (('installation_type', self.installation_type),
                ('inverter', self.inverter),
                ('optimisers', self.optimisers),
                ('panel', self.panel))
        return dict(data)

class PrestigePackage(OfferClass):

    _prestige_panels = [list(PANEL_TYPES.keys())[0], list(PANEL_TYPES.keys())[1]]
    panel = SelectField('Rodzaj paneli', choices=_prestige_panels)

class VipPackage(OfferClass):

    panel = list(PANEL_TYPES.keys())[2]

class ClassicPackage(OfferClass):

    panel = list(PANEL_TYPES.keys())[3]
