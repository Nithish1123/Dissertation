# -*- coding: utf-8 -*-
"""GNN_GAT.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1A3redluKN2mUV8Vjam55sJ5MdocJNGJw
"""

!pip install torch torchvision torchaudio torch-geometric
!pip install torch_geometric

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

# Function to calculate the spillover index using Diebold and Yilmaz methodology
def calculate_spillover_index(realized_vol_dict, lag_order=2, forecast_horizon=10):
    """
    Calculate the volatility spillover index using the Diebold-Yilmaz methodology.

    Parameters:
    - realized_vol_dict: dictionary of pd.Series, where each series contains realized volatilities for a ticker.
    - lag_order: int, the lag order for the VAR model.
    - forecast_horizon: int, the forecast horizon for the variance decomposition.

    Returns:
    - spillover_index: pd.DataFrame, the spillover index matrix.
    """
    # Combine the realized volatilities into a single DataFrame
    combined_data = pd.DataFrame(realized_vol_dict)

    # Drop NaN values
    combined_data = combined_data.dropna()

    # Fit VAR model
    model = VAR(combined_data)
    var_result = model.fit(lag_order)

    # Perform variance decomposition
    fevd = var_result.fevd(forecast_horizon)

    # Initialize spillover matrix
    spillover_matrix = np.zeros((len(realized_vol_dict), len(realized_vol_dict)))

    # Populate the spillover matrix
    for i in range(len(realized_vol_dict)):
        for j in range(len(realized_vol_dict)):
            if i != j:
                spillover_matrix[i, j] = fevd.decomp[j][:, i].sum() / fevd.decomp[j].sum()

    # Create a DataFrame for better readability
    spillover_index = pd.DataFrame(spillover_matrix, index=realized_vol_dict.keys(), columns=realized_vol_dict.keys())

    return spillover_index * 100  # Convert to percentage

# Step 1: Extract the training data for each ticker
train_realized_vol_dict = {}
for ticker, splits in data_splits.items():
    train_realized_vol_dict[ticker] = splits['train']['realized_volatility']

# Step 2: Calculate the spillover index using only the training data
spillover_index_train = calculate_spillover_index(train_realized_vol_dict)

# Step 3: Visualize the spillover index matrix
print("Spillover Index Matrix (Training Data):")
print(spillover_index_train)

# Calculate the total spillover index for the training data
total_spillover_index_train = spillover_index_train.to_numpy().sum() / (len(train_realized_vol_dict) ** 2 - len(train_realized_vol_dict))
print(f"\nTotal Spillover Index (Training Data): {total_spillover_index_train:.2f}%")

# Plot the spillover matrix as a heatmap for visualization
plt.figure(figsize=(10, 8))
plt.title("Volatility Spillover Index Heatmap (Training Data)")
sns.heatmap(spillover_index_train, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.show()

def create_spillover_graph(spillover_matrix):
    """
    Create a directed graph from the spillover matrix.

    Parameters:
    - spillover_matrix: pd.DataFrame, the spillover index matrix.

    Returns:
    - G: networkx.DiGraph, the directed graph constructed from the spillover matrix.
    """
    # Initialize a directed graph
    G = nx.DiGraph()

    # Add nodes to the graph
    for node in spillover_matrix.columns:
        G.add_node(node)

    # Add edges to the graph based on the spillover matrix
    for i, source in enumerate(spillover_matrix.columns):
        for j, target in enumerate(spillover_matrix.columns):
            if i != j:  # Avoid self-loops
                weight = spillover_matrix.iloc[i, j]
                if weight > 0:  # Only add edges with a positive weight
                    G.add_edge(source, target, weight=weight)

    return G

G = create_spillover_graph(spillover_index_train)

# Step 4: Plot the spillover graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)  # Use spring layout for better node positioning
nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=3000,
        font_size=12, font_weight='bold', edge_color='gray', width=2)

# Add edge labels with weights
edge_labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

plt.title('Volatility Spillover Directed Graph (Training Data)')
plt.show()

# Step 1: Extract the test and validation data for each ticker
test_realized_vol_dict = {}
validation_realized_vol_dict = {}

for ticker, splits in data_splits.items():
    test_realized_vol_dict[ticker] = splits['test']['realized_volatility']
    validation_realized_vol_dict[ticker] = splits['validation']['realized_volatility']

# Step 2: Calculate the spillover index for the test data
spillover_index_test = calculate_spillover_index(test_realized_vol_dict)

# Step 3: Visualize the spillover index matrix for the test data
print("Spillover Index Matrix (Test Data):")
print(spillover_index_test)

# Calculate the total spillover index for the test data
total_spillover_index_test = spillover_index_test.to_numpy().sum() / (len(test_realized_vol_dict) ** 2 - len(test_realized_vol_dict))
print(f"\nTotal Spillover Index (Test Data): {total_spillover_index_test:.2f}%")

# Plot the spillover matrix as a heatmap for visualization (Test Data)
plt.figure(figsize=(10, 8))
plt.title("Volatility Spillover Index Heatmap (Test Data)")
sns.heatmap(spillover_index_test, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.show()

# Step 4: Create and plot the spillover graph for the test data
G_test = create_spillover_graph(spillover_index_test)

plt.figure(figsize=(12, 8))
pos_test = nx.spring_layout(G_test)  # Use spring layout for better node positioning
nx.draw(G_test, pos_test, with_labels=True, node_color='lightgreen', node_size=3000,
        font_size=12, font_weight='bold', edge_color='gray', width=2)

# Add edge labels with weights (Test Data)
edge_labels_test = nx.get_edge_attributes(G_test, 'weight')
nx.draw_networkx_edge_labels(G_test, pos_test, edge_labels=edge_labels_test, font_size=10)

plt.title('Volatility Spillover Directed Graph (Test Data)')
plt.show()

# Step 5: Repeat the process for the validation data
spillover_index_validation = calculate_spillover_index(validation_realized_vol_dict)

# Visualize the spillover index matrix for the validation data
print("Spillover Index Matrix (Validation Data):")
print(spillover_index_validation)

# Calculate the total spillover index for the validation data
total_spillover_index_validation = spillover_index_validation.to_numpy().sum() / (len(validation_realized_vol_dict) ** 2 - len(validation_realized_vol_dict))
print(f"\nTotal Spillover Index (Validation Data): {total_spillover_index_validation:.2f}%")

# Plot the spillover matrix as a heatmap for visualization (Validation Data)
plt.figure(figsize=(10, 8))
plt.title("Volatility Spillover Index Heatmap (Validation Data)")
sns.heatmap(spillover_index_validation, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.show()

# Step 6: Create and plot the spillover graph for the validation data
G_validation = create_spillover_graph(spillover_index_validation)

plt.figure(figsize=(12, 8))
pos_validation = nx.spring_layout(G_validation)  # Use spring layout for better node positioning
nx.draw(G_validation, pos_validation, with_labels=True, node_color='lightcoral', node_size=3000,
        font_size=12, font_weight='bold', edge_color='gray', width=2)

# Add edge labels with weights (Validation Data)
edge_labels_validation = nx.get_edge_attributes(G_validation, 'weight')
nx.draw_networkx_edge_labels(G_validation, pos_validation, edge_labels=edge_labels_validation, font_size=10)

plt.title('Volatility Spillover Directed Graph (Validation Data)')
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

class GCN_GAT_Model(torch.nn.Module):
    def __init__(self, node_feature_dim, hidden_dim, num_heads, num_layers=2):
        super(GCN_GAT_Model, self).__init__()
        self.num_layers = num_layers
        self.gcn_layers = torch.nn.ModuleList()
        self.gat_layers = torch.nn.ModuleList()

        # Initialize the first GCN layer
        self.gcn_layers.append(GCNConv(node_feature_dim, hidden_dim))

        # Add additional GCN layers
        for _ in range(1, num_layers):
            self.gcn_layers.append(GCNConv(hidden_dim, hidden_dim))

        # Add GAT layers
        for _ in range(num_layers):
            self.gat_layers.append(GATConv(hidden_dim, hidden_dim, heads=num_heads, concat=False))

        # Fully connected layer for output, modified to output 8 features
        self.fc = torch.nn.Linear(hidden_dim, 8)  # Change output features from 1 to 8

        # Dropout layer (optional)
        self.dropout = torch.nn.Dropout(p=0.5)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index

        # Apply GCN layers with ReLU and optional dropout
        for gcn in self.gcn_layers:
            x = gcn(x, edge_index)
            x = F.relu(x)
            x = self.dropout(x)  # Apply dropout after activation

        # Apply GAT layers with ReLU and optional dropout
        for gat in self.gat_layers:
            x = gat(x, edge_index)
            x = F.relu(x)
            x = self.dropout(x)  # Apply dropout after activation

        # Generate predictions for each node
        out = self.fc(x)
        return out

# Hyperparameters
node_feature_dim = train_data.x.shape[1]
hidden_dim = 64
num_heads = 8
num_layers = 3

model = GCN_GAT_Model(node_feature_dim, hidden_dim, num_heads, num_layers)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = torch.nn.MSELoss()

# Store loss values for plotting later
all_train_loss_values = []
all_validation_loss_values = []

# Grid search loop
for params in param_combinations:
    hidden_dim, num_heads, num_layers, lr, dropout_rate = params

    model = GCN_GAT_Model(node_feature_dim, hidden_dim, num_heads, num_layers)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.MSELoss()

    # Modify the model to include the selected dropout rate
    for layer in model.gcn_layers:
        layer.dropout = dropout_rate
    for layer in model.gat_layers:
        layer.dropout = dropout_rate

    train_loss_values = []
    validation_loss_values = []
    num_epochs = 50
    for epoch in range(num_epochs):
        model.train()  # Set model to training mode
        optimizer.zero_grad()
        out = model(train_data)
        loss = criterion(out[:-1], train_data.x[1:])
        loss.backward()
        optimizer.step()
        train_loss_values.append(loss.item())

        model.eval()  # Set model to evaluation mode
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

# Plotting the loss functions
plt.figure(figsize=(12, 6))

# Plot training and validation loss for the best configuration
best_index = param_combinations.index(best_params)
plt.plot(range(num_epochs), all_train_loss_values[best_index], label='Training Loss', color='blue')
plt.plot(range(num_epochs), all_validation_loss_values[best_index], label='Validation Loss', color='red')

plt.title('Training and Validation Loss Over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.show()

print(f"Best Hyperparameters: Hidden Dim: {best_params[0]}, Num Heads: {best_params[1]}, Num Layers: {best_params[2]}, Learning Rate: {best_params[3]}, Dropout Rate: {best_params[4]}")

def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero_mask = y_true != 0
    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100
validation_targets = validation_data.x
def calculate_all_metrics(actuals, predictions, h):
    """
    Calculate MSE, RMSE, MAPE, R2, and MAFE for each index for a given horizon h.

    Parameters:
    - actuals: Tensor, actual values with shape [T, num_indices].
    - predictions: Tensor, predicted values with shape [T-h, num_indices].
    - h: int, forecasting horizon.

    Returns:
    - DataFrame containing all metrics for each index.
    """
    T = actuals.shape[0]
    if predictions.shape[0] > T - h:
        predictions = predictions[:T - h]
    actuals = actuals[h:]

    metrics_list = []

    for idx in range(actuals.shape[1]):
        act = actuals[:, idx].detach().cpu().numpy()
        pred = predictions[:, idx].detach().cpu().numpy()

        mse = mean_squared_error(act, pred)
        rmse = np.sqrt(mse)
        mape = mean_absolute_percentage_error(act, pred)

        mafe = np.mean(np.abs(pred - act))

        # Collect the results for this index
        metrics_list.append({
            'Index': f"Index {idx+1}",
            'MAFE': mafe,
            'MSE': mse,
            'RMSE': rmse,
            'MAPE': mape,

        })

    # Convert the list of dictionaries to a DataFrame
    metrics_df = pd.DataFrame(metrics_list)
    return metrics_df

# Assume validation_data, model, and validation_targets are properly defined

model.eval()
with torch.no_grad():
    validation_out = model(validation_data)

# Define horizons for which you want to calculate the metrics
horizons = [1, 5, 10, 22]
metrics_results_per_horizon = {}

for h in horizons:
    metrics_df = calculate_all_metrics(validation_targets, validation_out, h)
    metrics_results_per_horizon[f"Metrics for horizon {h}"] = metrics_df

# Print results for each horizon
for horizon, metrics_df in metrics_results_per_horizon.items():
    print(f"{horizon}:")
    print(metrics_df.to_string(index=False))



