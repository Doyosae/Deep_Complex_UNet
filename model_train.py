import os, argparse
from model_module import *

from model import *
from model_loss import *
from model_data import *

from complex_layers.STFT import *
from complex_layers.networks import *
from complex_layers.activations import *

device_lib.list_local_devices()
print(tf.config.list_physical_devices())
print("GPU Available: ", tf.test.is_gpu_available('GPU'))

def data_generator(train_arguments, test_arguments):

      train_generator = datagenerator(**train_arguments)
      test_generator  = datagenerator(**test_arguments)

      return train_generator, test_generator


def model_train(model, optimizer, total_epochs, train_generator, test_generator):

      for epoch in range (total_epochs):

            train_batch_losses = 0
            test_batch_losses  = 0

            'Training Loop'
            for index, (train_noisy_speech, train_clean_speech) in enumerate(train_generator):
                  
                  with tf.GradientTape() as tape:
                        train_predict_speech = model(train_noisy_speech)
                        train_loss = weighted_SDR_loss(train_noisy_speech, train_predict_speech, train_clean_speech)
                  
                  gradients = tape.gradient(train_loss, model.trainable_variables)
                  optimizer.apply_gradients(zip(gradients, model.trainable_variables))
                  train_batch_losses = train_batch_losses + train_loss

            'Test Loop'
            for index, (test_noisy_speech, test_clean_speech) in enumerate(test_generator):
                  test_predict_speech = model(test_noisy_speech)
                  test_loss = weighted_SDR_loss(test_noisy_speech, test_predict_speech, test_clean_speech)
                  test_batch_losses = test_batch_losses + test_loss

            train_loss_per_epoch = train_batch_losses / train_steps
            test_loss_per_epoch  = test_batch_losses / test_steps

            templet = "Epoch : {:3d},     TRAIN LOSS : {:.5f},     TEST LOSS  :  {:.5}"
            print(templet.format(epoch+1, train_loss_per_epoch, test_loss_per_epoch))

      model.save_weights("./model_save/" + model_type + str(index+1) + ".h5")



if __name__ == "__main__":

      parser = argparse.ArgumentParser(description = 'SETTING OPTION')
      parser.add_argument("--model", type = str, defualt = "dcunet20", help = "Input model tpe")
      parser.add_argument("--epoch", type = int, default = 500, help = "Input epochs")
      parser.add_argument("--batch", type = int, default = 128, help = "Input batch size")
      parser.add_argument("--optim", type = str, default = "adam", help = "Input optimizer option")
      parser.add_argument("--lr",    type = float)
      parser.add_argument("--trn", type = str, default = "./datasets/train_noisy/", help = "Input train noisy path")
      parser.add_argument("--tec", type = str, default = "./datasets/train_clean/", help = "Input train clean phat")
      parser.add_argument("--ten", type = str, default = "./datasets/test_noisy/",  help = "Input test noisy path")
      parser.add_argument("--tec", type = str, default = "./datasets/test_clean/",  help = "Input test clean path")
      args = parser.parse_args()

      model_type     = args.model
      total_epochs   = args.epoch
      batch_size     = args.batch
      optimizer_type = args.optim
      learning_rate  = args.lr


      train_noisy_path = args.trn
      train_clean_path = args.tec
      test_noisy_path  = args.ten
      test_clean_path  = args.tec


train_arguments = {"inputs_ids" : os.listdir(train_noisy_path), 
                   "outputs_ids" : os.listdir(train_clean_path),
                   "inputs_dir" : train_noisy_path, 
                   "outputs_dir" : train_clean_path,
                   "batch_size" : batch_size}
test_arguments  = {"inputs_ids" : os.listdir(test_noisy_path), 
                   "outputs_ids" : os.listdir(test_clean_path),
                   "inputs_dir" : test_noisy_path,
                   "outputs_dir" : test_clean_path,
                   "batch_size" : batch_size}

train_generator, test_generator = data_generator(train_arguments = train_arguments, test_arguments = test_arguments)

train_steps = len(os.listdir(train_noisy_path)) // batch_size
test_steps  = len(os.listdir(test_noisy_path)) // batch_size
print("TRAIN STEPS, TEST STEPS   ", train_steps, test_steps)


if model_type == "dcunet16":
      call_model = Naive_DCUnet_16(norm_trainig = True).model()
      call_model.summary()

if optimizer_type == "adam":
      learning_rate_scheduling = schedules.ExponentialDecay(initial_learning_rate = learning_rate, decay_steps = 100000, decay_rate = 0.98)
      optimizer = tf.keras.optimizers.Adam(learning_rate = learning_rate_scheduling, beta_1 = 0.9)

model_train(call_model, optimizer, total_epochs, train_generator, test_generator)