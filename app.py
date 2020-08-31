from flask import Flask, request, render_template, redirect
from calculator.offer import Offer
from calculator.interface import PrestigePackage, VipPackage, ClassicPackage
import json
import pdb

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('base.html')

@app.route('/prestige', methods=['GET']) 
def prestige():
    form = PrestigePackage() 
    return render_template('prestige.html', form=form)

@app.route('/prestige', methods=['POST'])
def prestige_post():
    form = PrestigePackage(request.form)
    if request.method == 'POST' and form.validate:
        offer = Offer(form, p='prestige')
        return json.dumps(offer.pdf())
    return render_templace('prestige.html', form=form)

@app.route('/vip')
def vip():
    form = VipPackage() 
    if request.method == 'POST' and form.validate:
        return redirect('vip')
    return render_template('vip.html', form=form)

@app.route('/classic')
def classic():
    form = ClassicPackage() 
    if request.method == 'POST' and form.validate:
        return redirect('classic')
    return render_template('classic.html', form=form)

if __name__ == '__main__':
    app.run()

