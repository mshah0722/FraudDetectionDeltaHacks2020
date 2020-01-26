import sys
sys.path.append("APIS/")
sys.path.append("Forms/")

import API
from Transactions import get_transaction_data
from InputTransactionForm import TransactionForm

from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from flask_mongoengine import Document, MongoEngine
from flask_mongoengine.wtf import model_form
from datetime import datetime

from td_api import get_transations_by_customer
from prediction_models import get_list, parse_data_into_X_and_Y, parse_data_into_categories_to_data, train

app = Flask(__name__)

app.config['SECRET_KEY'] = '032893044egjhd3209r834'
app.config["MONGO_URI"] = 'mongodb+srv://user1:deltahacks@deltahacks-4necq.mongodb.net/test?retryWrites=true&w=majority'
app.config['MONGODB_SETTINGS'] = {
    'db': 'DeltaHacks',
    'host': ''
}
db = MongoEngine(app)
app.config.update(
    DEBUG=True,
)


class Transaction(db.Document):
    customerID = db.StringField(required=True)
    cost = db.DecimalField(required=True)
    date = db.IntField()
    time = db.IntField()
    longitude = db.DecimalField(required=True)
    latitude = db.DecimalField(required=True)
    categoryID = db.IntField(required=True)

    def __repr__(self):
        return f"Transaction('{self.customerID}','{self.cost}','{self.date}','{self.time}','{self.longitude}','{self.latitude}','{self.categoryID}')"

    def __str__(self):
        return f"Transaction('{self.customerID}','{self.cost}','{self.date}','{self.time}','{self.longitude}','{self.latitude}','{self.categoryID}')"


@app.route('/')
def hello_world():
    return "Hello World"


@app.route('/users')
def get_users():
    return API.responseJson


@app.route('/transaction/<customerID>', methods=['GET'])
def get_transactions(customerID):
    return get_transaction_data(customerID)


@app.route('/input-transaction', methods=['GET', 'POST'])
def input_transaction():
    form = TransactionForm()
    if form.validate_on_submit():

        X = [int(form.categoryID.data), float(
            form.longitude.data), float(form.latitude.data)]
        Y = [float(form.cost.data)]

        td_data = get_transations_by_customer(form.customerID.data)

        train_X, train_Y = parse_data_into_X_and_Y(td_data)

        cat_to_data = parse_data_into_categories_to_data(train_X, train_Y)

        cat_to_model = train(cat_to_data)

        prediction = cat_to_model[X[0]].predict([[X[1], X[2]]])[0]

        f_prediction = prediction * 1.3

        if (f_prediction) >= Y[0] or ((f_prediction < Y[0]) and ((Y[0] - f_prediction) <= 4)):
            print('wss')
            transaction = Transaction(customerID=form.customerID.data, cost=form.cost.data,
                                  longitude=form.longitude.data, latitude=form.latitude.data, categoryID=form.categoryID.data)
            print('wss2')
            transaction.save()
            print('wss3')
            flash(f'Transaction Added!', 'success')
            print('wss3')
            return (redirect(url_for('input_transaction')))
        else:
            return (redirect(url_for("validate_transaction")))

        
    return render_template('form.html', form=form)


@app.route("/validate_transaction", methods=["GET", "POST"])
def validate_transaction():
    return "suspecious"

@app.route('/get_approved_transactions', methods=['GET'])
def approved_transactions():
    array1 = []
    array2 = []
    for transaction in Transaction.objects:
        array1.append([transaction['categoryID'],
                       transaction['longitude'], transaction['latitude']])
        array2.append(transaction['cost'])
    # print(array1)
    # print(array2)
    return jsonify(Transaction.objects)


@app.route('/get_unapproved_transactions', methods=['GET'])
def unapproved_transactions():
    return


if __name__ == '__main__':
    app.run()
