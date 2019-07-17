import os
import pickle

import numpy as np
import tensorflow as tf

from Scripts import Print_Functions as Output

ROOT = os.path.dirname(os.path.dirname(__file__))
AUTISM = os.path.join(ROOT, 'Data', 'Autism')


def unison_shuffled_copies(a, b):
    assert len(a) == len(b)
    p = np.random.permutation(len(a))
    return a[p], b[p]


def get_pickle_files(directory):
    files = []
    for file in os.listdir(directory):
        if file.endswith(".pkl"):
            files.append(os.path.join(directory, file))
    files = sorted(files)
    return files


def load_pickle(file_name):
    with open(file_name, 'rb') as f:
        file = pickle.load(f)
    return file


def prepare_autism_data(file):
    frame_number_col = 5
    splits = 6, 257, 327, 354, 378, 393

    frames = file[frame_number_col]
    offset_file = file[:, splits[0]:]
    face = np.expand_dims(offset_file[:, :splits[1]], axis=0)
    body = np.expand_dims(offset_file[:, splits[1]:splits[2]], axis=0)
    phy = np.expand_dims(offset_file[:, splits[2]:splits[3]], axis=0)
    audio = np.expand_dims(offset_file[:, splits[3]:splits[4]], axis=0)
    cars = np.expand_dims(offset_file[:, splits[4]:splits[5]], axis=0)
    labels = np.expand_dims(offset_file[:, -1:], axis=0)
    return frames, face, body, phy, audio, cars, labels


def load_autism_data_into_clients(folder_path):
    files = get_pickle_files(folder_path)
    clients_frames, clients_face, clients_body, clients_phy, clients_audio, clients_cars, clients_labels = \
        [], [], [], [], [], [], []

    for file_name in files:
        file = load_pickle(file_name)
        frames, face, body, phy, audio, cars, labels = prepare_autism_data(file)
        clients_frames.append(frames)
        clients_face.append(face)
        clients_body.append(body)
        clients_phy.append(phy)
        clients_audio.append(audio)
        clients_cars.append(cars)
        clients_labels.append(labels)
    return clients_frames, clients_face, clients_body, clients_phy, clients_audio, clients_cars, clients_labels


def train_test_split(features, labels, test_split=0.25, shuffle=False):
    if shuffle:
        features, labels = unison_shuffled_copies(features, labels)
    split_point = int(len(features) * test_split)
    train_data = features[split_point:]
    test_data = features[:split_point]
    train_labels = features[split_point:]
    test_labels = features[:split_point]
    return train_data, train_labels, test_data, test_labels


def load_mnist_data():
    """
    Loads the MNIST Data Set and reshapes it for further model training

    :return:
        train_images        numpy array of shape (60000, 28, 28, 1)
        train_labels        numpy array of shape (60000, )
        test_images         numpy array of shape (10000, 28, 28, 1)
        test_labels         numpy array of shape (10000, )
    """

    (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.mnist.load_data()

    train_images = train_images.reshape((60000, 28, 28, 1))
    test_images = test_images.reshape((10000, 28, 28, 1))

    # Normalize pixel values to be between 0 and 1
    train_images, test_images = train_images / 255.0, test_images / 255.0

    return train_images, train_labels, test_images, test_labels


def split_by_label(data, labels):
    split_data = [data[labels == label] for label in np.unique(labels).tolist()]
    split_labels = [labels[labels == label] for label in np.unique(labels).tolist()]
    return split_data, split_labels


def allocate_data(num_clients, split_data, split_labels, categories_per_client, data_points_per_category):
    clients = []
    labels = []
    it = 0
    for idx in range(num_clients):
        client = []
        label = []
        for _ in range(categories_per_client):
            choice_arr = np.random.choice(split_data[it % len(split_data)].shape[0], data_points_per_category)
            client.append(split_data[it % len(split_data)][choice_arr, :])
            label.append(split_labels[it % len(split_labels)][choice_arr])
            it += 1
        client = np.concatenate(client)
        label = np.concatenate(label)
        client, label = unison_shuffled_copies(client, label)
        clients.append(client)
        labels.append(label)
    return clients, labels


def load_autism_data_body():
    clients = load_autism_data_into_clients(AUTISM)
    return clients[2], clients[-1]


def load_data(dataset):
    # Load data
    if dataset == "MNIST":
        train_data, train_labels, test_data, test_labels = load_mnist_data()
    else:
        Output.eprint("No data-set named {}. Loading MNIST instead.".format(dataset))
        train_data, train_labels, test_data, test_labels = load_mnist_data()
        dataset = "MNIST"

    train_data = train_data.astype('float32')
    train_labels = train_labels.astype('float32')
    test_data = test_data.astype('float32')
    test_labels = test_labels.astype('float32')
    return train_data, train_labels, test_data, test_labels, dataset


def sort_data(data, labels):
    sort_array = np.argsort(labels)
    data = data[sort_array]
    labels = labels[sort_array]
    return data, labels


def split_train_data(num_of_clients, train_data, train_labels):
    """
    Splits a dataset into a provided number of clients to simulate a "federated" setting

    :param num_of_clients:          integer specifying the number of clients the data should be split into
    :param train_data:              numpy array
    :param train_labels:            numpy array

    :return:
        train_data:                 numpy array (with additional dimension for N clients)
        train_labels:               numpy array (with additional dimension for N clients)
    """

    # Split data into twice as many shards as clients
    train_data = np.array_split(train_data, num_of_clients * 2)
    train_labels = np.array_split(train_labels, num_of_clients * 2)

    # Shuffle shards so that for sorted data, shards with different labels are adjacent
    train = list(zip(train_data, train_labels))
    np.random.shuffle(train)
    train_data, train_labels = zip(*train)

    # Concatenate adjacent shards
    train_data = [np.concatenate(train_data[i:i+2]) for i in range(0, len(train_data), 2)]
    train_labels = [np.concatenate(train_labels[i:i+2]) for i in range(0, len(train_labels), 2)]

    return train_data, train_labels


def split_data_into_clients(clients, split, train_data, train_labels):
    """
    Utility function to split train data and labels into a specified number of clients, in accordance with a specified
    type of split.

    :param clients:                     int, number of clients the data needs to be split into
    :param split:                       string, type of split that should be performed
    :param train_data:                  numpy array, train data
    :param train_labels:                numpy array, train_labels
    :return:
        train_data                      list of numpy arrays, train_data, split into clients
        train_labels                    list of numpy arrays, train_labels, split into clients
    """

    assert len(train_data) == len(train_labels)

    # Split data
    if split.lower() == 'random':
        train_data, train_labels = split_train_data(clients, train_data, train_labels)
    elif split.lower() == 'overlap':
        train_data, train_labels = sort_data(train_data, train_labels)
        train_data, train_labels = split_train_data(clients, train_data, train_labels)
        for idx in range(len(train_data)):
            train_data[idx], train_labels[idx] = unison_shuffled_copies(train_data[idx], train_labels[idx])
    elif split.lower() == 'no_overlap':
        split_data, split_labels = split_by_label(train_data, train_labels)
        train_data, train_labels = allocate_data(clients,
                                                 split_data,
                                                 split_labels,
                                                 categories_per_client=2,
                                                 data_points_per_category=int(
                                                     len(train_data) / (clients * 2)))
    else:
        raise ValueError(
            "Invalid value for 'Split'. Value can be 'random', 'overlap', 'no_overlap', value was: {}".format(split))
    return train_data, train_labels
