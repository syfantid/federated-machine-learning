# federated-machine-learning
Multiple experimental settings for Federated Machine Learning using CNNs.

- [federated-machine-learning](#federated-machine-learning)
  * [Installation](#installation)
  * [Citations](#citations)
  * [How to run this code](#how-to-run-this-code)
    + [Data Pre-Processing](#data-pre-processing)
    + [Running Experiments](#running-experiments)
      - [Shell scripts](#shell-scripts)
      - [Experiments.py](#experimentspy)
        * [main(seed=123, shards_unbalanced=False, shards_balanced=False, sessions=False, evaluate=False, dest_folder_name='', args=None)](#main-seed-123--shards-unbalanced-false--shards-balanced-false--sessions-false--evaluate-false--dest-folder-name-----args-none-)
        * [experiment_pain(algorithm='centralized', dataset='PAIN', experiment='placeholder', setting=None, rounds=30, shards=None, balance_test_set=False, model_path=None, pretraining=None, cumulative=True, optimizer=None, loss=None, metrics=None, local_epochs=1, model_type='CNN', pain_gap=(), individual_validation=True, local_operation='global_averaging')](#experiment-pain-algorithm--centralized---dataset--pain---experiment--placeholder---setting-none--rounds-30--shards-none--balance-test-set-false--model-path-none--pretraining-none--cumulative-true--optimizer-none--loss-none--metrics-none--local-epochs-1--model-type--cnn---pain-gap-----individual-validation-true--local-operation--global-averaging--)
        * [run_pretraining(dataset, experiment, local_epochs, optimizer, loss, metrics, model_path, model_type, pretraining, rounds, pain_gap)](#run-pretraining-dataset--experiment--local-epochs--optimizer--loss--metrics--model-path--model-type--pretraining--rounds--pain-gap-)
        * [run_shards(algorithm, cumulative, dataset, experiment, local_epochs, model, model_type, rounds, shards, pain_gap, individual_validation, local_operation, balance_test)](#run-shards-algorithm--cumulative--dataset--experiment--local-epochs--model--model-type--rounds--shards--pain-gap--individual-validation--local-operation--balance-test-)
        * [run_sessions(algorithm, dataset, experiment, local_epochs, model, model_type, rounds, pain_gap, individual_validation, local_operation)](#run-sessions-algorithm--dataset--experiment--local-epochs--model--model-type--rounds--pain-gap--individual-validation--local-operation-)
      - [Model_Training.py](#model-trainingpy)
        * [federated_learning(model, global_epochs, train_data, train_labels, train_people, val_data, val_labels, val_people, val_all_labels, clients, local_epochs, individual_validation, local_operation, weights_accountant)](#federated-learning-model--global-epochs--train-data--train-labels--train-people--val-data--val-labels--val-people--val-all-labels--clients--local-epochs--individual-validation--local-operation--weights-accountant-)
        * [train_cnn(algorithm, model, epochs, train_data, train_labels, val_data, val_labels, val_people, val_all_labels, individual_validation)](#train-cnn-algorithm--model--epochs--train-data--train-labels--val-data--val-labels--val-people--val-all-labels--individual-validation-)
      - [Weights_Accountant.py](#weights-accountantpy)


## Installation
Clone this project from:
```bash
git clone https://github.com/ntobis/federated-machine-learning.git
```
Go into the directory `federated-machine-learning`. I recommend to create a virtual environment.
```bash
virtualenv venv
source venv/bin/activate
```
To install all dependencies run:
```bash
pip install -r requirements.txt
```
If you have the UNBC-McMaster shoulder pain expression archive database, which is required to run this code
out-of-the-box, create the following folders
- Data
- Data/Raw Data/  
- Data/Preprocessed Data/
- Data/Augmented Data/

and move the images into the "Raw Data" folder with the following naming convention ```43_0_0_0_2.jpg```, where the numbers refer to [person, session, culture, frame, pain_level].

Alternatively, you should be able to run the following commands from
the project's root directory:
```bash
mkdir Data
cd Data/
mkdir Raw\ Data
mkdir Preprocessed\ Data
mkdir Augmented\ Data
mv -r [folder where UNBC database is on your computer] Raw\ Data/
```

## Citations
If you use this code for your own research, please reference it using the following citation format:
```
@misc{rudovic2021personalized,
      title={Personalized Federated Deep Learning for Pain Estimation From Face Images}, 
      author={Ognjen Rudovic and Nicolas Tobis and Sebastian Kaltwang and Bj??rn Schuller and Daniel Rueckert and Jeffrey F. Cohn and Rosalind W. Picard},
      year={2021},
      eprint={2101.04800},
      archivePrefix={arXiv},
      primaryClass={cs.LG}
}
```

## How to run this code
### Data Pre-Processing
If your images do not follow the naming convention described above (the original UNBC dataset does not), i.e., ```43_0_0_0_2.jpg```, then:
1. Navigate to federated-machine-learning/Notebooks and run the notebook "input_restructuring.ipynb"
2. "Run All",  and the naming convention will be applied.

First, you will need to pre-process the image data.
1. Navigate to federated-machine-learning/Notebooks and run the notebook "Data Pre-Processing.ipynb"
2. "Run All",  and the pre-processing steps "histogram equalization" and "image flipping", and "image rotation/cropping" will be applied.

### Running Experiments
#### Shell scripts
There are 2 shell scripts that can be executed out-of-the-box.
```bash
./execute_local.sh
./execute_GCP.sh
```

`execute_local.sh` is recommended when running an experiment on an ordinary machine. `execute_GCP.sh` includes 2 sets of
additional parameters:

If you run this code on the Google Cloud Platform, you can specify
```bash
--project [your GCP project, e.g., centered-flash-251417]
--zone [your GCP VM zone, e.g., us-west1-b]
--instance [your GCP instance, e.g., tensorflow-1-vm]
```
and the instance will automatically be stopped once your experiment is completed.

If you have a Twilio account (see more under www.twilio.com), you can also provide your account credentials, as well as
a receiver phone number, to receive a text message once training is completed, or if an error occurs.

```bash
--sms_acc [your Twilio account, typically of the format ACeabXXXXXXXXXXXXX]
--sms_pw [your Twilio password, typically of the format eab57930XXXXXXXXXX]
--sender [your Twilio sender number, typically of the format +4418XXXXXXXX]
--receiver [your personal phone number, e.g., +4477XXXXXXXX]
```

#### Experiments.py
`Experiments.py` contains the functions responsible for running all experimental settings. See below for a description
of the most important functions:

##### main(seed=123, shards_unbalanced=False, shards_balanced=False, sessions=False, evaluate=False, dest_folder_name='', args=None)
The `main()` function initializes the tensorflow optimizer, loss function, and metrics to track. It also executes
experiment_pain(), which runs all experiments. We also specify the shards for the "randomized shards" experiment in the
main function, all at the top.

The main function then contains 4 blocks, all of which can be controlled with the function parameters. The first three
blocks run the experimental settings "randomized shards, unbalanced test data", "randomized shards, balanced test data",
and "sessions" respectively. Each experimental block runs the experiment_pain() function 11 times, once for each
experimental setting. The final block executes the evaluate_baseline() function.

##### experiment_pain(algorithm='centralized', dataset='PAIN', experiment='placeholder', setting=None, rounds=30, shards=None, balance_test_set=False, model_path=None, pretraining=None, cumulative=True, optimizer=None, loss=None, metrics=None, local_epochs=1, model_type='CNN', pain_gap=(), individual_validation=True, local_operation='global_averaging')
The `experiment_pain()` function allows to fine tune each experimental setting. It defines if a given experiment should be
centralized or federated, which type of federated algorithm should be run. It defines if pre-training should be applied,
as well as how many global and local epochs should be run.

**It is recommended to limit changes to the code to the parameters of this function, if the general features should be
maintained and only different experimental settings (optimizers, number of epochs, etc.) are expected to be tried.**

##### run_pretraining(dataset, experiment, local_epochs, optimizer, loss, metrics, model_path, model_type, pretraining, rounds, pain_gap)
`run_pretraining()` returns one of 4 models depending on the arguments provided: A Tensorflow model loaded from file,
a model that was pre-trained with the centralized algorithm, a model that was pre-trained with the federated
algorithm, or a randomly initialized model.

##### run_shards(algorithm, cumulative, dataset, experiment, local_epochs, model, model_type, rounds, shards, pain_gap, individual_validation, local_operation, balance_test)
`run_shards()` runs the randomized shards experiment. It follows the algorithm described in chapter 5 of the thesis.

##### run_sessions(algorithm, dataset, experiment, local_epochs, model, model_type, rounds, pain_gap, individual_validation, local_operation)
`run_shards()` runs the sessions experiment. It follows the algorithm described in chapter 5 of the thesis.

#### Model_Training.py
`Model_Training.py` contains the different learning algorithms described in chapter 5 of the thesis. The two most
important functions are:

##### federated_learning(model, global_epochs, train_data, train_labels, train_people, val_data, val_labels, val_people, val_all_labels, clients, local_epochs, individual_validation, local_operation, weights_accountant)
The `federated_learning()` function governs all federated algorithms. It iterates over a specified number of
communication rounds, and after each round computes the custom training and validation metrics, based on the algorithm
it is currently running. It also implements a custom `EarlyStopping` class, that monitors average validation loss across
clients and restores the best model weights, once training has ended.

##### train_cnn(algorithm, model, epochs, train_data, train_labels, val_data, val_labels, val_people, val_all_labels, individual_validation)
`train_cnn()` is the central training function. It implements early stopping if the algorithm is centralized, (for
federated algorithms this is handled by `federated_learning()` and allows to individually track training and validation
metrics for clients with custom callbacks.

#### Weights_Accountant.py
Finally, the `WeightsAccountant` tracks the weights of all clients in a federated setting. It performs the
Federated Averaging algorithm as well as the Federated Personalization algorithm. It also tracks all weights
in the Local Model experimental setting.
