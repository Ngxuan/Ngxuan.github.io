from django.shortcuts import render
import pyrebase

config={
    "apiKey": "AIzaSyCIKUwbx7V-r7aRTrjfbPWPoNu1NUXg1XE",
    "authDomain": "fyp1-17b8b.firebaseapp.com",
    "databaseURL": "https://fyp1-17b8b-default-rtdb.firebaseio.com",
    "projectId": "fyp1-17b8b",
    "storageBucket": "fyp1-17b8b.appspot.com",
    "messagingSenderId": "4435587057",
    "ppId": "1:4435587057:web:af5912c987921a42531e50",
    "measurementId": "G-V66DWFTZS7"
}




firebase=pyrebase.initialize_app(config)
authe = firebase.auth()
database=firebase.database()

def index(request):
    channel_name = database.child('Data').child('Name').get().val()
    channel_age = database.child('Data').child('Age').get().val()
    return render(request,'test.html', {
        "channel_name" : channel_name,
        "channel_age": channel_age
    })