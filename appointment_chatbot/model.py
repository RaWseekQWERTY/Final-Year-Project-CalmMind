import torch
import torch.nn as nn

class Attention(nn.Module):
    def __init__(self, hidden_size):
        super(Attention, self).__init__()
        self.attention_weights = nn.Linear(hidden_size, 1)

    def forward(self, encoder_outputs):
        """
        encoder_outputs: (batch_size, sequence_length, hidden_size)
        Returns:
            context_vector: (batch_size, hidden_size)
            attention_weights: (batch_size, sequence_length, 1)
        """
        # Compute attention scores
        attention_scores = self.attention_weights(encoder_outputs)  # (batch_size, sequence_length, 1)
        attention_scores = torch.tanh(attention_scores)
        attention_weights = torch.softmax(attention_scores, dim=1)  # Normalize across sequence length

        # Apply attention to encoder outputs
        context_vector = torch.sum(attention_weights * encoder_outputs, dim=1)  # (batch_size, hidden_size)
        return context_vector, attention_weights


class NeuralNetWithAttention(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(NeuralNetWithAttention, self).__init__()
        self.embedding = nn.Linear(input_size, hidden_size)  # Input embedding layer
        self.lstm = nn.LSTM(hidden_size, hidden_size, batch_first=True)  # LSTM layer
        self.attention = Attention(hidden_size)  # Attention mechanism
        self.fc = nn.Linear(hidden_size, output_size)  # Output layer

    def forward(self, x):
        """
        x: (batch_size, input_size)
        Returns:
            out: (batch_size, output_size)
        """
        # Input embedding
        embedded = self.embedding(x)  # (batch_size, hidden_size)

        # Add sequence dimension for LSTM (batch_size, 1, hidden_size)
        embedded = embedded.unsqueeze(1)

        # Pass through LSTM
        lstm_out, _ = self.lstm(embedded)  # (batch_size, 1, hidden_size)

        # Apply attention
        context_vector, _ = self.attention(lstm_out)  # (batch_size, hidden_size)

        # Fully connected layer
        out = self.fc(context_vector)  # (batch_size, output_size)
        return out