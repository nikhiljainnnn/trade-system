import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif
import xgboost as xgb
import lightgbm as lgb
import joblib
import os
import yaml
import warnings
warnings.filterwarnings('ignore')

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def prepare_features(df):
    """Prepare and engineer features for model training"""
    print("Preparing features for training...")
    
    # Define feature columns (all numerical indicators)
    feature_columns = [
        # Basic OHLCV features
        'Close', 'Volume',
        
        # Momentum indicators
        'RSI_14', 'RSI_21', 'RSI_7', 'RSI_Momentum',
        'Stoch_K', 'Stoch_D', 'Williams_R',
        
        # Trend indicators
        'MACD', 'MACD_Signal', 'MACD_Histogram', 'MACD_Std', 'MACD_Signal_Std',
        'EMA_9', 'EMA_21', 'EMA_50', 'EMA_200',
        'EMA_Cross_Short', 'EMA_Cross_Long',
        
        # Volatility indicators
        'BB_Width', 'BB_Position', 'ATR', 'ATR_Percent',
        'Volatility_Breakout', 'Volatility_Regime',
        
        # Volume indicators
        'VWAP_Distance', 'Volume_ROC',
        
        # Pattern recognition
        'Higher_High', 'Lower_Low', 'Support_Distance', 'Resistance_Distance',
        
        # Market regime
        'ADX', 'Trending_Market', 'Choppiness',
        
        # Momentum confluence
        'Momentum_Confluence',
        
        # Lag features
        'Close_Lag_1', 'Close_Lag_2', 'Close_Lag_3', 'Close_Lag_5',
        'RSI_Lag_1', 'RSI_Lag_2', 'RSI_Lag_3', 'RSI_Lag_5',
        'MACD_Lag_1', 'MACD_Lag_2', 'MACD_Lag_3', 'MACD_Lag_5',
        
        # Rolling statistics
        'Close_SMA_5', 'Close_SMA_20', 'Close_Std_20',
        'Close_Skew_20', 'Close_Kurt_20',
        
        # Returns and volatility
        'Return_3d', 'Return_5d', 'Return_10d', 'Return_20d',
        'Volatility_3d', 'Volatility_5d', 'Volatility_10d', 'Volatility_20d',
        
        # Option-specific features
        'Call_LTP', 'Call_IV', 'Call_OI', 'Call_Volume'
    ]
    
    # Check for crypto-specific features
    config = load_config()
    is_crypto = 'BTC' in config.get('index_symbol', '').upper()
    
    if is_crypto:
        crypto_features = ['Crypto_Fear_Greed', 'Is_Weekend', 'Hour', 'Is_US_Hours', 'Is_Asian_Hours']
        for feature in crypto_features:
            if feature in df.columns:
                feature_columns.append(feature)
    
    # Add option-specific features if available
    option_features = ['PCR_Volume', 'PCR_OI', 'Avg_IV', 'IV_Skew']
    for feature in option_features:
        if feature in df.columns:
            feature_columns.append(feature)
    
    # Select only existing columns
    available_features = [col for col in feature_columns if col in df.columns]
    print(f"Available features: {len(available_features)}/{len(feature_columns)}")
    
    if len(available_features) < 10:
        print("Warning: Very few features available. Model accuracy may be limited.")
    
    # Create feature matrix
    X = df[available_features].copy()
    
    # Handle missing values
    X = X.fillna(method='ffill').fillna(method='bfill')
    
    # Remove infinite values
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(0)
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Features: {available_features}")
    
    return X, available_features

def create_ensemble_model():
    """Create an ensemble model with multiple algorithms for high accuracy"""
    
    # Individual models with optimized parameters
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    gb = GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.1,
        max_depth=8,
        random_state=42
    )
    
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    lgb_model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=8,
        num_leaves=31,
        random_state=42,
        verbose=-1
    )
    
    # Create ensemble with voting
    ensemble = VotingClassifier(
        estimators=[
            ('rf', rf),
            ('gb', gb),
            ('xgb', xgb_model),
            ('lgb', lgb_model)
        ],
        voting='soft'  # Use predicted probabilities
    )
    
    return ensemble

def train_and_save_model():
    """Train an enhanced ensemble model for 90%+ accuracy"""
    # Check if labeled data exists
    if not os.path.exists("data/labeled_data.csv"):
        print("   ❌ labeled_data.csv not found. Run label_data.py first.")
        return False
    
    print("Loading and preparing data...")
    # Load prepared data
    df = pd.read_csv("data/labeled_data.csv")
    print(f"Loaded {len(df)} samples")
    
    # Check signal distribution
    if 'Signal' not in df.columns:
        print("   ❌ Signal column not found in labeled data")
        return False
    
    signal_counts = df['Signal'].value_counts()
    print(f"Signal distribution: {dict(signal_counts)}")
    
    # Prepare features
    X, feature_names = prepare_features(df)
    y = df['Signal']
    
    # Check class distribution
    if len(y.unique()) < 2:
        print("   ❌ Need at least 2 different signal classes for training")
        return False
    
    # Feature selection (select top K features)
    config = load_config()
    if config.get('feature_engineering_enabled', True):
        print("Performing feature selection...")
        
        # Select top 30 features (or all if less than 30)
        k_features = min(30, X.shape[1])
        selector = SelectKBest(score_func=f_classif, k=k_features)
        X_selected = selector.fit_transform(X, y)
        
        # Get selected feature names
        selected_features = [feature_names[i] for i in selector.get_support(indices=True)]
        print(f"Selected {len(selected_features)} best features")
        
        # Save feature selector
        joblib.dump(selector, "models/feature_selector.pkl")
        
        X = pd.DataFrame(X_selected, columns=selected_features)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X = pd.DataFrame(X_scaled, columns=X.columns)
    
    # Save scaler
    joblib.dump(scaler, "models/feature_scaler.pkl")
    
    # Time series split for crypto data (respects temporal order)
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Create ensemble model
    if config.get('ensemble_models', True):
        print("Creating ensemble model...")
        model = create_ensemble_model()
    else:
        print("Creating single Random Forest model...")
        model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    
    # Perform cross-validation
    print("Performing cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=tscv, scoring='accuracy')
    print(f"Cross-validation scores: {cv_scores}")
    print(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Check if accuracy meets threshold
    min_accuracy = config.get('min_accuracy_threshold', 0.85)
    if cv_scores.mean() < min_accuracy:
        print(f"   ⚠️  CV accuracy {cv_scores.mean():.4f} below threshold {min_accuracy}")
        print("   Consider collecting more data or adjusting features")
    
    # Split data for final training and testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Train the model
    print("Training final model...")
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"\n📊 MODEL PERFORMANCE:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    
    # Detailed classification report
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance (if available)
    if hasattr(model, 'feature_importances_'):
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🔝 Top 10 Most Important Features:")
        print(feature_importance.head(10))
        
        # Save feature importance
        feature_importance.to_csv("models/feature_importance.csv", index=False)
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Save the model and metadata
    joblib.dump(model, "models/trade_model.pkl")
    
    # Save model metadata
    metadata = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'features': list(X.columns),
        'model_type': 'ensemble' if config.get('ensemble_models', True) else 'random_forest',
        'training_samples': len(X_train),
        'test_samples': len(X_test)
    }
    
    import json
    with open("models/model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Check if model meets accuracy requirements
    target_accuracy = 0.90  # 90% target
    if accuracy >= target_accuracy:
        print(f"\n✅ SUCCESS! Model achieved {accuracy:.2%} accuracy (target: {target_accuracy:.0%})")
    else:
        print(f"\n⚠️  Model accuracy {accuracy:.2%} below 90% target")
        print("Consider:")
        print("- Collecting more training data")
        print("- Adjusting signal labeling criteria")
        print("- Fine-tuning hyperparameters")
    
    return True

def hyperparameter_tuning(X, y):
    """Perform hyperparameter tuning for the model"""
    print("Performing hyperparameter tuning...")
    
    # Define parameter grids for different models
    rf_params = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 15, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    
    # Use TimeSeriesSplit for crypto data
    tscv = TimeSeriesSplit(n_splits=3)
    
    # Grid search for Random Forest
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    grid_search = GridSearchCV(
        rf, rf_params, cv=tscv, scoring='accuracy', n_jobs=-1, verbose=1
    )
    
    grid_search.fit(X, y)
    
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
    
    return grid_search.best_estimator_

if __name__ == "__main__":
    train_and_save_model()
