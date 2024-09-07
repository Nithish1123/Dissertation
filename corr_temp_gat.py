# -*- coding: utf-8 -*-
"""corr_temp_gat.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1tJVtnpSB9d-KDS6ZjoJo4WyzPFLhDjKl
"""

!pip install torch torchvision torchaudio torch-geometric
!pip install torch_geometric
!pip install optuna

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import yfinance as yf
import plotly.graph_objects as go
from itertools import cycle
import plotly.express as px
from scipy.stats import skew, kurtosis
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
import seaborn as sns
from sklearn.model_selection import train_test_split
import torch
from torch_geometric.utils import from_networkx
import torch.nn.functional as F
from torch_geometric.nn import GATConv, GCNConv
import torch_geometric.utils as pyg_utils
from sklearn.metrics import mean_squared_error, r2_score

# Define the stock tickers
tickers = ['^GSPC', '^GDAXI', '^FCHI', '^FTSE', '^NSEI', '^N225', '^KS11', '^HSI']

# Define the start and end dates
start_date = '2007-11-06'
end_date = '2022-06-03'

# Function to fetch historical data, reindex to complete date range, and fill missing data
def fetch_and_fill_data(symbol, start, end):
    try:
        # Fetch historical data
        data = yf.download(symbol, start=start, end=end)
        # Create a complete date range
        full_range = pd.date_range(start=start, end=end, freq='B')  # 'B' frequency is for business days
        # Reindex to the full date range
        original_data = data.copy()  # Keep a copy of the original fetched data
        data = data.reindex(full_range)
        # Forward-fill and backward-fill the missing data
        data_filled = data.ffill().bfill()
        # Count how many days the values were replaced
        filled_days_count = data_filled.notna().sum() - original_data.notna().sum()
        return data_filled, filled_days_count
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None, None

# Dictionary to store the processed data and filled days count
stock_data = {}
filled_days_counts = {}

# Fetch and fill data for each ticker
for ticker in tickers:
    data, filled_days_count = fetch_and_fill_data(ticker, start_date, end_date)
    if data is not None:
        stock_data[ticker] = data
        filled_days_counts[ticker] = filled_days_count
        # Save each DataFrame to a CSV file
        stock_data[ticker].to_csv(f"{ticker}_stock_data.csv")

# Plot the 'Close' price of each ticker in separate graphs
for ticker, data in stock_data.items():
    if data is not None:
        plt.figure(figsize=(14, 7))
        plt.plot(data.index, data['Close'], label=f'{ticker} Close Price')
        plt.title(f'{ticker} Close Price Over Time')
        plt.xlabel('Date')
        plt.ylabel('Close Price')
        plt.legend()
        plt.show()

# Print the head, total count of each processed DataFrame, and the count of filled values
for ticker, data in stock_data.items():
    if data is not None:
        print(f'Head of {ticker} data:')
        print(data.head(), '\n')
        print(f'Total count of trading days for {ticker}: {len(data)}\n')
        print(f'Count of forward-filled or backward-filled days for {ticker}:')
        print(filled_days_counts[ticker], '\n')

for ticker, data in stock_data.items():
    print(f"Ticker: {ticker}, Total number of days: {data.shape[0]}, Total number of fields: {data.shape[1]}")
# Convert the date index to datetime for each DataFrame
for ticker, data in stock_data.items():
    data.index = pd.to_datetime(data.index)

# Print the head of each DataFrame to check the conversion
for ticker, data in stock_data.items():
    print(f"Ticker: {ticker}")
    print(data.head())
    print("\n")

# Initialize an empty dictionary to store the results
ticker_close_dict = {}

# Iterate through each DataFrame in the stock_data dictionary
for ticker, data in stock_data.items():
    # Select only the 'Close' column and convert it to a Series
    ticker_close_series = data['Adj Close']
    # Store the Series in the dictionary with the ticker as the key
    ticker_close_dict[ticker] = ticker_close_series

# Print the results
for ticker, series in ticker_close_dict.items():
    print(f"Ticker: {ticker}")
    print(series.head())  # Show the first few entries for brevity
    print(f"Length: {len(series)}")
    print()

# Loop through each ticker and plot the closing prices
for ticker, series in ticker_close_dict.items():
    df = series.reset_index()
    df.columns = ['date', 'Adj Close']  # Rename columns to match the plotly naming

    fig = px.line(df, x='date', y='Adj Close', labels={'date': 'Date', 'close': 'Close Stock'})
    fig.update_traces(marker_line_width=2, opacity=0.8)
    fig.update_layout(
        title_text=f'Stock Close Price Chart for {ticker}',
        plot_bgcolor='white',
        font_size=15,
        font_color='black'
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)

    fig.show()

def calculate_realized_volatility(data: pd.DataFrame, window: int = 21) -> pd.Series:
    """
    Calculate realized volatility for the given data using squared returns.

    Parameters:
    - data: pd.DataFrame with a DateTimeIndex and 'Close' prices.
    - window: int, the rolling window size for volatility calculation.

    Returns:
    - pd.Series with realized volatility values.
    """
    # Calculate simple returns
    returns = data['Adj Close'].pct_change()

    # Square the returns
    squared_returns = returns**2

    # Calculate realized variance over the rolling window
    realized_variance = squared_returns.rolling(window=window).sum()

    # Calculate realized volatility as the square root of realized variance
    realized_volatility = np.sqrt(realized_variance)

    return realized_volatility.dropna()

# Initialize an empty dictionary to store the results
realized_vol_dict = {}

# Assume stock_data is a dictionary containing the stock data DataFrames
for ticker, data in stock_data.items():
    realized_volatility = calculate_realized_volatility(data)
    realized_vol_dict[ticker] = realized_volatility

# Print the results
for ticker, series in realized_vol_dict.items():
    print(f"Ticker: {ticker}")
    print(series.head())  # Show the first few entries for brevity
    print(f"Length: {len(series)}")
    print()

# Plot realized volatility for each ticker
for ticker, series in realized_vol_dict.items():
    df = series.reset_index()
    df.columns = ['date', 'realized_volatility']  # Rename columns to match the plotly naming

    fig = px.line(df, x='date', y='realized_volatility', labels={'date': 'Date', 'realized_volatility': 'Realized Volatility'})
    fig.update_traces(marker_line_width=2, opacity=0.8)
    fig.update_layout(
        title_text=f'Realized Volatility Chart for {ticker}',
        plot_bgcolor='white',
        font_size=15,
        font_color='black'
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)

    fig.show()

# Function to calculate descriptive statistics
def calculate_descriptive_statistics(realized_volatility: pd.Series) -> dict:
    """
    Calculate descriptive statistics for the given realized volatility series.

    Parameters:
    - realized_volatility: pd.Series containing realized volatility values.

    Returns:
    - dict with mean, standard deviation, skewness, kurtosis, and ADF test statistic and p-value.
    """
    # Calculate mean
    mean_value = realized_volatility.mean()

    # Calculate standard deviation
    std_dev = realized_volatility.std()

    # Calculate skewness
    skewness_value = skew(realized_volatility)

    # Calculate kurtosis
    kurtosis_value = kurtosis(realized_volatility, fisher=False)  # 'fisher=False' to get excess kurtosis

    # Perform Augmented Dickey-Fuller test
    adf_result = adfuller(realized_volatility.dropna())
    adf_statistic = adf_result[0]
    adf_p_value = adf_result[1]

    return {
        'Mean': mean_value,
        'Standard Deviation': std_dev,
        'Skewness': skewness_value,
        'Kurtosis': kurtosis_value,
        'ADF Statistic': adf_statistic,
        'ADF p-value': adf_p_value
    }

# Initialize a dictionary to store the descriptive statistics for each ticker
descriptive_stats_dict = {}

# Calculate descriptive statistics for each ticker's realized volatility
for ticker, series in realized_vol_dict.items():
    descriptive_stats = calculate_descriptive_statistics(series)
    descriptive_stats_dict[ticker] = descriptive_stats

# Print the descriptive statistics for each ticker
for ticker, stats in descriptive_stats_dict.items():
    print(f"Descriptive Statistics for {ticker}:")
    for stat_name, value in stats.items():
        print(f"{stat_name}: {value}")
    print()

# Initialize an empty dictionary to store the splits
data_splits = {}

# Split data into training, validation, and test sets
for ticker, realized_volatility in realized_vol_dict.items():
    # Reset the index and rename columns for ease of use
    df = realized_volatility.reset_index()
    df.columns = ['date', 'realized_volatility']

    # Split the data into training and temp (validation + test)
    train_data, temp_data = train_test_split(df, test_size=0.5, shuffle=False)

    # Split temp data into validation and test sets
    validation_data, test_data = train_test_split(temp_data, test_size=0.6, shuffle=False)

    data_splits[ticker] = {
        'train': train_data,
        'validation': validation_data,
        'test': test_data
    }

# Print the size of each split for each ticker
for ticker, splits in data_splits.items():
    print(f"Ticker: {ticker}")
    print(f"Training Set Size: {len(splits['train'])}")
    print(f"Validation Set Size: {len(splits['validation'])}")
    print(f"Test Set Size: {len(splits['test'])}")
    print()

def calculate_correlation_matrix(realized_vol_dict):
    """
    Calculate the correlation matrix based on realized volatilities.

    Parameters:
    - realized_vol_dict: dictionary of pd.Series, where each series contains realized volatilities for a ticker.

    Returns:
    - correlation_matrix: pd.DataFrame, the correlation matrix.
    """
    # Combine the realized volatilities into a single DataFrame
    combined_data = pd.DataFrame(realized_vol_dict)

    # Drop NaN values
    combined_data = combined_data.dropna()

    # Calculate the correlation matrix
    correlation_matrix = combined_data.corr()

    return correlation_matrix

# Step 1: Extract the training data for each ticker
train_realized_vol_dict = {}
for ticker, splits in data_splits.items():
    train_realized_vol_dict[ticker] = splits['train']['realized_volatility']

# Step 2: Calculate the correlation matrix using only the training data
correlation_matrix_train = calculate_correlation_matrix(train_realized_vol_dict)

# Step 3: Visualize the correlation matrix
print("Correlation Matrix (Training Data):")
print(correlation_matrix_train)

# Plot the correlation matrix as a heatmap for visualization
plt.figure(figsize=(10, 8))
plt.title("Correlation Matrix Heatmap (Training Data)")
sns.heatmap(correlation_matrix_train, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.show()

def create_correlation_graph(correlation_matrix, threshold=0.3):
    """
    Create a graph from the correlation matrix, with edges only for correlations above a certain threshold.

    Parameters:
    - correlation_matrix: pd.DataFrame, the correlation matrix.
    - threshold: float, the minimum correlation value to consider an edge.

    Returns:
    - G: networkx.Graph, the graph constructed from the correlation matrix.
    """
    # Initialize an undirected graph
    G = nx.Graph()

    # Add nodes to the graph
    for node in correlation_matrix.columns:
        G.add_node(node)

    # Add edges to the graph based on the correlation matrix
    for i, source in enumerate(correlation_matrix.columns):
        for j, target in enumerate(correlation_matrix.columns):
            if i != j:  # Avoid self-loops
                weight = correlation_matrix.iloc[i, j]
                if abs(weight) > threshold:  # Only add edges with a correlation above the threshold
                    G.add_edge(source, target, weight=weight)

    return G

G = create_correlation_graph(correlation_matrix_train)

# Step 4: Plot the correlation graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)  # Use spring layout for better node positioning
nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=3000,
        font_size=12, font_weight='bold', edge_color='gray', width=2)

# Add edge labels with weights
edge_labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

plt.title('Correlation Graph (Training Data)')
plt.show()

# Step 5: Repeat the process for the test and validation data

# Extract the test and validation data for each ticker
test_realized_vol_dict = {}
validation_realized_vol_dict = {}

for ticker, splits in data_splits.items():
    test_realized_vol_dict[ticker] = splits['test']['realized_volatility']
    validation_realized_vol_dict[ticker] = splits['validation']['realized_volatility']

# Calculate the correlation matrix for the test data
correlation_matrix_test = calculate_correlation_matrix(test_realized_vol_dict)

# Visualize the correlation matrix for the test data
print("Correlation Matrix (Test Data):")
print(correlation_matrix_test)

# Plot the correlation matrix as a heatmap for visualization (Test Data)
plt.figure(figsize=(10, 8))
plt.title("Correlation Matrix Heatmap (Test Data)")
sns.heatmap(correlation_matrix_test, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.show()

# Create and plot the correlation graph for the test data
G_test = create_correlation_graph(correlation_matrix_test)

plt.figure(figsize=(12, 8))
pos_test = nx.spring_layout(G_test)  # Use spring layout for better node positioning
nx.draw(G_test, pos_test, with_labels=True, node_color='lightgreen', node_size=3000,
        font_size=12, font_weight='bold', edge_color='gray', width=2)

# Add edge labels with weights (Test Data)
edge_labels_test = nx.get_edge_attributes(G_test, 'weight')
nx.draw_networkx_edge_labels(G_test, pos_test, edge_labels=edge_labels_test, font_size=10)

plt.title('Correlation Graph (Test Data)')
plt.show()

# Step 6: Repeat the process for the validation data
correlation_matrix_validation = calculate_correlation_matrix(validation_realized_vol_dict)

# Visualize the correlation matrix for the validation data
print("Correlation Matrix (Validation Data):")
print(correlation_matrix_validation)

# Plot the correlation matrix as a heatmap for visualization (Validation Data)
plt.figure(figsize=(10, 8))
plt.title("Correlation Matrix Heatmap (Validation Data)")
sns.heatmap(correlation_matrix_validation, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.show()

# Create and plot the correlation graph for the validation data
G_validation = create_correlation_graph(correlation_matrix_validation)

plt.figure(figsize=(12, 8))
pos_validation = nx.spring_layout(G_validation)  # Use spring layout for better node positioning
nx.draw(G_validation, pos_validation, with_labels=True, node_color='lightcoral', node_size=3000,
        font_size=12, font_weight='bold', edge_color='gray', width=2)

# Add edge labels with weights (Validation Data)
edge_labels_validation = nx.get_edge_attributes(G_validation, 'weight')
nx.draw_networkx_edge_labels(G_validation, pos_validation, edge_labels=edge_labels_validation, font_size=10)

plt.title('Correlation Graph (Validation Data)')
plt.show()

def networkx_to_pyg_data(G, realized_vol_dict):
    """
    Convert a NetworkX directed graph and realized volatility dictionary
    into PyTorch Geometric Data format.

    Parameters:
    - G: networkx.DiGraph, the directed graph.
    - realized_vol_dict: dictionary of pd.Series, realized volatility for each node.

    Returns:
    - data: torch_geometric.data.Data, graph data suitable for GNN.
    """
    # Convert NetworkX graph to PyTorch Geometric Data object
    data = from_networkx(G)

    # Add node features from realized volatility
    node_features = []
    for node in G.nodes():
        vol_series = realized_vol_dict[node].values
        node_features.append(torch.tensor(vol_series, dtype=torch.float).view(-1, 1))

    # Convert node features list to a tensor and assign to data.x
    data.x = torch.cat(node_features, dim=1)

    return data

# Convert the training and validation graphs
train_data = networkx_to_pyg_data(G, train_realized_vol_dict)
validation_data = networkx_to_pyg_data(G_validation, validation_realized_vol_dict)
test_data = networkx_to_pyg_data(G_test, test_realized_vol_dict)

class TemporalGATModel(torch.nn.Module):
    def __init__(self, node_feature_dim, hidden_dim, num_heads):
        super(TemporalGATModel, self).__init__()
        # Layer 1: GCN
        self.gcn1 = GCNConv(node_feature_dim, hidden_dim)
        self.gcn2 = GCNConv(hidden_dim, hidden_dim)

        # Layer 2: GAT
        self.gat1 = GATConv(hidden_dim, hidden_dim, heads=num_heads, concat=False)
        self.gat2 = GATConv(hidden_dim, hidden_dim, heads=num_heads, concat=False)

        # Additional Fully Connected Layers
        self.fc1 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = torch.nn.Linear(hidden_dim, hidden_dim)

        # Final Prediction Layer
        self.fc_final = torch.nn.Linear(hidden_dim, 1)

    def forward(self, data):
        # GCN layers to aggregate neighborhood information
        x = self.gcn1(data.x, data.edge_index)
        x = F.relu(x)
        x = self.gcn2(x, data.edge_index)
        x = F.relu(x)

        # GAT layers to focus on important nodes
        x = self.gat1(x, data.edge_index)
        x = F.relu(x)
        x = self.gat2(x, data.edge_index)
        x = F.relu(x)

        # Fully Connected layers
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x = F.relu(x)
        x = self.fc3(x)
        x = F.relu(x)

        # Final output layer (predict future values, e.g., volatility)
        out = self.fc_final(x)
        return out

# Hyperparameters
node_feature_dim = train_data.x.shape[1]  # Number of features per node
hidden_dim = 32
num_heads = 8

model = TemporalGATModel(node_feature_dim, hidden_dim, num_heads)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = torch.nn.MSELoss()

# Initialize lists to store the loss values
train_loss_values = []
validation_loss_values = []

# Training loop with loss recording
model.train()
num_epochs = 70

for epoch in range(num_epochs):
    optimizer.zero_grad()

    # Forward pass for training data
    out = model(train_data)

    # Compute the loss for training data
    loss = criterion(out[:-1], train_data.x[1:])

    # Backward pass and optimization
    loss.backward()
    optimizer.step()

    # Store the training loss
    train_loss_values.append(loss.item())

    # Print the loss every 10 epochs
    if epoch % 10 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item()}")

# Evaluation phase for validation data
model.eval()
with torch.no_grad():
    validation_out = model(validation_data)
    validation_loss = criterion(validation_out[:-1], validation_data.x[1:])
    validation_loss_values.append(validation_loss.item())
    print(f"Validation Loss: {validation_loss.item()}")

# Visualization of the loss function over epochs
plt.figure(figsize=(10, 6))
plt.plot(range(num_epochs), train_loss_values, label='Training Loss')
plt.plot(range(num_epochs), validation_loss_values * num_epochs, label='Validation Loss', linestyle='--')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss Function Over Epochs')
plt.legend()
plt.grid(True)
plt.show()

import torch
import torch.nn as nn
import torch.nn.functional as F
import itertools
import matplotlib.pyplot as plt
from torch_geometric.nn import GCNConv, GATConv

class TemporalGATModel(torch.nn.Module):
    def __init__(self, node_feature_dim, hidden_dim, num_heads):
        super(TemporalGATModel, self).__init__()
        # Layer 1: GCN
        self.gcn1 = GCNConv(node_feature_dim, hidden_dim)
        self.gcn2 = GCNConv(hidden_dim, hidden_dim)

        # Layer 2: GAT
        self.gat1 = GATConv(hidden_dim, hidden_dim, heads=num_heads, concat=False)
        self.gat2 = GATConv(hidden_dim, hidden_dim, heads=num_heads, concat=False)

        # Additional Fully Connected Layers
        self.fc1 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = torch.nn.Linear(hidden_dim, hidden_dim)

        # Final Prediction Layer
        self.fc_final = torch.nn.Linear(hidden_dim, 1)

    def forward(self, data):
        # GCN layers to aggregate neighborhood information
        x = self.gcn1(data.x, data.edge_index)
        x = F.relu(x)
        x = self.gcn2(x, data.edge_index)
        x = F.relu(x)

        # GAT layers to focus on important nodes
        x = self.gat1(x, data.edge_index)
        x = F.relu(x)
        x = self.gat2(x, data.edge_index)
        x = F.relu(x)

        # Fully Connected layers
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x = F.relu(x)
        x = self.fc3(x)
        x = F.relu(x)

        # Final output layer (predict future values, e.g., volatility)
        out = self.fc_final(x)
        return out

# Define the ranges of hyperparameters for the grid search
hidden_dim_values = [32, 64, 128]
num_heads_values = [4, 8]
learning_rate_values = [0.0001, 0.001, 0.01]

# Create a list of all possible combinations
param_combinations = list(itertools.product(hidden_dim_values, num_heads_values, learning_rate_values))

best_val_loss = float('inf')
best_params = None
all_train_loss_values = []
all_validation_loss_values = []

# Grid search loop
for params in param_combinations:
    hidden_dim, num_heads, lr = params

    model = TemporalGATModel(node_feature_dim=train_data.x.shape[1], hidden_dim=hidden_dim, num_heads=num_heads)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.MSELoss()

    train_loss_values = []
    validation_loss_values = []
    num_epochs = 70
    for epoch in range(num_epochs):
        model.train()
        optimizer.zero_grad()
        out = model(train_data)
        loss = criterion(out[:-1], train_data.x[1:])
        loss.backward()
        optimizer.step()
        train_loss_values.append(loss.item())

        # Validation phase
        model.eval()
        with torch.no_grad():
            validation_out = model(validation_data)
            validation_loss = criterion(validation_out[:-1], validation_data.x[1:])
            validation_loss_values.append(validation_loss.item())

        if epoch % 10 == 0:
            print(f"Epoch {epoch}, Training Loss: {loss.item()}, Validation Loss: {validation_loss.item()}")

    all_train_loss_values.append(train_loss_values)
    all_validation_loss_values.append(validation_loss_values)

    final_val_loss = validation_loss_values[-1]

    # Track the best hyperparameters
    if final_val_loss < best_val_loss:
        best_val_loss = final_val_loss
        best_params = params

# Plotting the loss functions for the best configuration
best_index = param_combinations.index(best_params)

plt.figure(figsize=(12, 6))
plt.plot(range(num_epochs), all_train_loss_values[best_index], label='Training Loss', color='blue')
plt.plot(range(num_epochs), all_validation_loss_values[best_index], label='Validation Loss', color='red')
plt.title('Training and Validation Loss Over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.show()

print(f"Best Hyperparameters: Hidden Dim: {best_params[0]}, Num Heads: {best_params[1]}, Learning Rate: {best_params[2]}")

def calculate_metrics_for_all_indices(actuals, predictions, h):
    """
    Calculate evaluation metrics (MAFE, MSE, RMSE, MAPE, R²) for each index at a given horizon h.

    Parameters:
    - actuals: Tensor, actual values with shape [T, num_indices].
    - predictions: Tensor, predicted values with shape [T-h, num_indices] or [T-h, 1].
    - h: int, forecasting horizon.

    Returns:
    - dict of metrics for each index.
    """
    T = actuals.shape[0]  # Total number of actual data points available
    if predictions.shape[0] > T - h:
        predictions = predictions[:T - h]  # Adjust predictions to match the actual data available
    actuals = actuals[h:]  # Shift actuals to start at the horizon

    # Dictionary to store metrics for each index
    metrics_results = {}

    # Calculate metrics for each index
    for idx in range(actuals.shape[1]):  # Iterate over each index
        actual = actuals[:, idx]
        prediction = predictions[:, idx] if predictions.shape[1] > 1 else predictions.view(-1)

        # Calculate metrics
        mafe = torch.mean(torch.abs(prediction - actual)).item()
        mse = F.mse_loss(prediction, actual).item()
        rmse = torch.sqrt(F.mse_loss(prediction, actual)).item()
        mape = (torch.mean(torch.abs((actual - prediction) / actual)) * 100).item()
        ss_res = torch.sum((actual - prediction) ** 2).item()
        ss_tot = torch.sum((actual - torch.mean(actual)) ** 2).item()
        r2 = 1 - (ss_res / ss_tot)

        # Store metrics for the current index
        metrics_results[f"Index {idx+1}"] = {
            "MAFE": mafe,
            "MSE": mse,
            "RMSE": rmse,
            "MAPE": mape
        }

    return metrics_results

# Simulated Actuals
validation_targets = validation_data.x

# Simulated Predictions from your model
model.eval()
with torch.no_grad():
    validation_out = model(validation_data)

# Calculate metrics for each forecasting horizon for all indices
horizons = [1, 5, 10, 22]
metrics_results_per_horizon = {}

for h in horizons:
    metrics_results = calculate_metrics_for_all_indices(validation_targets, validation_out, h)
    metrics_results_per_horizon[f"Metrics for horizon {h}"] = metrics_results

# Print results in the desired format
for horizon, metrics_by_index in metrics_results_per_horizon.items():
    print(f"Metrics for horizon {horizon}:")
    print(f"  {'Index':<8} {'MAFE':<10} {'MSE':<10} {'RMSE':<10} {'MAPE':<12}")
    for index, metrics in metrics_by_index.items():
        print(f"{index:<8} {metrics['MAFE']:<10.6f} {metrics['MSE']:<10.6f} {metrics['RMSE']:<10.6f} {metrics['MAPE']:<12.6f} ")

