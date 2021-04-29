#!/usr/bin/env python3

# import necessary modules
from flask_table import Table, Col

# declare table
class ItemTable(Table):    
    category=Col("Category")
    price=Col("Price")
    quantity=Col("Quantity")
    subtotal=Col("Subtotal")
    delete=Col("Delete")    

# get objects
class Item(object):
    def __init__(self, category, price, quantity, subtotal, delete):
        self.category=category        
        self.price=price
        self.quantity=quantity
        self.subtotal=subtotal      
        self.delete=delete  
