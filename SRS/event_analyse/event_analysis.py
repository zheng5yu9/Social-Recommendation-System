from tf_idf import *

class Event_analysis:
    stopwords_file_path = 'data/stopwords/frenchST.txt'

    def __init__(self):
        self.corpus = Corpus()
        self.is_corpus_complete = False
        self.tf_idf = None

    def add_document_in_corpus(self, text, id_doc, is_website):
        """
        The id is as follow :
        - A description : Event's id
        - A website : Event's id + "_"
        """
        self.corpus.add_document(Document(text.lower(), Event_analysis.get_id_website(id_doc, is_website)))

    def set_corpus_complete(self):
        self.is_corpus_complete = True
        self.tf_idf = TfIdf(self.corpus, Event_analysis.stopwords_file_path)

    def compute_tf_idf(self, term, id_doc, is_website):
        """
        The id is as follow :
        - A description : Event's id
        - A website : Event's id + "_"
        """
        return self.tf_idf.get_tf_idf(term, Event_analysis.get_id_website(id_doc, is_website))

    def get_tf_idf_the_k_most_important(self, k, id_doc, is_website):
        if not self.is_corpus_complete:
            raise Exception("The corpus is not complete ! Please call set_corpus_complete when you've filled it.")

        if k <= 0:
            raise Exception("The k is <= 0 !")

        from itertools import islice
        from collections import OrderedDict

        #Transform OrderedDict(key, tuple(double1, double2)) in OrderedDict(key, double2)
        return OrderedDict((x[0], (x[1][0], x[1][1])) for x in islice(self.tf_idf.get_all_tf_idf_sorted(Event_analysis.get_id_website(id_doc, is_website)).items(), 0, k))

    @staticmethod
    def get_id_website(id_doc, is_website):
        return id_doc if not is_website else id_doc + '_'