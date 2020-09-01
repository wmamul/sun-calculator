from flask import Flask, request, render_template, redirect, send_file
from calculator.offer import Offer
from calculator.interface import PrestigePackage, VipPackage, ClassicPackage
import json
import pdb

app = Flask(__name__, template_folder='../templates/', static_folder='../static/')

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
        return send_file(offer.pdf())
    return render_templace('prestige.html', form=form)

@app.route('/vip', methods=['GET'])
def vip():
    form = VipPackage() 
    if request.method == 'POST' and form.validate:
        return redirect('vip')
    return render_template('vip.html', form=form)

@app.route('/vip', methods=['POST'])
def vip_post():
    form = VipPackage(request.form) 
    if request.method == 'POST' and form.validate:
        offer = Offer(form, p='vip')
        return send_file(offer.pdf())
    return render_template('vip.html', form=form)

@app.route('/classic', methods=['GET'])
def classic():
    form = ClassicPackage() 
    if request.method == 'POST' and form.validate:
        return redirect('classic')
    return render_template('classic.html', form=form)

@app.route('/classic', methods=['POST'])
def classic_post():
    form = ClassicPackage(request.form) 
    if request.method == 'POST' and form.validate:
        offer = Offer(form, p='classic')
        return send_file(offer.pdf())
    return render_template('classic.html', form=form)

def run_app():
    app.run()
