# -*-  coding=utf-8 -*-
from decimal import *
from typing import Tuple
from collections import OrderedDict
import inspect
from reportlab import rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import cm, inch
from reportlab.pdfgen.canvas import Canvas
from datetime import datetime
import pdb

BOLD_FONT = 'LiberationSans-Bold'
NORMAL_FONT = 'LiberationSans-Regular'

TWOPLACES = Decimal(10) ** -2

THERMO_TYPES = [0.17, 0.19, 0.32]

INVERTER_TYPES = {'Huawei SUN2000-4KTL-MO': 15, 'Solar EDGE SE3K-SE10K': 12}

PANEL_TYPES = {'Astroenergy Full Black 350/360WP': (350, 12, 25),\
        'Znshine 330WP': (330, 12, 25), 'Jinko JKM320-60V': (320, 15, 25),\
        'Boviet BVM6610M-315WP': (315, 12, 25)}

INSTALLATION_TYPES = ['Gospodarstwo domowe', 'Gospodarstwo rolne',\
        'Instalacja na potrzeby firmy']

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
            'Monitoring: ': 'konfiguracja WIFI + monitoring',
            'Audyt: ': 'Sprawdzenie instalacji pod kątem jej wydajności przed uruchomieniem'},
        'classic': {
            'Monitoring: ': 'wytyczne do samodzielnej konfiguracji WIFI',
            'Audyt: ': 'Sprawdzenie instalacji pod kątem jej wydajności przed uruchomieniem'}
        }

FOOTER = [
        'Kamil Kupsik',
        'Doradca handlowy',
        '+48 515 076 934',
        'HSG Sun Sp. z.o.o.',
        'ul. Okopowa 58/72',
        '01-042 Warszawa',
        '+48 530 439 439 biuro',
        '+48 530 164 164 infolinia handlowa',
        'mailto: kamil.kupsik@hsgsun.com.pl',
        'https://www.hsgsun.com.pl'
        ]
        
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

class Offer:

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
    _price_per_kw = 0
    _optimizers = False

    def __init__(self, form, p=None):
        self._owner = form.owner.data
        self._yearly_mean = form.yearly_mean.data
        self._type = form.installation_type.data
        self._thermo = form.thermo.data
        self._package = p
        self._optimizers = form.optimisers.data
        self._panel = Panel((form.panel.data, PANEL_TYPES[form.panel.data]))
        self._inverter = Inverter((form.inverter.data, INVERTER_TYPES[form.inverter.data]))
        if form.power_price.data:
            self._price_per_kw = form.power_price.data
        else:
            self._price_per_kw = PACKAGE_PRICES[self._package]

        getcontext().prec = 3

        if 'domowe' in  self._type:
            self._tax = Decimal(0.08)
        else:
            self._tax = Decimal(0.23)

    def _remove_exponent(self, d):

        getcontext().prec = 29

        return d.quantize(1) if d == d.to_integral() else d.normalize()

    def _get_power(self):

        self._power = self._yearly_mean * Decimal(1.2)

        if self._power > 10:
            self._power = self._yearly_mean * Decimal(1.3)

    def _raw(self):
        if self._power == 0:
            self._get_power()

        if 'EDGE' in self._inverter.name:
            self._net_price = self._power * (self._price_per_kw + SOLAR_EDGE_ADDITION)

        else:
            self._net_price = self._power * self._price_per_kw


    def _with_opts(self):
        if self._net_price == 0:
            self._raw()

        return self._power * PACKAGE_OPTS[self._package]

    def _with_subsidy(self, value: Decimal):
        return value - 5000

    def _with_thermo(self):
        gross_price = self._gross(self._net_price)
        thermo_price = gross_price - (gross_price * self.thermo)
        return thermo_price.quantize(TWOPLACES)

    def _with_opts_and_thermo(self):
        gross_price = self._gross(self._net_price + self._with_opts())
        thermo_price = gross_price - (gross_price * self.thermo)
        return thermo_price.quantize(TWOPLACES)

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
        if self._power == 0:
            self._get_power()

        self._power = (self._panel.power * self._num_of_panels) / 1000

        return str(self._remove_exponent(self._power))

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

    def calculate(self):

        if self._optimizers:
            prices = {
                    'Cena instalacji netto: ': self.net_price,
                    'Cena instalacji brutto: ': self.gross(self._net_price),
                    'Cena instalacji brutto z optymalizatorami: ': self.gross(self._net_price + self._with_opts()),
                    'Wartość instalacji z dofinansowaniem "Mój prąd": ': self.gross_with_subsidy(self._net_price),
                    'Wartość instalacji z optymalizatorami i dofinansowaniem "Mój prąd": ': self.gross_with_subsidy(self._net_price + self._with_opts()),
                    f'Wartość instalacji z ulgą termomodernizacyjną {self._thermo[2:4]}%: ': str(self._with_thermo()),
                    f'Wartość instalacji z ulgą termomodernizacyjną {self._thermo[2:4]}%\n i dofinansowaniem "Mój prąd": ': self.gross_with_subsidy(self._with_thermo()),
                    f'Wartość instalacji z optymalizatorami i ulgą termomodernizacyjną {self._thermo[2:4]}%: ': str(self._with_opts_and_thermo()),
                    f'Wartość instalacji z optymalizatorami, ulgą termomodernizacyjną {self._thermo[2:4]}%\n oraz dofinansowaniem "Mój prąd": ': str(self._with_subsidy(self._with_opts_and_thermo()))
                    }
        
        else:
            prices = {
                    'Cena instalacji netto: ': self.net_price,
                    'Cena instalacji brutto: ': self.gross(self._net_price),
                    'Wartość instalacji z dofinansowaniem "Mój prąd": ': self.gross_with_subsidy(self._net_price),
                    f'Wartość instalacji z ulgą termomodernizacyjną {self._thermo[2:4]}%: ': str(self._with_thermo()),
                    f'Wartość instalacji z ulgą termomodernizacyjną {self._thermo[2:4]}%\n i dofinansowaniem "Mój prąd": ': self.gross_with_subsidy(self._with_thermo())
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
                'Właściciel: ': self._owner,
                'Ilość paneli: ': self.num_of_panels,
                'Proponowana moc instalacji: ': f'{self.power}kW',
                'Średnie roczne zużycie energetyczne: ': f'{self.yearly_mean}MWH',
                'Rodzaj instalacji: ': self._type,
                'Rodzaj paneli fotowoltaicznych: ': self.panel[0],
                'Inwerter: ': self._inverter.name,
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
        title = f'{self._owner}_{current_date}_{current_time}.pdf'

        pdf_canvas = Canvas('static/offers/' + title)
        pdf_canvas.setTitle(title)

        pdf_canvas.drawImage('static/images/hsg_logo.png', 1 * cm, 27 * cm,\
                width=186, height=44, mask='auto')

        text = pdf_canvas.beginText(2 * cm, 25 * cm)

        for key, value in data.items():

            field_cursor = text.getCursor()

            text.setFont(BOLD_FONT, 12)
            field = f'{key}'
            text.textLines(field)

            field_width = stringWidth(field.split('\n')[-1], BOLD_FONT, 12)
            ver_diff = text.getCursor()[1] - field_cursor[1]

            if key == f'Wartość instalacji z optymalizatorami, ulgą termomodernizacyjną {self._thermo[2:4]}%\n oraz dofinansowaniem "Mój prąd": '\
            or key == f'Wartość instalacji z ulgą termomodernizacyjną {self._thermo[2:4]}%\n i dofinansowaniem "Mój prąd": ':
                ver_diff = ver_diff / 2

            text.moveCursor(field_width + 0.1 * cm, ver_diff)

            text.setFont(NORMAL_FONT, 12)

            if 'Cena' in key or 'Wartość' in key:
                field_value = f'{value} zł'
            else:
                field_value = f'{value}'

            text.textLines(field_value)

            hor_diff = text.getCursor()[0] - field_cursor[0]

            text.moveCursor(-hor_diff, 0)

            if 'Audyt' in key:
                text.textLines('\n')

        foot = pdf_canvas.beginText(2 * cm, 6 * cm)
        foot.setFont(NORMAL_FONT, 9)
        foot.textLines(FOOTER)

        pdf_canvas.drawText(text)
        pdf_canvas.drawText(foot)

        pdf_canvas.save()

        return 'static/offers/' + title

