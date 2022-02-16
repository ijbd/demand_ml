from multiprocessing import ProcessError
import pandas as pd
import tensorflow as tf
import keras_tuner as kt
import argparse
import pickle

from process_data import load_processed_data
from modules.model import build_model, split_data, split_features, get_normalizer

def build_model_for_search(hyperparameters):
	'''
	Note that build_model_for_search.normalizer must be defined ahead of time
	TODO
	'''
	# define solution space for fixed-length hyperparameters
	min_hidden_layers = 1
	max_hidden_layers = 5
	hidden_layers = hyperparameters.Int("hiddenLayers",min_hidden_layers,max_hidden_layers)
	activation = hyperparameters.Choice("activation",["relu","tanh"])
	learning_rate = hyperparameters.Float("lr", min_value=5e-4, max_value=1e-1, sampling="log")
	
	# define solution space for variable-length hyperparameters
	units = []
	dropout = []

	for i in range(5):
		units.append(hyperparameters.Choice(f"units_{i}", [64,128,256,512,1028]))
		dropout.append(hyperparameters.Choice(f"dropout_{i}", [.0, .1, .2]))
	
	return build_model(build_model_for_search.normalizer,hidden_layers,units,activation,dropout,learning_rate)

def hyperparameter_search(processed_data_filepath,search_dir,search_name,model_filepath):
	'''
	TODO
	'''
	# get data
	processed_data = load_processed_data(processed_data_filepath)

	train_dataset, val_dataset, test_dataset = split_data(processed_data)

	train_features, train_labels = split_features(train_dataset)
	val_features, val_labels = split_features(val_dataset)
	test_features, test_labels = split_features(test_dataset)

	# assign normalizer
	build_model_for_search.normalizer = get_normalizer(train_features)

	# build keras tuner
	tuner = get_tuner(search_dir, search_name)

	# search
	search(tuner,train_features,train_labels,val_features,val_labels)

	# save model
	best_model = get_best_model(tuner)
	best_model.save(model_filepath)
	
def get_tuner(search_dir,search_name):
	'''
	TODO
	''' 
	# define search parameters
	tuner = kt.RandomSearch(
		build_model_for_search,
		objective='val_loss',
		max_trials=200,
		directory=search_dir,
		project_name=search_name
	)
	return tuner

def get_best_model(tuner):
	return tuner.get_best_models(num_models=1)[0]

def search(tuner,train_features,train_labels,val_features,val_labels):
	'''
	TODO
	'''
	# add early stopping 
	early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=25)

	# search
	tuner.search(train_features, 
			train_labels,
			epochs=5000,
			validation_data=(val_features, val_labels),
			verbose=False,
			callbacks=[early_stop])

	return None

if __name__ == '__main__':
	# argument parsing
	parser = argparse.ArgumentParser('hyperparameter search',description='Find best ANN architecture for dataset.')
	parser.add_argument('processed_data_filepath',type=str)
	parser.add_argument('search_dir',type=str)
	parser.add_argument('bal_authority',type=str)
	parser.add_argument('model_filepath',type=str)
	args = parser.parse_args()
	
	# search
	hyperparameter_search(args.processed_data_filepath,
						args.search_dir,
						args.bal_authority,
						args.model_filepath)
