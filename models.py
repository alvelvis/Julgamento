from app import db
import datetime

class Corpus(db.Model):

    __tablename__ = "corpora"

    name = db.Column(db.String, primary_key=True, unique=True)
    date = db.Column(db.String)
    sentences = db.Column(db.Integer)
    about = db.Column(db.String)
    partitions = db.Column(db.String)
    goldenAlias = db.Column(db.String)
    systemAlias = db.Column(db.String)
    UPOSMatrix = db.Column(db.String)
    DEPRELMatrix = db.Column(db.String)

    def __init__(self, name, date, sentences, about, partitions, goldenAlias, systemAlias, UPOSMatrix="", DEPRELMatrix=""):

        self.name = name
        self.date = date
        self.sentences = sentences
        self.about = about
        self.partitions = partitions
        self.goldenAlias = goldenAlias
        self.systemAlias = systemAlias
        self.UPOSMatrix = UPOSMatrix
        self.DEPRELMatrix = DEPRELMatrix

    def __repr__(self):

        return "<Corpus {}>".format(self.name)
