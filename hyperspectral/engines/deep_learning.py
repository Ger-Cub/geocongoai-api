import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier

class CNN1D(nn.Module):
    def __init__(self, in_channels=239, num_classes=6):
        super(CNN1D, self).__init__()
        self.features = nn.Sequential(
            nn.Conv1d(in_channels, 64, kernel_size=1),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=1),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(1)
        )
        self.classifier = nn.Linear(128, num_classes)
        
    def forward(self, x):
        x = self.features(x)
        x = x.squeeze(-1)
        return self.classifier(x)

# Example of how RF could be integrated if pre-trained models are available
class MachineLearningModel:
    def __init__(self, model_path=None):
        self.rf = RandomForestClassifier()
        # if model_path: self.load_model(model_path)
    
    def predict(self, flat_data):
        return self.rf.predict(flat_data)
