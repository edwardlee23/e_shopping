#!/usr/bin/env python3

# import necessary module
import pymongo

# connect to mongodb
def get_collection(col):
    client=pymongo.MongoClient("mongodb://localhost:27017/")
    database=client["database"]            
    collection=database[col]
    return collection
