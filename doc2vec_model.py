from gensim.models.doc2vec import Doc2Vec

class Doc2VecModel:

    def __init__(self):
        self.model = Doc2Vec.load("./enwiki_dbow/doc2vec.bin")

    def get_model(self):
        return self.model
