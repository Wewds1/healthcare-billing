import joblib 
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import json


class DenialPredictor:
    def __init__(self, model_dir : str = "ml/models/saved"):\
        # Claim Denial Prediciton Model -- Load trained models and provide methods for single, batch predictions and some important features
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metadata = None
        self._load_model()
        
        if self.metadata.get("model_type") == "Logistic Regression" and not hasattr(self.model, "multi_class"):
            self.model.multi_class = "auto"
    
    #Load model, scaler, feature names, and metadata
    def _load_model(self):
        try:
            #load Model
            model_path = self.model_dir / "denial_model.pkl"
            self.model = joblib.load(model_path)
            
            #load Scaler
            scaler_path = self.model_dir / "denial_model_scaler.pkl"
            self.scaler = joblib.load(scaler_path)
            
            #load feature names also
            features_path = self.model_dir / "denial_model_features.pkl"
            self.feature_names = joblib.load(features_path)
            
            #load metadata
            metadata_path = self.model_dir / "denial_model_metadata.json"
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
                
        except Exception as e:
            print(f"Error loading model or related files: {e}")
            raise e
        
        
    def prepare_features(self, input_data: Dict) -> pd.DataFrame:
        
        """Prepare input Data for Prediction 
        This method takes a dictionary of input data, converts it into a DataFrame,
        and ensures that the features are in the correct order and format for the model. 
        It also applies any necessary scaling using the loaded scaler.
        
        Returns:
            DataFrame with all required features (one-hot encoded)
        """
        
        
        df = pd.DataFrame([input_data])
        categorical_features = ['insurance_type', 'procedure_cpt_code', 'diagnosis_code']
        
        # One-hot encode categorical features (same as training)
        df_encoded = pd.get_dummies(df, columns=categorical_features, drop_first=True)
        
        for feature in self.feature_names:
            if feature not in df_encoded.columns:
                df_encoded[feature] = 0
        df_encoded = df_encoded[self.feature_names]
        
        return df_encoded
    
    def predict(self, input_data: Dict) -> Dict:
        """ Predict claim denial probability for a single input data point
            returns a dictionary with the predicted probability and the denial prediction (0 or 1)
            
        """
        
        X = self.prepare_features(input_data)
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0][1]
        
        
        if probability >=  0.7:
            risk_level = "HIGH"
        elif probability >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        top_risk_factors = self._get_top_risk_factors(X, n=3)
        return {
            "denial_probability": round(float(probability), 4),
            "risk_level": risk_level,
            "prediction": int(prediction), #this is just 0 and 1. 0 = Paid, 1 = Denied
            "prediction_label": "DENIED" if prediction == 1 else "PAID",
            "top_risk_factors": top_risk_factors
            
            }
        
        
    def predict_batch(self, input_data_list: List[Dict]) -> List[Dict]:
        predictions = []
        for input_data in input_data_list:
            try:
                pred = self.predict(input_data) # just use the single predict method for each in the batch
                predictions.append(pred)
            except Exception as e: # if there is an error with a specific input, we can log it and continue with the rest of the batch
                predictions.append({
                    'error': str(e),
                    'denial_probability': None,
                    'risk_level': 'ERROR'
                })
        return predictions

    def _get_top_risk_factors(self, X: pd.DataFrame, n: int = 3) -> List[Dict]:
        """ get the top N risk factors the default is 3 
        
        Returns a list of dictionnaries of feature, value amd importance score
        """
        # check if feature imporatnces are available
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importances = np.abs(self.model.coef_[0])
        else:
            return []
        
        feature_data = []
        
        for i, (feature, importance) in enumerate(zip(self.feature_names, importances)):  # combine then listes into one loop
            value = X.iloc[0, i]  # get the value of the feature for the input data
            feature_data.append({
                'feature': feature,
                'value': float(value),
                'importance': float(importance)
            })
        feature_data.sort(key = lambda x: x['importance'], reverse=True)
        
        
        return feature_data[:n]
            
    
    def get_model_info(self) -> Dict:
        return {
            'model_type': self.metadata.get('model_type', 'Unknown'),
            'training_date': self.metadata.get('training_date', 'Unknown'),
            'training_data_size': self.metadata.get('dataset_size', 0),
            'num_features': self.metadata.get('numeric_features', 0),
            'metrics': self.metadata.get('metrics', {}),
            'top_features': self.metadata.get('top_features', [])
        }
    
    
    def get_feature_importance(self) -> List[Dict]:
        """ Get feature Importance Rankings
        
        returns a list of dictionaries with feature name and importance score
        """
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importances = np.abs(self.model.coef_[0])
        else:
            return []
        
        feature_importance = [
            {'feature': feature, 'importance': float(imp)}
            for feature, imp in zip(self.feature_names, importances)
        ]
        
        # Sort by importance
        feature_importance.sort(key=lambda x: x['importance'], reverse=True)
        
        return feature_importance
    
    
_predictor_instance: Optional[DenialPredictor] = None

def get_predictor() -> DenialPredictor:
    # create a singleton instance of the predictor to be used across the app
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = DenialPredictor()
    return _predictor_instance

if __name__ == "__main__":
    predictor = get_predictor()
    print(predictor.get_model_info())
    
    sample_input = {
        'patient_age': 65,
        'insurance_type': 'Medicare',
        'procedure_cpt_code': '99214',
        'diagnosis_code': 'E11.9',
        'billed_amount': 250.00,
        'days_since_last_claim': 45,
        'num_prior_claims': 3,
        'prior_denial_rate': 0.33
    }
    
    result = predictor.predict(sample_input)

    print(f"   Denial Probability: {result['denial_probability']:.1%}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Prediction: {result['prediction_label']}")
    print(f"Top Risk Factors:")
    for i, factor in enumerate(result['top_risk_factors'], 1):
        print(f"{i}. {factor['feature']}: {factor['importance']:.4f}")
    
    print("\Predictor is working correctly!")