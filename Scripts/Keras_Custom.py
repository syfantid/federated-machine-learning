import tensorflow as tf


def weighted_loss(y_true, y_pred):
    weights = 1 / 0.2
    return tf.nn.weighted_cross_entropy_with_logits(y_true, y_pred, weights)


def TP(y_true, y_pred):
    y_pred = tf.argmax(y_pred, 1)
    y_true = tf.argmax(y_true, 1)
    return tf.math.count_nonzero(y_pred * y_true)


def FP(y_true, y_pred):
    y_pred = tf.argmax(y_pred, 1)
    y_true = tf.argmax(y_true, 1)
    return tf.math.count_nonzero(y_pred * (y_true - 1))


def TN(y_true, y_pred):
    y_pred = tf.argmax(y_pred, 1)
    y_true = tf.argmax(y_true, 1)
    return tf.math.count_nonzero((y_pred - 1) * (y_true - 1))


def FN(y_true, y_pred):
    y_pred = tf.argmax(y_pred, 1)
    y_true = tf.argmax(y_true, 1)
    return tf.math.count_nonzero((y_pred - 1) * y_true)


def conf_matrix(y_true, y_pred):
    return TP(y_true, y_pred), FP(y_true, y_pred), TN(y_true, y_pred), FN(y_true, y_pred)


def epoch_acc(y_true, y_pred):
    tp, fp, tn, fn = conf_matrix(y_true, y_pred)
    return (tp + tn) / (tp + fp + tn + fn)


def recall(y_true, y_pred):
    tp, fp, tn, fn = conf_matrix(y_true, y_pred)
    return tp / (fn + tp)


def precision(y_true, y_pred):
    tp, fp, tn, fn = conf_matrix(y_true, y_pred)
    return tp / (fp + tp)


def f1_score(y_true, y_pred):
    p = precision(y_true, y_pred)
    r = recall(y_true, y_pred)
    return 2 * (p * r) / (p + r)


class EarlyStopping:
    def __init__(self, patience):
        self.patience = patience
        self.stopping_metric = []
        self.weights = []

    def __call__(self, model, metric):
        if len(self.stopping_metric) == 0:
            pass
        elif min(self.stopping_metric) > metric:
            self.stopping_metric.clear()
            self.weights.clear()
        self.stopping_metric.append(metric)
        self.weights.append(model.get_weights())
        return True if len(self.stopping_metric) > self.patience else False

    def return_best_model(self, model):
        print("Restoring best model weights.")
        return model.set_weights(self.weights[0])


class AdditionalValidationSets(tf.keras.callbacks.Callback):
    def __init__(self, validation_sets, verbose=1, batch_size=None):
        """
        :param validation_sets:
        a list of 3-tuples (validation_data, validation_targets, validation_set_name)
        or 4-tuples (validation_data, validation_targets, sample_weights, validation_set_name)
        :param verbose:
        verbosity mode, 1 or 0
        :param batch_size:
        batch size to be used when evaluating on the additional datasets
        """
        super(AdditionalValidationSets, self).__init__()
        self.validation_sets = validation_sets
        for validation_set in self.validation_sets:
            if len(validation_set) not in [2, 3]:
                raise ValueError()
        self.epoch = []
        self.history = {}
        self.verbose = verbose
        self.batch_size = batch_size

    def on_train_begin(self, logs=None):
        self.epoch = []
        self.history = {}

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        self.epoch.append(epoch)

        # record the same values as History() as well
        for k, v in logs.items():
            self.history.setdefault(k, []).append(v)

        # evaluate on the additional validation sets
        for validation_set in self.validation_sets:
            if len(validation_set) == 3:
                validation_data, validation_targets, validation_set_name = validation_set
                sample_weights = None
            elif len(validation_set) == 4:
                validation_data, validation_targets, sample_weights, validation_set_name = validation_set
            else:
                raise ValueError()

            results = self.model.evaluate(x=validation_data,
                                          y=validation_targets,
                                          verbose=self.verbose,
                                          sample_weight=sample_weights,
                                          batch_size=self.batch_size)

            for i, result in enumerate(results):
                if i == 0:
                    valuename = validation_set_name + '_loss'
                else:
                    valuename = validation_set_name + '_' + self.model.metrics[i-1].name
                self.history.setdefault(valuename, []).append(result)
