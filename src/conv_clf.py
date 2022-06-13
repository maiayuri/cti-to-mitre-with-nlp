import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# #KERAS 
from keras.models import Sequential
from keras.layers import Dense, Embedding
from keras.callbacks import EarlyStopping
from scikeras.wrappers import KerasClassifier

from keras.layers import Dense, GlobalMaxPooling1D
from keras.layers import Conv1D, Embedding

from utils.filter_data import *

from nltk.tokenize import sent_tokenize
from utils.csv_output import Classifier_results, CSVOutput

from preprocessing_DL_utils import *

import os 

def f_measure(recall, precision):
    if recall != 0 and precision != 0:
        return (2*precision*recall)/(precision+recall)
    else:
        return 0.01

## Helper function for regex: creates a label_tec based on a specific windows path 
def repl(matchobj):
    return matchobj.group(2) + "_path" #the path name string is captured by group 2

TRAINING_SIZE = 0.80
# The maximum number of words to be used. (most frequent)
MAX_NB_WORDS = 50000
# Max number of words in each complaint.
MAX_SEQUENCE_LENGTH = 50
# This is fixed.
EMBEDDING_DIM = 100

def create_model(num_outputs, input_length): #66,9% con stop words 

    embedding_layer = Embedding(MAX_NB_WORDS, EMBEDDING_DIM, input_length=input_length)
    model = Sequential()
    model.add(embedding_layer)
    model.add(Conv1D(256,5,activation='relu'))
    model.add(GlobalMaxPooling1D())
    model.add(Dense(num_outputs, activation='softmax'))
    model.compile(
        loss='categorical_crossentropy',
        optimizer='adam',
        metrics=['accuracy']
    )
    print(model.summary())
    return model 

def main():

    pp_manager = DLPreprocessingManager()

    data_df = pd.read_csv('../data/dataset.csv')

    num_classes = len(data_df['label_tec'].value_counts())
    print(num_classes)

    path = './cnn_model'
    try:
        os.mkdir(path)
    except OSError as error:
        print(error)  

    pp_manager.fit(sentences=data_df['sentence'], labels=data_df['label_tec'])
    pp_manager.save_preprocessing_pipe(path=path)

    Y = pp_manager.get_labels_encoding(data_df['label_tec'])

    X_train, X_test, Y_train, Y_test = train_test_split(data_df['sentence'].values,data_df['label_tec'], test_size = 0.20, random_state = 42, stratify=data_df['label_tec'])

    #Transform sentences - TRAIN
    X_train_vec = pp_manager.get_features_vectors(X_train)
    print('Shape of data tensor:', X_train_vec.shape)
    #Transform label 
    Y_train_vec = pp_manager.get_labels_encoding(Y_train)

    #Transform sentences - TEST
    X_test_vec = pp_manager.get_features_vectors(X_test)
    print('Shape of data tensor:', X_test_vec.shape)
    #Transform label 
    Y_test_vec = pp_manager.get_labels_encoding(Y_test)

    epochs = 100
    batch_size = 32
    nn_model = KerasClassifier(model=create_model, num_outputs=num_classes, input_length=X_train_vec.shape[1], epochs=1, batch_size=batch_size, validation_split=0.2, loss="categorical_crossentropy", 
                        callbacks=[EarlyStopping(monitor='val_loss', patience=3, min_delta=0.0001)])
    nn_model.fit(X_train_vec,Y_train_vec)

    model_manager = Model_Manager(nn_model)
    model_manager.save_model(path=path)
    precision, recall, fscore, topk = model_manager.calculate_metrics(sentences_vec=X_test_vec, labels_vec=Y_test_vec, labels=Y)

    print("Precision: " + str(precision) + " Recall: " + str(recall) + " F-Score: " + str(fscore) + " AC@3: " + str(topk) + "\n")


if __name__ == "__main__":
    main()

# #TODO: Uncomment for saving predictions
# #Saving predictions
# test_len = len(X_test_vec)
# sentences = []
# actual_labels = []
# predicted_labels = []
# for i in range(test_len):
# # for i, x in np.nditer(X_test):
#     arr = np.array([X_test_vec[i]])
#     prediction = nn_model.predict(arr)
#     predicted_label = encoder.inverse_transform([prediction[0]])
#     predicted_labels.append(predicted_label[0])
#     actual_labels.append(Y_test.iloc[i])
#     sentences.append(X_test[i])
#         # print(test_set_x.iloc[i])
#         # print('Actual label:' + test_set_y.iloc[i])
#         # print("Predicted label: " + predicted_label)
    
# #DataFrame 
# data = {'sentences': sentences, 'actual_label': actual_labels, 'predicted_label': predicted_labels}
# pd.set_option('max_colwidth',1000)
# data_df = pd.DataFrame(data, columns=['sentences', 'actual_label', 'predicted_label'])
# #Saving on file predictions
# data_df.to_csv('prediction_cnn_new.csv')#, index=False)


# def remove_empty_lines(text):
# 	lines = text.split("\n")
# 	non_empty_lines = [line for line in lines if line.strip() != ""]

# 	string_without_empty_lines = ""
# 	for line in non_empty_lines:
# 		if line != "\n": 
# 			string_without_empty_lines += line + "\n"

# 	return string_without_empty_lines 

# def combine_text(list_of_text):
#     combined_text = ' '.join(list_of_text)
#     return combined_text

# def analyze_all_doc(file_path, tecs_vec):

#     lines = []
#     with open(file_path) as f:
#         lines += f.readlines()

#     ## Apply regex 
#     regex_list = load_regex("utils/regex.yml")

#     text = combine_text(lines)
#     text = re.sub('(%(\w+)%(\/[^\s]+))', repl, text)
#     text = apply_regex_to_string(regex_list, text)
#     text = re.sub('\(.*?\)', '', text)
#     text = remove_empty_lines(text)
#     text = text.strip()
#     sentences = sent_tokenize(text)

#     double_sentences = []

#     for i in range(1, len(sentences)):
#         new_sen = sentences[i-1] + sentences[i]
#         double_sentences.append(new_sen)

#     #Transform sentences
#     X = tokenizer.texts_to_sequences(sentences)
#     X = pad_sequences(X, maxlen=MAX_SEQUENCE_LENGTH)

#     predictions = nn_model.predict(X)

#     predicted = encoder.inverse_transform(predictions)

#     #Matrix
#     #Vector of vector of probabilities
#     predict_proba_scores = nn_model.predict_proba(X)
#     #Identify the indexes of the top predictions (increasing order so let's take the last 2, highest proba)
#     top_k_predictions = np.argsort(predict_proba_scores, axis = 1)[:,-2:]
#     #Get classes related to previous indexes
#     top_class_v = nn_model.classes_[top_k_predictions]

#     thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
#     precisions = []
#     recalls = []
#     corrected_pred = []
#     accepted_pred = []
#     correct_on_uniques = []
#     f1s = []

#     print(len(predicted))

#     num_sen = len(sentences)

#     for threshold in thresholds: 
#         tecs = tecs_vec
#         tecs = set(tecs)    
#         accepted = []

#         for i in range(0,len(predict_proba_scores)):
#             sorted_indexes = top_k_predictions[i]
#             top_classes = encoder.inverse_transform(top_class_v[i])
#             proba_vector = predict_proba_scores[i]
#             if proba_vector[sorted_indexes[1]] > threshold:
#                 accepted.append(top_classes[1])

#         correct = 0

#         unique_accepted = set(accepted)
#         len_tecs = len(tecs)

#         for pred in accepted:
#             if pred in tecs: #True Positives
#                 correct += 1

#         print(correct)

#         if len(accepted) != 0:
#             precision = correct/len(accepted)*100
#         else:
#             precision = 0
        
#         precision = round(precision,2)
#         print(precision) #accuracy or precision?

#         precisions.append(precision)

#         for pred in accepted:
#             if pred in tecs:
#                 tecs.remove(pred)

#         recall = str(len_tecs-len(tecs))+ '/' + str(len_tecs)

#         print(recall) #Recall

#         recalls.append(recall)
#         recall = (len_tecs-len(tecs))/len_tecs

#         corrected_pred.append(correct) 
#         accepted_pred.append(len(accepted))
        
#         cou = str(len_tecs-len(tecs))+ '/' + str(len(unique_accepted))
#         correct_on_uniques.append(cou)
#         cou = 0 if len(unique_accepted) == 0 else (len_tecs-len(tecs))/len(unique_accepted)

#         f1 = f_measure(recall=recall, precision=cou)
#         f1 = round(f1,2)
#         f1s.append(f1)
#         print("Threshold: " + str(threshold) + ": " + str(cou) + " correct on uniques")

#     result = Classifier_results( title='CNN', 
#                                 lines=num_sen,
#                                 accepted_preds=accepted_pred, 
#                                 correct_preds=corrected_pred, 
#                                 precisions=precisions, 
#                                 recalls=recalls, 
#                                 correct_uniques=correct_on_uniques,
#                                 f1s=f1s)
#     return result

# from document_data import *

# fin6_intel_results = analyze_all_doc(fin6_files[2], 
#                             fin6_tecs_intel)
# fin6_intel_output = CSVOutput('FIN6/FIN6_intelligence_summary', [fin6_intel_results])
# fin6_intel_output.append_to_file('.')

# fin6_ref_1_results = analyze_all_doc(fin6_files[0], 
#                             fin6_tec_1)
# fin6_ref_1_output = CSVOutput('FIN6/FIN6_ref_1', [fin6_ref_1_results])
# fin6_ref_1_output.append_to_file('.')

# fin6_ref_2_results = analyze_all_doc(fin6_files[1], 
#                             fin6_tec_2)
# fin6_ref_2_output = CSVOutput('FIN6/FIN6_ref_2', [fin6_ref_2_results])
# fin6_ref_2_output.append_to_file('.')

# menuPass_ref_8_results = analyze_all_doc(menuPass_files[1], 
#                             menuPass_tec_8)
# menuPass_ref_8_output = CSVOutput('MenuPass/MenuPass_ref_8', [menuPass_ref_8_results])
# menuPass_ref_8_output.append_to_file('.')

# menuPass_ref_2_results = analyze_all_doc(menuPass_files[0], 
#                             menuPass_tec_2)
# menuPass_ref_2_output = CSVOutput('MenuPass/MenuPass_ref_2', [menuPass_ref_2_results])
# menuPass_ref_2_output.append_to_file('.')

# wizardSpider_ref_7_results = analyze_all_doc(wizardSpider_files[0], 
#                             wizardSpider_tec_7)
# wizardSpider_ref_7_output = CSVOutput('WizardSpider/WizardSpider_ref_7', [wizardSpider_ref_7_results])
# wizardSpider_ref_7_output.append_to_file('.')

# wizardSpider_ref_2_results = analyze_all_doc(wizardSpider_files[1], 
#                             wizardSpider_tec_2)
# wizardSpider_ref_2_output = CSVOutput('WizardSpider/WizardSpider_ref_2', [wizardSpider_ref_2_results])
# wizardSpider_ref_2_output.append_to_file('.')















