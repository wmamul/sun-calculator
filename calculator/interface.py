from decimal import ROUND_DOWN
from typing import Dict
from .offer import (Offer,
        INVERTER_TYPES,
        INSTALLATION_TYPES,
        PANEL_TYPES,
        THERMO_TYPES)
from wtforms import (Form,
        BooleanField,
        SelectField,
        StringField,
        IntegerField,
        DecimalField)
from wtforms.validators import InputRequired, NumberRange


class OfferClass(Form):

    owner = StringField('Właściciel', validators=[InputRequired(message='Podaj imię i naziwsko')])
    yearly_mean = DecimalField('Średnie roczne zużycie energetyczne [MWh]', places=3,\
            rounding=ROUND_DOWN, validators=[InputRequired(message='Wprowadź zużycie w megawatach')])
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
    power_price = IntegerField('Cena za kW (opcjonalne)', validators=[NumberRange(min=4250,\
            message='Minimalna wartość dla wybranego pakietu to %(min)')])

class VipPackage(OfferClass):

    panel = SelectField('Rodzaj paneli', choices=[list(PANEL_TYPES.keys())[2]])
    power_price = IntegerField('Cena za kW (opcjonalne)', validators=[NumberRange(min=4500,\
            message='Minimalna wartość dla wybranego pakietu to %(min)')])

class ClassicPackage(OfferClass):

    panel = SelectField('Rodzaj paneli', choices=[list(PANEL_TYPES.keys())[3]])
    power_price = IntegerField('Cena za kW (opcjonalne)', validators=[NumberRange(min=5000,\
            message='Minimalna wartość dla wybranego pakietu to %(min)')])
