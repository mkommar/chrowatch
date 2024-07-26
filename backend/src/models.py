from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2

def load_vgg_model():
    return VGG16(weights='imagenet', include_top=False, pooling='avg')

def load_mobilenet_model():
    return MobileNetV2(weights='imagenet', include_top=True)