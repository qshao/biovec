from Bio import SeqIO
from theano import function, config, shared, tensor

from collections import Counter
import biovec
import bio_tsne
import tensorflow as tf
import numpy as np
import os
import sys
import gzip


def make_protein_vector(fasta_file, protein_vector_fname, ngram_vectors):
    with gzip.open(fasta_file, 'rb') as fasta_file:
        with open(protein_vector_fname, 'w') as output_file:
            for record in SeqIO.parse(fasta_file, "fasta"):
                protein_name = record.name.split('|')[-1]
                protein_vector = pv.to_vecs(record.seq, ngram_vectors)

                output_file.write('{}\t{}\n'.format(protein_name, ' '.join(map(str, protein_vector))))

def get_uniprot_protein_families(path):
    protein_families = {}
    protein_family_stat = Counter()
    for record in SeqIO.parse(path, "fasta"): 
        family_id = None
        for element in record.description.split():
            if element.startswith('PFAM'):
                family_id = element.split('=', 1)[1]
        if family_id:
            uniprot_id = record.name.split('|')[-1]
            protein_families[uniprot_id] = family_id
            protein_family_stat[family_id] += 1

    return protein_families, protein_family_stat

def make_uniport_with_families(Pfam_file, fasta_file, uniprot_with_families): 
    protein_families = {}
    protein_family_stat = Counter()
    with gzip.open(Pfam_file, 'rb') as gzipped_file:
        for record in SeqIO.parse(gzipped_file, "fasta"):  
            family_id = record.description.rsplit(';', 2)[-2]
            uniprot_id = record.name.split('/', 1)[0].lstrip('>') 
            protein_families[uniprot_id] = family_id

    with gzip.open(fasta_file, 'rb') as gzipped_file, \
        open(uniprot_with_families, "w") as output_fasta:
        for record in SeqIO.parse(gzipped_file, "fasta"):
            uniprot_id = record.name.split('|')[2] 
            if uniprot_id in protein_families:
                family = protein_families[uniprot_id]
                record.description += ' PFAM={}'.format(protein_families[uniprot_id])
                SeqIO.write(record, output_fasta, "fasta")

fasta_file = "document/uniprot_sprot.fasta.gz"
Pfam_file = "document/Pfam-A.fasta.gz"
ngram_corpus_fname = "trained_models/ngram_vector.txt"
model_ngram = "trained_models/ngram_model"
protein_vector_fname = "trained_models/protein_vector.txt"
uniprot_with_families = "trained_models/uniprot_with_families.fasta"
protein_pfam_vector_fname = "trained_models/protein_pfam_vector.csv"

#Make corpus
pv = biovec.ProtVec(fasta_file, out="trained_models/ngram_corpus.txt")

print ("Checking the file(trained_models/ngram_vector.csv)")
if not os.path.isfile(ngram_model_fname) or not os.path.isfile(protein_model_fname):
    print ('INFORM : There is no vector model file. Generate model files from data file...')
    
    #Make ngram_vector.txt and word2vec model
    pv.word2vec_init(ngram_corpus_fname)
    pv.save(model_ngram) 

    #Get ngram and vectors
    ngram_vectors = pv.get_ngram_vectors(ngram_corpus_fname)
    
    #Make protein_vector.txt by ngram, vector, uniprot
    make_protein_vector(fasta_file, protein_vector_fname, ngram_vectors)

else:
    print("INFORM : File's Existence is confirmed\n")

print ("...OK\n")


print("Checking the file(trained_models/protein_pfam_vector.csv)")
if not os.path.isfile(protein_pfam_vector_fname):
    print ('INFORM : There is no pfam_model file. Generate pfam_model files from data file...')
    
    #Cut standard
    min_proteins_in_family = 10

    #Make uniprot_with_family.fasta by uniprot, Pfam
    make_uniport_with_families(Pfam_file, fasta_file, uniprot_with_families): 

    #Get protein_name, family_name, vectors
    protein_families, protein_family_stat = get_uniprot_protein_families(uniprot_with_families)


    #Make protein_pfam_vector_fname.csv by protein_name, family_name, vectors
    f = open(protein_pfam_model_fname, "w")
    with open(protein_vector_fname) as protein_vector_file:
        for line in protein_vector_file:
            uniprot_name, vector_string = line.rstrip().split('\t', 1)
            if uniprot_name in protein_families:
                family = protein_families[uniprot_name]
                if protein_family_stat[family] >= min_proteins_in_family:
                    f.write('{}\t{}\t{}'.format(uniprot_name, protein_families[uniprot_name], vector_string) + "\n")
    f.close()

print ("...Uniprot Done\n")

print("Start disprot...\n")

disprot_fasta = "document/disprot.fasta.gz"
dpv = biovec.ProtVec(disprot_fasta,
                     out="trained_models/disprot/disprot_ngram_corpus.txt")

print ("Checking the file(trained_models/ngram_vector.csv)")

# disprot
disprot_ngram = "trained_models/disprot/disprot_ngram.csv"
disprot_protein = "trained_models/disprot/disprot_protein.csv"
if not os.path.isfile(disprot_ngram) or not os.path.isfile(disprot_protein):
    print ('INFORM : There is no vector model file. Generate model files from data file...')
    dpv.word2vec_init(disprot_ngram)
    #dpv.save(model_ngram)

    ngram_vectors = dpv.get_ngram_vectors(disprot_ngram)
    open_gzip_fasta(disprot_fasta, disprot_protein)

else:
    print ("INFORM : File's Existence is confirmed\n")

print ("...OK\n")


# pdb
pdb_fasta= "document/uniprot_sprot.fasta.gz"
ppv = biovec.ProtVec(fasta_file,out="trained_models/pdb/pdb_ngram_corpus.txt")

pdb_ngram = "trained_models/pdb/pdb_ngram.csv"
pdb_protein = "trained_models/pdb/pdb_protein.csv"
if not os.path.isfile(pdb_ngram) or not os.path.isfile(pdb_protein):
    print ('INFORM : There is no vector model file. Generate model files from data file...')
    ppv.word2vec_init(pdb_ngram)
    #pv.save(model_ngram)

    ngram_vectors = ppv.get_ngram_vectors(pdb_ngram)
    open_gzip_fasta(pdb_fasta, pdb_protein)

else:
    print ("INFORM : File's Existence is confirmed\n")

print ("...OK\n")

#===============================================================================#
