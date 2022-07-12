import ast
from datetime import datetime, date
from flask import Blueprint, render_template, request, flash, redirect, url_for, json
from flask_login import login_required, current_user
from .models import Parameter, Product, Service, Transaction
from . import db
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.frequent_patterns import association_rules
from natsort import natsort_keygen, natsorted
from sqlalchemy import desc

dt = datetime.now()

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    parameters = Parameter.query.order_by(Parameter.id)
    if not db.session.query(Parameter).first():       
        new_support = Parameter(id=1, name='support', value='0.5')
        db.session.add(new_support)
        db.session.commit()
        new_confidence = Parameter(id=2, name='confidence', value='0.5')
        db.session.add(new_confidence)
        db.session.commit()
        
    total_sales = db.session.query(Transaction).count()
    total_product = db.session.query(Product).count()
    total_service = db.session.query(Service).count()
    print('{} dan {} dan {}'.format(dt.day, dt.month, dt.year))

    this_year = datetime.strptime('1/1/{}'.format(dt.year), '%d/%m/%Y')
    this_month = datetime.strptime('1/{}/{}'.format(dt.month, dt.year), '%d/%m/%Y')
    print(this_month)
    
    month_transactions = Transaction.query.filter(Transaction.date >= this_month)
    year_transactions = Transaction.query.filter(Transaction.date >= this_year)
    
    min_support = Parameter.query.get_or_404(1)
    min_confidence = Parameter.query.get_or_404(2)

    
    
    
    # print(df)
    try:

        try:
            data_month = []
    
            for transaction in month_transactions:
                data_month.append(ast.literal_eval(transaction.products.replace('"', "'")))
            
            te = TransactionEncoder()
            
            month_data = te.fit(data_month).transform(data_month)
            print(month_data)

            df_month = pd.DataFrame(month_data, columns=te.columns_)

            df_month = df_month.replace(False,0).replace(True,1)
            print(df_month)
            frequent_month = fpgrowth(df_month, min_support=float(min_support.value), use_colnames=True)
            print(frequent_month)
            rules_month = association_rules(frequent_month, metric="confidence", min_threshold=0.6)
            print(rules_month)
            frequent_month["itemsets"] = frequent_month["itemsets"].apply(lambda x: list(x)[0]).astype("unicode")
            rules_month["antecedents"] = rules_month["antecedents"].apply(lambda x: list(x)[0]).astype("unicode")
            rules_month["consequents"] = rules_month["consequents"].apply(lambda x: list(x)[0]).astype("unicode")

            rules_month['rank'] = rules_month['confidence'].rank(ascending=False, method='first').astype(int)
            rec_month = rules_month[rules_month['confidence'] > float(min_confidence.value)].sort_values(by='rank', ascending=True)
            rec_month = rec_month.head(3)
            print(rec_month)
        except:
            rec_month = pd.DataFrame(columns= ['antecedents', 'consequents', 'confidence', 'rank'])

        try:
            data_year = []

            for transaction in year_transactions:
                data_year.append(ast.literal_eval(transaction.products.replace('"', "'")))

            year_data = te.fit(data_year).transform(data_year)

            df_year = pd.DataFrame(year_data, columns=te.columns_)

            df_year = df_year.replace(False,0).replace(True,1)
            frequent_year = fpgrowth(df_year, min_support=float(min_support.value), use_colnames=True)
            rules_year = association_rules(frequent_year, metric="confidence", min_threshold=0.6)
            frequent_year["itemsets"] = frequent_year["itemsets"].apply(lambda x: list(x)[0]).astype("unicode")
            rules_year["antecedents"] = rules_year["antecedents"].apply(lambda x: list(x)[0]).astype("unicode")
            rules_year["consequents"] = rules_year["consequents"].apply(lambda x: list(x)[0]).astype("unicode")
            
            rules_year['rank'] = rules_year['confidence'].rank(ascending=False, method='first').astype(int)
            rec_year = rules_year[rules_year['confidence'] > float(min_confidence.value)].sort_values(by='rank', ascending=True)
            rec_year = rec_year.head(3)
            print(rec_year)
        except:
            rec_year=pd.DataFrame(columns= ['antecedents', 'consequents', 'confidence', 'rank'])
        
        
        # print(rules)
        flash("Data Success: ", category="success")
        return render_template('home.html', 
                                page='home',
                                total_sales=total_sales,
                                total_product=total_product,
                                total_service=total_service,
                                rules_month=rec_month,
                                rules_year=rec_year, 
                                user=current_user)
    except Exception as e:
            flash("Error! There was a problem: " + str(e), category="error")
            return render_template('home.html', 
                                    page='home',
                                    total_sales=total_sales,
                                    total_product=total_product,
                                    total_service=total_service, 
                                    rules_month=pd.DataFrame(columns= ['antecedents', 'consequents', 'confidence', 'rank']), 
                                    rules_year=pd.DataFrame(columns= ['antecedents', 'consequents', 'confidence', 'rank']), 
                                    user=current_user)


# Create transaction data
@views.route('/sales-transaction-data', methods=['GET', 'POST'])
@login_required
def transaction():
    items = Product.query.all()
    services = Service.query.all()
    transactions = Transaction.query.order_by(desc(Transaction.id))
    print('select transaction from database success')
    
    parameters = Parameter.query.order_by(Parameter.id)
    if not db.session.query(Parameter).first():       
        new_support = Parameter(id=1, name='support', value='0.5')
        db.session.add(new_support)
        db.session.commit()
        new_confidence = Parameter(id=2, name='confidence', value='0.5')
        db.session.add(new_confidence)
        db.session.commit()

    min_support = Parameter.query.get_or_404(1)
    min_confidence = Parameter.query.get_or_404(2)
    data = []
    for transaction in transactions:
        data.append(ast.literal_eval(transaction.products.replace('"', "'")))
    # print(data)
    te = TransactionEncoder()
    te_data = te.fit(data).transform(data)
    df = pd.DataFrame(te_data, columns=te.columns_)
    df = df.replace(False,0).replace(True,1)
    
    if request.method == 'POST':
        service_name = request.form.getlist('service-name')
        service_price = request.form.getlist('service-price')
        
        product_name = request.form.getlist('product-name')
        products = request.form.getlist('product-name')
        product_qtt = request.form.getlist('qtt')
        stock = request.form.getlist('stock')
        product_price = request.form.getlist('price')
        total_price = request.form.get('total-price')
        product_name.extend(service_name)
        product_price.extend(service_price)
        t_date = Transaction.query.filter(Transaction.date >= "{}-{}-01".format(dt.strftime('%y'),dt.strftime('%m'))).order_by(desc(Transaction.id))
        if t_date.count() == 0:
            id = 'ABM-{}-{}-{}'.format(dt.strftime('%Y'), dt.strftime('%m'),'1')
        else:
            id = 'ABM-{}-{}-{}'.format(dt.strftime('%Y'), dt.strftime('%m'), int(t_date[0].transaction_id.split('-')[-1]) + 1)
        
        for i, product in enumerate(products):
            new_product = Product.query.filter(Product.name == product).first()
            new_product.stock = int(stock[i]) - int(product_qtt[i])
            db.session.add(new_product)
            db.session.commit()

        try:
            transaction = Transaction(  transaction_id=id, 
                                        products='{}'.format(product_name), 
                                        qtt='{}'.format(product_qtt), 
                                        price='{}'.format(product_price), 
                                        total=total_price  )
            db.session.add(transaction)
            db.session.commit()
            product
            flash("Transaction Added Successfully", category="success")
            return redirect('/sales-transaction-data')
        except:
            flash("Error! There was a problem Adding transaction", category="error")
            return redirect('/sales-transaction-data')
    
    try:
        frequent_itemsets = fpgrowth(df, min_support=float(min_support.value), use_colnames=True)
        # print(frequent_itemsets)
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.6)
        frequent_itemsets["itemsets"] = frequent_itemsets["itemsets"].apply(lambda x: list(x)[0]).astype("unicode")
        rules["antecedents"] = rules["antecedents"].apply(lambda x: list(x)[0]).astype("unicode")
        rules["consequents"] = rules["consequents"].apply(lambda x: list(x)[0]).astype("unicode")
        rules['rank'] = rules['confidence'].rank(ascending=False, method='first').astype(int)
        rec = rules[rules['confidence'] >= float(min_confidence.value)].sort_values(by='rank', ascending=True)
        rec = rec.head(3)
        print(rec)
    except Exception as e:
        flash("Error! There was a problem: " + str(e), category="error")
        return render_template('transaction.html', 
                            page='sales transaction data', 
                            transactions=transactions, 
                            products=json.dumps(items),
                            services=json.dumps(services), 
                            rules=pd.DataFrame(columns= ['antecedents', 'consequents', 'confidence', 'rank']),
                            user=current_user)
    
    return render_template('transaction.html', 
                            page='sales transaction data', 
                            transactions=transactions, 
                            products=json.dumps(items),
                            services=json.dumps(services),
                            rules=rec, 
                            user=current_user)


# import transaction
@views.route('/sales-transaction-data/import', methods=['GET', 'POST'])
@login_required
def transaction_import():
    items = Product.query.all()
    if request.method == 'POST':
        file = request.files['file']
        def new_products(row):
            return "', '".join([row['NAMA BARANG']]*row['QTT'])   

        data = pd.read_excel(file)
        data["PRICE"] = data["QTT"] * data["HARGA SATUAN"]
        # print(data)
        data = data.groupby('ID TRANSAKSI').agg({'TGL JUAL':'first', 'NAMA BARANG':list,'JENIS':list,'QTT':list, 'PRICE':list}).reset_index().sort_values("ID TRANSAKSI", axis=0, key=natsort_keygen())
        data["TOTAL"] = data["PRICE"].apply(sum)
        data_list = data.values.tolist()
        # print(data)
        try:
            for index, transaction in enumerate(data_list):
                transactions = Transaction( transaction_id=transaction[0], 
                                            date=transaction[1], 
                                            products='{}'.format(transaction[2]), 
                                            qtt='{}'.format(transaction[4]), 
                                            price='{}'.format(transaction[5]), 
                                            total=transaction[6])
                db.session.add(transactions)
                db.session.commit()
                print("{}. {} added successfully".format(index, transaction[0]))
            flash('All Product Added!', category='success')
        except:
            flash("Error! There was a problem importing data", category="error")
        finally:
            return redirect('/sales-transaction-data')  


# delete all transaction   
@views.route('/sales-transaction-data/delete', methods=['GET', 'POST'])
@login_required
def transactions_delete():
    try:
        db.session.query(Transaction).delete()
        db.session.commit()
        flash("Transaction Deleted Successfully", category="success")
        return redirect('/sales-transaction-data')
    except:
        flash("Error! There was a problem deleting", category="error")
        return redirect('/sales-transaction-data')

# Delete transaction
@views.route('/sales-transaction-data/<id>/delete')
@login_required
def transaction_delete(id):
    transaction = Transaction.query.get_or_404(id)
    try:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction Deleted Successfully", category="success")
        return redirect('/sales-transaction-data')
    except:
        flash("Error! There was a problem deleting", category="error")
        return redirect('/sales-transaction-data')

# Recomended Items
@views.route('/recomended-items', methods=['GET', 'POST'])
@login_required
def recomended_items():
    min_support = Parameter.query.get_or_404(1)
    min_confidence = Parameter.query.get_or_404(2)
    
    transactions = Transaction.query.order_by(desc(Transaction.id))
    data_month = []
    data_year = []
    for transaction in transactions:
        if transaction.date.strftime("%b %Y") not in data_month:
            data_month.append(transaction.date.strftime("%b %Y"))
        if transaction.date.strftime("%Y") not in data_year:
            data_year.append(transaction.date.strftime("%Y"))
    
    if request.method == 'POST':
        # FILTER DATA RANGE
        # date1 = datetime.strptime(request.form.get('date1'), '%d/%m/%Y')
        # date2 = datetime.strptime(request.form.get('date2'), '%d/%m/%Y')
        # filtered_transactions = Transaction.query.filter(Transaction.date >= date1).filter(Transaction.date < date2)
        
        # FILTER SELECT COMBOBOX
        select_month = request.form.get('select-month')
        select_year = request.form.get('select-year')
        print(select_month)
        print(select_year)

        if select_month:
            start = datetime.strptime('1 {}'.format(select_month), '%d %b %Y')
            try:
                end = datetime.strptime('31 {}'.format(select_month), '%d %b %Y')
            except:
                end = datetime.strptime('30 {}'.format(select_month), '%d %b %Y')
            filtered_transactions = Transaction.query.filter(Transaction.date >= start).filter(Transaction.date < end)

        if select_year:
            start = datetime.strptime('1-1-{}'.format(select_year), '%d-%m-%Y')
            end = datetime.strptime('31-12-{}'.format(select_year), '%d-%m-%Y')
            filtered_transactions = Transaction.query.filter(Transaction.date >= start).filter(Transaction.date < end)
        
        data = []
        for transaction in filtered_transactions:
            data.append(ast.literal_eval(transaction.products.replace('"', "'")))
        # print(data)
        te = TransactionEncoder()
        te_data = te.fit(data).transform(data)
        df = pd.DataFrame(te_data, columns=te.columns_)
        df = df.replace(False,0).replace(True,1)
        # print(df)
        try:
            frequent_itemsets = fpgrowth(df, min_support=float(min_support.value), use_colnames=True)
            # print(frequent_itemsets)
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.6)
            frequent_itemsets["itemsets"] = frequent_itemsets["itemsets"].apply(lambda x: list(x)[0]).astype("unicode")
            rules["antecedents"] = rules["antecedents"].apply(lambda x: list(x)[0]).astype("unicode")
            rules["consequents"] = rules["consequents"].apply(lambda x: list(x)[0]).astype("unicode")
            rules['rank'] = rules['confidence'].rank(ascending=False, method='first').astype(int)
            rec = rules[rules['confidence'] >= float(min_confidence.value)]
            # print(rules)
            if select_month:
                flash("Filtering Data Success: {}".format(select_month), category="success")
            if select_year:
                flash("Filtering Data Success: {}".format(select_year), category="success")
            
            return render_template('recomended_items.html', 
                                    page='recomended items', 
                                    frequent_itemsets=frequent_itemsets, 
                                    data_month=data_month,
                                    data_year=data_year,
                                    rules=rec, 
                                    user=current_user)
        except Exception as e:
            flash("Error! There was a problem: " + str(e), category="error")
            return render_template('recomended_items.html', 
                                    page='recomended items', 
                                    frequent_itemsets=frequent_itemsets,
                                    data_month=data_month,
                                    data_year=data_year, 
                                    rules=pd.DataFrame(columns= ['antecedents', 'consequents', 'confidence', 'rank']), 
                                    user=current_user)
        
    data = []
    for transaction in transactions:
        data.append(ast.literal_eval(transaction.products.replace('"', "'")))
    # print(data)
    te = TransactionEncoder()
    te_data = te.fit(data).transform(data)
    df = pd.DataFrame(te_data, columns=te.columns_)
    df = df.replace(False,0).replace(True,1)
    # print(df)
    try:
        frequent_itemsets = fpgrowth(df, min_support=float(min_support.value), use_colnames=True)
        print(frequent_itemsets)
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.6)
        frequent_itemsets["itemsets"] = frequent_itemsets["itemsets"].apply(lambda x: list(x)[0]).astype("unicode")
        rules["antecedents"] = rules["antecedents"].apply(lambda x: list(x)[0]).astype("unicode")
        rules["consequents"] = rules["consequents"].apply(lambda x: list(x)[0]).astype("unicode")
        rules['rank'] = rules['confidence'].rank(ascending=False, method='first').astype(int)
        rec = rules[rules['confidence'] >= float(min_confidence.value)]
        return render_template('recomended_items.html', 
                                page='recomended items', 
                                frequent_itemsets=frequent_itemsets, 
                                data_month=data_month,
                                data_year=data_year,
                                rules=rec, 
                                user=current_user)
    except Exception as e:
        flash("Error! There was a problem: " + str(e), category="error")
        return render_template('recomended_items.html', 
                                page='recomended items', 
                                frequent_itemsets=frequent_itemsets, 
                                data_month=data_month,
                                data_year=data_year,
                                rules=pd.DataFrame(columns= ['antecedents', 'consequents', 'confidence', 'rank']), 
                                user=current_user)


# Create Product
@views.route('/list-of-items', methods=['GET', 'POST'])
@login_required
def items():
    if request.method == 'POST':
        id = request.form.get('id')
        name = request.form.get('name')
        price = request.form.get('price')
        unit = request.form.get('unit')
        type = request.form.get('type')
        stock = request.form.get('stock') 

        item = Product.query.filter_by(id=id).first()
        if item:
            flash('Product Code has been registered!' , category='error')
        elif len(id) < 1:
            flash('Product code cannot be empty' , category='error')
        elif len(name) < 1:
            flash('Product name cannot be empty' , category='error')
        elif len(price) < 1:
            flash('Product price cannot be empty' , category='error')
        elif len(unit) < 1:
            flash('Product unit cannot be empty' , category='error')
        elif len(type) < 1:
            flash('Product type cannot be empty' , category='error')
        elif len(stock) < 1:
            flash('Product stock cannot be empty' , category='error')
        else:
            new_item = Product(id=id, name=name, price=price, unit=unit, type=type, stock=stock)
            db.session.add(new_item)
            db.session.commit()
            flash('Product Added!', category='success')   
    products = Product.query.order_by(Product.id)
    return render_template('items.html', page='list of items', user=current_user, products=products)

# Update Product
@views.route('/list-of-items/<id>/edit', methods=['GET', 'POST'])
@login_required
def item_update(id):
    new_product = Product.query.get_or_404(id)
    if request.method == 'POST':
        new_product.id = request.form.get('id')
        new_product.name = request.form.get('name')
        new_product.price = request.form.get('price')
        new_product.unit = request.form.get('unit')
        new_product.type = request.form.get('type')
        new_product.stock = request.form.get('stock')
        try:
            db.session.add(new_product)
            db.session.commit()
            flash("Items Updated Successfully", category="success")
            return redirect('/list-of-items')
        except:
            flash("Error! There was a problem updating", category="error")
            return redirect('/list-of-items')

# Delete Product
@views.route('/list-of-items/<id>/delete')
@login_required
def item_delete(id):
    product = Product.query.get_or_404(id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash("Items Deleted Successfully", category="success")
        return redirect('/list-of-items')
    except:
        flash("Error! There was a problem deleting", category="error")
        return redirect('/list-of-items')

# Delete All Product
@views.route('/list-of-items/delete')
@login_required
def items_delete():
    try:
        db.session.query(Product).delete()
        db.session.commit()
        flash("Items Deleted Successfully", category="success")
        return redirect('/list-of-items')
    except:
        flash("Error! There was a problem deleting", category="error")
        return redirect('/list-of-items')


# import product
@views.route('/list-of-items/import', methods=['GET', 'POST'])
@login_required
def item_import():
    if request.method == 'POST':
        file = request.files['file']
        data = pd.read_excel(file)
        # keys = ['id', 'name', 'price', 'unit']
        # products = [dict(zip(keys, sublst)) for sublst in data_list]
        try:
            for index, row in data.iterrows():  
                index += 1  
                products = Product(id=row['KODE BARANG'], name=row['NAMA BARANG'], price=row['HARGA SATUAN'], unit=row['UNIT'], type=row['JENIS'], stock=row['STOCK'])
                db.session.add(products)
                db.session.commit()
                print("{}. {} added successfully".format(index, row['KODE BARANG']))
            flash('All Product Added!', category='success')
            return redirect('/list-of-items')
        except Exception as e:
            flash("Error! There was a problem importing data" + str(e), category="error")
            return redirect('/list-of-items')


# Create Service
@views.route('/list-of-services', methods=['GET', 'POST'])
@login_required
def servicess():
    if request.method == 'POST':
        id = request.form.get('id')
        name = request.form.get('name')
        price = request.form.get('price')
        type = request.form.get('type')

        service = Service.query.filter_by(id=id).first()
        if service:
            flash('Service Code has been registered!' , category='error')
        elif len(id) < 1:
            flash('Service code cannot be empty' , category='error')
        elif len(name) < 1:
            flash('Service name cannot be empty' , category='error')
        elif len(price) < 1:
            flash('Service price cannot be empty' , category='error')
        elif len(type) < 1:
            flash('Service type cannot be empty' , category='error')
        else:
            new_service = Service(id=id, name=name, price=price, type=type)
            db.session.add(new_service)
            db.session.commit()
            flash('Service Added!', category='success')   
    services = Service.query.order_by(Service.id)
    return render_template('services.html', page='list of services', user=current_user, services=services)

# Update service
@views.route('/list-of-services/<id>/edit', methods=['GET', 'POST'])
@login_required
def service_update(id):
    new_service = Service.query.get_or_404(id)
    if request.method == 'POST':
        new_service.id = request.form.get('id')
        new_service.name = request.form.get('name')
        new_service.price = request.form.get('price')
        new_service.type = request.form.get('type')
        try:
            db.session.add(new_service)
            db.session.commit()
            flash("Service Updated Successfully", category="success")
            return redirect('/list-of-services')
        except:
            flash("Error! There was a problem updating", category="error")
            return redirect('/list-of-services')

# Delete service
@views.route('/list-of-services/<id>/delete')
@login_required
def service_delete(id):
    service = Service.query.get_or_404(id)
    try:
        db.session.delete(service)
        db.session.commit()
        flash("Services Deleted Successfully", category="success")
        return redirect('/list-of-services')
    except:
        flash("Error! There was a problem deleting", category="error")
        return redirect('/list-of-services')

# Delete All service
@views.route('/list-of-services/delete')
@login_required
def services_delete():
    try:
        db.session.query(Service).delete()
        db.session.commit()
        flash("Services Deleted Successfully", category="success")
        return redirect('/list-of-services')
    except:
        flash("Error! There was a problem deleting", category="error")
        return redirect('/list-of-services')


# import service
@views.route('/list-of-services/import', methods=['GET', 'POST'])
@login_required
def service_import():
    if request.method == 'POST':
        file = request.files['file']
        data = pd.read_excel(file)
        try:
            for index, row in data.iterrows():   
                index += 1  
                services = Service(id=row['KODE JASA'], name=row['NAMA JASA'], price=row['HARGA'], type=row['JENIS'])
                db.session.add(services)
                db.session.commit()
                print("{}. {} added successfully".format(index, row['KODE JASA']))
            flash('All Service Added!', category='success')
            return redirect('/list-of-services')
        except Exception as e:
            flash("Error! There was a problem importing data" + str(e), category="error")
            return redirect('/list-of-services')

# Support and Confidence page
@views.route('/support-and-confidence') 
@login_required
def support_confidence():
    parameters = Parameter.query.order_by(Parameter.id)
    if db.session.query(Parameter).first():
        support_value = parameters[0].value
        confidence_value = parameters[1].value
        return render_template('support_confidence.html', page='support and confidence', support_value=support_value, confidence_value=confidence_value, user=current_user)
    else:
        try:
            new_support = Parameter(id=1, name='support', value='0.5')
            db.session.add(new_support)
            db.session.commit()
            new_confidence = Parameter(id=2, name='confidence', value='0.5')
            db.session.add(new_confidence)
            db.session.commit()
            return render_template('support_confidence.html', page='support and confidence', support_value='0.5', confidence_value='0.5', user=current_user)
        except:
            flash("Error! There was a problem Initializing", category="error")
            return render_template('support_confidence.html', page='support and confidence')
        
# Change support
@views.route('/support/<id>', methods=['GET', 'POST'])
@login_required
def support(id):
    new_parameter = Parameter.query.get_or_404(id)
    if request.method == 'POST':
        new_parameter.value = request.form.get('value')
        try:
            db.session.add(new_parameter)
            db.session.commit()
            flash("Support Value Updated Successfully", category="success")
            return redirect('/support-and-confidence')
        except:
            flash("Error! There was a problem updating support value!", category="error")
            return redirect('/support-and-confidence')

# change confidence
@views.route('/confidence/<id>', methods=['GET', 'POST'])
@login_required
def confidence(id):
    new_parameter = Parameter.query.get_or_404(id)
    if request.method == 'POST':
        new_parameter.value = request.form.get('value')
        try:
            db.session.add(new_parameter)
            db.session.commit()
            flash("Confidence Value Updated Successfully", category="success")
            return redirect('/support-and-confidence')
        except:
            flash("Error! There was a problem updating confidence value!", category="error")
            return redirect('/support-and-confidence')

