# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################
import json
import urllib2


def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """

    result = {}

    # add to shopping cart
    if auth.user is not None and request.get_vars['add_one_to_cart'] is not None:
        item_id = request.get_vars['add_one_to_cart']
        cart_rows = db((db.cart_table.user_id == str(auth.user.id)) & (db.cart_table.item_id == item_id)).select()
        if len(cart_rows) is not 0:
            quantity = cart_rows.first()['quantity']
            db((db.cart_table.user_id == str(auth.user.id)) & (db.cart_table.item_id == item_id)).update(
                quantity=quantity + 1)
        else:
            db.cart_table.insert(user_id=str(auth.user.id), item_id=item_id, quantity=1)
    elif auth.user is not None and request.get_vars['remove_one_from_cart'] is not None:
        item_id = int(request.get_vars['remove_one_from_cart'])
        cart_rows = db((db.cart_table.user_id == str(auth.user.id)) & (db.cart_table.item_id == item_id)).select()
        if len(cart_rows) is not 0:
            quantity = cart_rows.first()['quantity']
            if quantity <= 1:
                db((db.cart_table.user_id == str(auth.user.id)) & (db.cart_table.item_id == item_id)).delete()
            else:
                db((db.cart_table.user_id == str(auth.user.id)) & (db.cart_table.item_id == item_id)).update(
                    quantity=quantity - 1)

    item_rows = db(db.item_table).select()

    result['item_list'] = item_rows

    # load shopping cart
    if auth.user is not None:
        result['cart'] = []
        cart_rows = db(db.cart_table.user_id == str(auth.user.id)).select()
        for cart in cart_rows:
            item_rows = db(db.item_table.id == cart.item_id).select()
            item_row = item_rows.first()
            result['cart'].append(
                {
                    'id': item_row['id'],
                    'item_name': item_row['item_name'],
                    'category': item_row['category'],
                    'price': item_row['price'],
                    'image': item_row['image'],
                    'quantity': cart['quantity']
                }
            )
    return dict(user=auth.user, result=result)


@auth.requires_login()
def admin_panel():
    result = {}
    if auth.user is not None and auth.user.email == 'admin@addrest.us':
        result['page_type'] = 'admin'
        order_rows = db(db.order_table).select()
        result['orders'] = []
        for order_row in order_rows:
            address_json = json.load(
                urllib2.urlopen('http://127.0.0.1:8001/merchant_address_api?address_id=' + order_row[
                    'address'] + '&token=ZHANGXUBAIHANTIANYUE'))
            result['orders'].append(
                {
                    'id': order_row['id'],
                    'user_id': order_row['user_id'],
                    'item_id_array': order_row['item_id_array'].split(','),
                    'quantity_array': order_row['quantity_array'].split(','),
                    'total': order_row['total'],
                    'address_type': order_row['address_type'],
                    'address': order_row['address'],
                    'real_address_json': address_json['result']['address']
                }
            )
    else:
        result['page_type'] = 'invalid'
    return dict(user=auth.user, result=result)


@auth.requires_login()
def checkout():
    result = {}

    if auth.user is not None:
        result['cart'] = []
        cart_rows = db(db.cart_table.user_id == str(auth.user.id)).select()
        for cart in cart_rows:
            item_rows = db(db.item_table.id == cart.item_id).select()
            item_row = item_rows.first()
            result['cart'].append(
                {
                    'id': item_row['id'],
                    'item_name': item_row['item_name'],
                    'category': item_row['category'],
                    'price': item_row['price'],
                    'image': item_row['image'],
                    'quantity': cart['quantity']
                }
            )

    return dict(user=auth.user, result=result)


@auth.requires_login()
def confirm_order():
    result = {}
    if auth.user is not None and request.get_vars['address_id'] is not None:
        address_id = request.get_vars['address_id']
        item_id_array = ''
        quantity_array = ''
        cart_rows = db(db.cart_table.user_id == str(auth.user.id)).select()
        result['items'] = []
        for cart_row in cart_rows:
            item_id = cart_row['item_id']
            quantity = cart_row['quantity']
            item_rows = db(db.item_table.id == item_id).select()
            item_row = item_rows.first()
            result['items'].append(
                {
                    'id': item_row['id'],
                    'item_name': item_row['item_name'],
                    'category': item_row['category'],
                    'price': item_row['price'],
                    'image': item_row['image'],
                    'quantity': quantity
                }
            )
            if item_id_array == '':
                item_id_array += str(item_id)
                quantity_array += str(quantity)
            else:
                item_id_array += ',' + str(item_id)
                quantity_array += ',' + str(quantity)
        db.order_table.insert(user_id=auth.user.id, item_id_array=item_id_array, quantity_array=quantity_array, total=0,
                              address_type='addrest', address=address_id)
        db(db.cart_table.user_id == str(auth.user.id)).delete()
        result['status'] = 'success'
    else:
        result['status'] = 'fail'

    return dict(user=auth.user, result=result)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
