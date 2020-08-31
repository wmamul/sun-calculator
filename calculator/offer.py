# -*-  coding=utf-8 -*-
from decimal import *
from typing import Tuple
from collections import OrderedDict
import inspect
from reportlab import rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlat.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import cm, inch
from reportlab.pdfgen.canvas import Canvas
from datetime import datetime
import pdb

BOLD_FONT = 'LiberationSans-Bold'
NORMAL_FONT = 'LiberationSans-Regular'

TWOPLACES = Decimal(10) ** -2

THERMO_TYPES = [0, 0.17, 0.19, 0.32]

INVERTER_TYPES = {'Huawei SUN2000-4KTL-MO': 15, 'Solar EDGE SE3K-SE10K': 12}

PANEL_TYPES = {'Astroenergy Full Black 350/360WP': (350, 12, 25),\
        'Znshine 330WP': (330, 12, 25), 'Jinko JKM320-60V': (320, 15, 25),\
        'Boviet BVM6610M-315WP': (315, 12, 25)}

INSTALLATION_TYPES = ['Gospodarstwo domowe', 'Gospodarstwo rolne',\
        'Instalacja na potrzeby firmy']

MAPPED_VALUES = ['_address', '_owner', '_type', 'inverter',\
        'power', 'panel', 'num_of_panels', 'net_price', '_optimizers']

PACKAGE_PRICES = {'prestige': 5000, 'vip': 4500, 'classic': 4250}
PACKAGE_OPTS = {'prestige': 400, 'vip': 300, 'classic': 200}
SOLAR_EDGE_ADDITION = 450

PACKAGE_CONSTS = {
        'prestige': {
            'Serwis: ': 'darmowy przegląd instalacji po 2 latach',
            'Monitoring: ': 'monitoring z poziomu aplikacji;\n\
            dodatkowo zdalny monitoring wykonywany poprzez naszą firmę\n\
                    w celu jak największego bezpieczeństwa instalacji',
            'Audyt: ': 'Sprawdzenie instalacji pod kątem jej wydajności przed uruchomieniem'},
        'vip': {
            'Monitoring': 'konfiguracja WIFI + monitoring',
            'Audyt': 'Sprawdzenie instalacji pod kątem jej wydajności przed uruchomieniem'},
        'classic': {
            'Monitoring': 'wytyczne do samodzielnej konfiguracji WIFI',
            'Audyt': 'Sprawdzenie instalacji pod kątem jej wydajności przed uruchomieniem'}
        }

class LastUpdatedOrderedDict(OrderedDict):
    'Store items in the order the keys were last added'

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)

class Inverter:

    def __init__(self, data: Tuple):
        self.name = data[0]
        self.warranty = data[1]

class Panel:

    def __init__(self, data: Tuple):
        self.name = data[0]
        self.power = data[1][0]
        self.product_warranty = data[1][1]
        self.linear_warranty = data[1][2]

class OfferMapper:

    def __init__(self, offer):
        self._mapped_class = offer

    def get_dict(self):
        self.map = []
        for i in inspect.getmembers(self._mapped_class):
            if i[0] in MAPPED_VALUES:
                self.map.append(i)

        return dict(self.map)


class Offer:

    _address = ''
    _owner = ''
    _type = ''
    _package = ''
    _inverter = ''
    _thermo = 0
    _tax = 0
    _yearly_mean = 0
    _power = 0
    _num_of_panels = 0
    _net_price = 0
    _optimizers = False

    def __init__(self, form, p=None):
        self._address = form.address.data
        self._owner = form.owner.data
        self._yearly_mean = form.yearly_mean.data
        self._type = form.installation_type.data
        self._thermo = form.thermo.data
        self._package = p
        self._optimizers = form.optimisers.data
        self._panel = Panel((form.panel.data, PANEL_TYPES[form.panel.data]))
        self._inverter = Inverter((form.inverter.data, INVERTER_TYPES[form.inverter.data]))

        getcontext().prec = 3

        if 'domowe' in  self._type:
            self._tax = Decimal(0.08)
        else:
            self._tax = Decimal(0.23)

    def _remove_exponent(self, d):

        getcontext().prec = 29

        return d.quantize(1) if d == d.to_integral() else d.normalize()

    def _get_power(self):

        if self._yearly_mean < 10:
            self._power = self._yearly_mean * Decimal(1.2)
        else:
            self._power = self._yearly_mean * Decimal(1.3)

    def _raw(self):
        if self._power == 0:
            self._get_power()

        if 'EDGE' in self._inverter.name:
            self._net_price = self._power * (PACKAGE_PRICES[self._package] + SOLAR_EDGE_ADDITION)

        else:
            self._net_price = self._power * PACKAGE_PRICES[self._package]


    def _with_opts(self):
        if self._optimizers:
            if self._net_price == 0:
                self._raw()

            return self._power * PACKAGE_OPTS[self._package]
        else:
            return "N/D"

    def _with_subsidy(self, value: Decimal):
        return value - 5000

    def _with_thermo(self):
        gross_price = self._gross(self._net_price)
        thermo_price = gross_price - (gross_price * self.thermo)
        return thermo_price.quantize(TWOPLACES)

    def _with_opts_and_thermo(self):
        if self._optimizers:
            gross_price = self._gross(self._net_price + self._with_opts())
            thermo_price = gross_price - (gross_price * self.thermo)
            return thermo_price.quantize(TWOPLACES)
        else:
            return "N/D"

    def _gross(self, value: Decimal):
        return value + value * self._tax

    def gross(self, value: Decimal):

        value_noexp = self._remove_exponent(value)
        gross_price = value_noexp + value_noexp * self._tax
        return str(gross_price.quantize(TWOPLACES))

    def gross_with_subsidy(self, value: Decimal):
        gross_price = self._remove_exponent(self._with_subsidy(self._gross(value)))
        return str(gross_price.quantize(TWOPLACES))
    
    @property
    def thermo(self):
        return Decimal(self._thermo)

    @property
    def inverter(self):
        return (f'{self._inverter.name}', self._inverter.warranty)

    @property
    def panel(self):
        return (f'{self._panel.name}', self._panel.product_warranty, self._panel.linear_warranty)

    @property
    def num_of_panels(self):

        getcontext().rounding = ROUND_CEILING

        if self._power == 0:
            tmp = self.power

        self._num_of_panels = ((self._power * 1000) / self._panel.power).quantize(Decimal(1))
        return str(self._num_of_panels)

    @property
    def yearly_mean(self):
        value = str(self._yearly_mean)
        return value

    @yearly_mean.setter
    def yearly_mean(self, value: Decimal):
        self._yearly_mean = value

    @yearly_mean.deleter
    def yearly_mean(self):
        del self._yearly_mean

    @property
    def power(self):
        return str(self._power)

    @power.setter
    def power(self, value: Decimal):
        self._power = value

    @property
    def net_price(self):
        value = self._net_price
        return str(self._remove_exponent(value))

    @net_price.setter
    def net_price(self, value: Decimal):
        self._net_price = value

    @net_price.deleter
    def net_price(self):
        del self._net_price

    def get_map(self):
        mapper = OfferMapper(self)
        return mapper.get_dict()

    def calculate(self):

        prices = {
                'Cena instalacji netto: ': self.net_price,
                'Cena instalacji brutto: ': self.gross(self._net_price),
                'Cena instalacji brutto z optymalizatorami: ': self.gross(self._net_price + self._with_opts()),
                'Koszt instalacji z dofinansowaniem "Mój prąd": ': self.gross_with_subsidy(self._net_price),
                'Koszt instalacji z optymalizatorami i dofinansowaniem "Mój prąd": ': self.gross_with_subsidy(self._net_price + self._with_opts()),
                f'Koszt instalacji z z ulgą termomodernizacyjną {self._thermo[2:4]}%: ': str(self._with_thermo()),
                f'Koszt instalacji z ulgą termomodernizacyjną {self._thermo[2:4]}%: ': self.gross_with_subsidy(self._with_thermo()),
                f'Koszt instalacji z optymalizatorami i ulgą termomodernizacyjną {self._thermo[2:4]}%: ': str(self._with_opts_and_thermo()),
                f'Koszt instalacji z optymalizatorami, z ulgą termomodernizacyjną {self._thermo[2:4]}%\n oraz dofinansowaniem "Mój prąd": ': str(self._with_subsidy(self._with_opts_and_thermo()))
                }
        ordered_prices = LastUpdatedOrderedDict()

        for key, value in prices.items():
            ordered_prices.__setitem__(key, value)

        return ordered_prices

    def pdf(self):

        if self._net_price == 0:
            self._raw()

        rl_config.TTFSearchPath.append('static/fonts/')

        pdfmetrics.registerFont(TTFont('LiberationSans-Regular', 'LiberationSans-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('LiberationSans-Bold', 'LiberationSans-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('LiberationSans-Italic', 'LiberationSans-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('Liberationsans-BoldItalic', 'LiberationSans-BoldItalic.ttf'))

        pdf_map = {
                'Adres: ': self._address,
                'Właściciel: ': self._owner,
                'Proponowana moc instalacji: ': f'{self.power}kW',
                'Średnie roczne zużycie energetyczne: ': f'{self.yearly_mean}MWH',
                'Rodzaj instalacji: ': self._type,
                'Rodzaj paneli fotowoltaicznych: ': self.panel[0],
                'Inwerter: ': self._inverter.name,
                'Ilość paneli: ': self.num_of_panels,
                'Gwarancja paneli: ': f'{self._panel.product_warranty} letnia gwarancja produktowa, {self._panel.linear_warranty} letnia gwarancja liniowa',
                'Gwarancja inwerter: ': f'{self._inverter.warranty} lat',
                'Optymalizatory: ': "Nie" if not self._optimizers else f'{PACKAGE_OPTS[self._package]} zł',
                }

        data = LastUpdatedOrderedDict()

        for key, value in pdf_map.items():
            data.__setitem__(key, value)

        for key, value in PACKAGE_CONSTS[self._package].items():
            data.__setitem__(key, value)

        data.update(self.calculate())

        current_date = datetime.utcnow().strftime("%d%m%Y")
        current_time = datetime.utcnow().strftime("%H%M%S")

        pdf_canvas = Canvas(f'{self._owner}_{current_date}_{current_time}.pdf')

        pdf_canvas.drawImage('static/images/hsg_logo.png', 1 * cm, 24 * cm, mask='auto')

        text = pdf_canvas.beginText(2 * cm, 22 * cm)

        for key, value in data.items():
            
            field_cursor = text.getCursor()

            text.setFont('LiberationSans-Bold', 12)
            field = f'{key}'
            text.textLines(field)

            field_width = stringWidth(field,

            text.setFont('LiberationSans-Regular', 12)
            field_value = f'{value}'
            text.textLines(field_value)

            if 'Audyt' in key:
                text.textLines('\n')

        pdf_canvas.drawText(text)

        pdf_canvas.save()

        return data

